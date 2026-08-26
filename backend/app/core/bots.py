import random
import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.clock import now_utc
from app.core.game_data import (
    BOT_PROGRESSION_INTERVAL_DAYS,
    BOT_PROGRESSION_OVR_GAIN,
    LEAGUES,
    player_market_value,
)
from app.core.security import hash_password
from app.core.team_setup import assign_real_roster
from app.core.trades import TradeError, _cancel_conflicting_offers, create_offer
from app.models.enums import TradeStatus
from app.models.league import League
from app.models.player import Player
from app.models.team import Team
from app.models.trade_offer import TradeOffer
from app.models.user import User

# Small per-team, per-daily-cycle odds -- keeps bot activity visible without
# flooding the market/inbox.
BOT_TRADE_INITIATION_CHANCE = 0.15
BOT_TRANSFER_LISTING_CHANCE = 0.20
BOT_MAX_LISTED_PLAYERS = 1

BOT_ACCEPT_THRESHOLD = 0.9  # bots accept offers worth at least 90% of the target player's value


def seed_bot_teams(db: Session, league: League) -> int:
    """Fills every team in this league without a franchise yet with a
    lightweight AI-controlled one, so there is always a full league to play
    matches and trade against."""
    existing_codes = {code for (code,) in db.query(Team.nfl_team_code).filter(Team.nfl_team_code.isnot(None))}
    created = 0

    for entry in LEAGUES[league.key]["teams"]:
        code = entry["code"]
        if code in existing_codes:
            continue

        # Runs on every backend startup, so it can race a concurrent caller
        # (e.g. a manual reset script) also seeding this same team. A nested
        # transaction lets that single insert fail without aborting the rest
        # of the loop -- the other side's row wins, we just skip ours.
        try:
            with db.begin_nested():
                bot_user = User(
                    email=f"bot-{code.lower()}@bots.local",
                    hashed_password=hash_password(uuid.uuid4().hex),
                    display_name=f"{entry['name']} (AI)",
                    is_bot=True,
                )
                db.add(bot_user)
                db.flush()

                team = Team(
                    owner_id=bot_user.id, league_id=league.id, name=entry["name"], nfl_team_code=code, is_bot=True
                )
                db.add(team)
                db.flush()

                assign_real_roster(db, team, code, league.id)
        except IntegrityError:
            continue

        created += 1

    if created:
        db.commit()

    return created


def apply_bot_progression(db: Session, league: League) -> int:
    """Rubber-band: since bots never train, every so often nudge their whole
    roster's OVR up a notch so the league doesn't stagnate around human teams
    that do train. No per-player AI decisions -- one cheap bulk update."""
    if league.season_day <= 0 or league.season_day % BOT_PROGRESSION_INTERVAL_DAYS != 0:
        return 0

    bot_players = (
        db.query(Player)
        .join(Team, Player.team_id == Team.id)
        .filter(Team.league_id == league.id, Team.is_bot.is_(True), Player.overall < 99)
        .all()
    )
    for player in bot_players:
        player.overall = min(99, player.overall + BOT_PROGRESSION_OVR_GAIN)

    if bot_players:
        db.flush()

    return len(bot_players)


def _player_value(player) -> int:
    if player.market_price:
        return player.market_price
    return max(1, round(player_market_value(1000, player.overall, player.age)))


def resolve_bot_trade_offers(db: Session, now: datetime | None = None) -> dict:
    """Resolves any bot-addressed offer whose respond_at has passed -- not
    every pending one, so a bot's reply lands somewhere in its random 0-4h
    window (see trades.py: BOT_RESPONSE_WINDOW_HOURS) instead of instantly.
    A NULL respond_at (an offer from before this existed) resolves right
    away rather than getting stuck forever."""
    now = now or now_utc(db)
    pending = (
        db.query(TradeOffer)
        .options(joinedload(TradeOffer.to_team), joinedload(TradeOffer.target_player), joinedload(TradeOffer.offered_player))
        .join(Team, TradeOffer.to_team_id == Team.id)
        .filter(
            TradeOffer.status == TradeStatus.PENDING,
            Team.is_bot.is_(True),
            (TradeOffer.respond_at.is_(None)) | (TradeOffer.respond_at <= now),
        )
        .all()
    )

    accepted = 0
    rejected = 0

    for offer in pending:
        target_value = _player_value(offer.target_player)
        offered_value = offer.cash_offer + (_player_value(offer.offered_player) if offer.offered_player else 0)

        from_team = db.query(Team).filter(Team.id == offer.from_team_id).first()
        if from_team is None or offer.cash_offer > from_team.franchise_capital:
            offer.status = TradeStatus.REJECTED
            offer.resolved_at = now
            rejected += 1
            continue

        if offered_value >= target_value * BOT_ACCEPT_THRESHOLD:
            to_team = offer.to_team
            offer.target_player.team_id = from_team.id
            if offer.offered_player is not None:
                offer.offered_player.team_id = to_team.id
            if offer.cash_offer:
                from_team.franchise_capital -= offer.cash_offer
                to_team.franchise_capital += offer.cash_offer
            offer.status = TradeStatus.ACCEPTED
            offer.resolved_at = now
            _cancel_conflicting_offers(db, offer)
            accepted += 1
        else:
            offer.status = TradeStatus.REJECTED
            offer.resolved_at = now
            rejected += 1

    if pending:
        db.commit()

    return {"accepted": accepted, "rejected": rejected}


def bot_initiate_trades(db: Session, league: League, now: datetime) -> int:
    """Each bot team, with a small chance, offers cash for a random player
    on a random other team in the same league -- bot or human, so this
    covers both "trade with each other" and "trade with the human players"
    from issue #14. Reuses create_offer so a bot-to-bot offer also gets a
    respond_at and resolves through the normal timer; an unaffordable or
    otherwise invalid attempt is just skipped, not fatal."""
    teams = db.query(Team).filter(Team.league_id == league.id).all()
    bot_teams = [t for t in teams if t.is_bot]
    initiated = 0

    for bot_team in bot_teams:
        if random.random() >= BOT_TRADE_INITIATION_CHANCE:
            continue

        other_teams = [t for t in teams if t.id != bot_team.id and t.players]
        if not other_teams:
            continue
        target_team = random.choice(other_teams)
        target_player = random.choice(target_team.players)

        cash_offer = round(_player_value(target_player) * random.uniform(1.0, 1.3))
        if cash_offer > bot_team.franchise_capital:
            continue

        try:
            create_offer(db, bot_team, target_team.id, target_player.id, None, cash_offer)
            initiated += 1
        except TradeError:
            continue

    return initiated


def bot_list_for_transfer(db: Session, league: League) -> int:
    """Each bot team, with a small chance, lists one of its own players for
    transfer at a fair price -- fixes issue #16 (the transfer market was
    always empty because only humans ever listed a player)."""
    teams = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.league_id == league.id, Team.is_bot.is_(True))
        .all()
    )
    listed = 0

    for team in teams:
        if random.random() >= BOT_TRANSFER_LISTING_CHANCE:
            continue

        already_listed = sum(1 for p in team.players if p.listed_for_transfer)
        if already_listed >= BOT_MAX_LISTED_PLAYERS:
            continue

        candidates = [p for p in team.players if not p.listed_for_transfer]
        if not candidates:
            continue

        player = random.choice(candidates)
        player.asking_price = max(1, round(_player_value(player) * random.uniform(1.0, 1.2)))
        player.listed_for_transfer = True
        listed += 1

    if listed:
        db.flush()

    return listed
