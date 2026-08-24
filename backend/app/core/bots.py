import uuid

from sqlalchemy.orm import Session, joinedload

from app.core.clock import now_utc
from app.core.game_data import (
    BOT_PROGRESSION_INTERVAL_DAYS,
    BOT_PROGRESSION_OVR_GAIN,
    NFL_TEAMS,
    player_market_value,
)
from app.core.security import hash_password
from app.core.team_setup import assign_real_roster
from app.core.trades import _cancel_conflicting_offers
from app.models.enums import TradeStatus
from app.models.league import League
from app.models.player import Player
from app.models.team import Team
from app.models.trade_offer import TradeOffer
from app.models.user import User

BOT_ACCEPT_THRESHOLD = 0.9  # bots accept offers worth at least 90% of the target player's value


def seed_bot_teams(db: Session) -> int:
    """Fills every NFL team without a franchise yet with a lightweight AI-controlled
    one, so there is always a full league to play matches and trade against."""
    existing_codes = {code for (code,) in db.query(Team.nfl_team_code).filter(Team.nfl_team_code.isnot(None))}
    created = 0

    for entry in NFL_TEAMS:
        code = entry["code"]
        if code in existing_codes:
            continue

        bot_user = User(
            email=f"bot-{code.lower()}@bots.local",
            hashed_password=hash_password(uuid.uuid4().hex),
            display_name=f"{entry['name']} (AI)",
            is_bot=True,
        )
        db.add(bot_user)
        db.flush()

        team = Team(owner_id=bot_user.id, name=entry["name"], nfl_team_code=code, is_bot=True)
        db.add(team)
        db.flush()

        assign_real_roster(db, team, code)
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
        .filter(Team.is_bot.is_(True), Player.overall < 99)
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


def resolve_bot_trade_offers(db: Session) -> dict:
    pending = (
        db.query(TradeOffer)
        .options(joinedload(TradeOffer.to_team), joinedload(TradeOffer.target_player), joinedload(TradeOffer.offered_player))
        .join(Team, TradeOffer.to_team_id == Team.id)
        .filter(TradeOffer.status == TradeStatus.PENDING, Team.is_bot.is_(True))
        .all()
    )

    accepted = 0
    rejected = 0
    now = now_utc(db)

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
