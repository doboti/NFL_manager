import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.game_data import player_market_value
from app.core.security import hash_password
from app.models.enums import Position
from app.models.league import League
from app.models.player import Player
from app.models.team import Team
from app.models.user import User


class TeamClaimError(Exception):
    pass


def avg_overall_by_team(db: Session) -> dict[int, float]:
    """One aggregate query -- avoids loading every team's full roster just to
    show a lightweight average rating in list/standings views."""
    rows = (
        db.query(Player.team_id, func.avg(Player.overall))
        .filter(Player.team_id.isnot(None))
        .group_by(Player.team_id)
        .all()
    )
    return {team_id: round(float(avg), 1) for team_id, avg in rows}


def get_team_by_code(db: Session, league_id: int, code: str) -> Team | None:
    return db.query(Team).filter(Team.league_id == league_id, Team.nfl_team_code == code).first()


def is_team_code_taken_by_human(db: Session, league_id: int, code: str) -> bool:
    team = get_team_by_code(db, league_id, code)
    return team is not None and not team.is_bot


PLAYERS_PER_POSITION = 3


def _cap_roster_to_top_by_position(db: Session, team: Team) -> None:
    """Keeps only the 3 best-overall players per position on the team,
    releasing the rest back to the free-agent pool. Used both for a fresh
    team and for a human taking over an already-populated bot team -- in
    either case that's the moment the roster should shrink to what's
    actually needed, not the full NFL depth chart."""
    by_position: dict[Position, list[Player]] = {}
    for player in team.players:
        by_position.setdefault(player.position, []).append(player)

    for position_players in by_position.values():
        position_players.sort(key=lambda p: p.overall, reverse=True)
        for player in position_players[PLAYERS_PER_POSITION:]:
            player.team_id = None
            player.listed_for_transfer = False
            player.asking_price = None


def assign_real_roster(db: Session, team: Team, code: str, league_id: int) -> int:
    """Hands the team every currently-unclaimed real player on that team's
    real-world roster, then immediately caps it down to the 3 best per
    position (see _cap_roster_to_top_by_position) -- the rest stay in the
    free-agent pool, signable later via the transfer market."""
    players = (
        db.query(Player)
        .filter(Player.nfl_team == code, Player.league_id == league_id, Player.team_id.is_(None))
        .all()
    )
    for player in players:
        player.team_id = team.id

    db.flush()
    _cap_roster_to_top_by_position(db, team)
    return len(team.players)


def reset_all_rosters_to_real(db: Session, league: League) -> int:
    """Called once per season transition, the same moment
    season_manager.reset_team_economy() and reset_player_ratings() run --
    without this, roster composition was the one thing that never reset:
    economy/record wiped clean every season while bot-to-bot trades kept
    accumulating indefinitely, so a freshly-claimed team looked half brand
    new (0-0-0, starting capital) and half several-seasons-stale (a roster
    shaped by trade history, not the team's real depth chart). Frees every
    owned player in the league back to the pool, then re-assigns each team
    from scratch via assign_real_roster -- same as a first-time claim."""
    owned_players = db.query(Player).filter(Player.league_id == league.id, Player.team_id.isnot(None)).all()
    for player in owned_players:
        player.team_id = None
        player.listed_for_transfer = False
        player.asking_price = None
        player.market_price = max(1, round(player_market_value(1000, player.overall, player.age)))
    db.flush()

    teams = db.query(Team).filter(Team.league_id == league.id).all()
    reassigned = 0
    for team in teams:
        if team.nfl_team_code:
            assign_real_roster(db, team, team.nfl_team_code, league.id)
            reassigned += 1
    return reassigned


def claim_team(db: Session, user: User, league: League, code: str, team_name: str) -> Team:
    """Creates a fresh franchise for `code`, or -- if an AI bot currently runs that
    team -- hands the human the reins of that same (already-populated) franchise."""
    if db.query(Team).filter(Team.owner_id == user.id).first() is not None:
        raise TeamClaimError("You already have a team")

    existing = get_team_by_code(db, league.id, code)

    if existing is not None and not existing.is_bot:
        raise TeamClaimError("This team has already been claimed")

    if existing is not None and existing.is_bot:
        old_owner_id = existing.owner_id
        existing.owner_id = user.id
        existing.is_bot = False
        db.flush()
        db.query(User).filter(User.id == old_owner_id, User.is_bot.is_(True)).delete()
        _cap_roster_to_top_by_position(db, existing)
        return existing

    team = Team(owner_id=user.id, league_id=league.id, name=team_name, nfl_team_code=code)
    db.add(team)
    db.flush()
    assign_real_roster(db, team, code, league.id)
    return team


def _release_team_to_bot(db: Session, team: Team) -> None:
    bot_user = User(
        email=f"bot-{team.nfl_team_code.lower()}@bots.local",
        hashed_password=hash_password(uuid.uuid4().hex),
        display_name=f"{team.name} (AI)",
        is_bot=True,
    )
    db.add(bot_user)
    db.flush()

    team.owner_id = bot_user.id
    team.is_bot = True
    db.flush()


def release_team(db: Session, user: User) -> None:
    """Hands the team back to an AI bot so the player can pick a different
    one -- the mirror image of the takeover branch in claim_team above."""
    team = db.query(Team).filter(Team.owner_id == user.id).first()
    if team is None:
        raise TeamClaimError("You don't have a team")

    _release_team_to_bot(db, team)


def release_all_human_teams(db: Session, league: League) -> int:
    """Called once a league's season is fully over: a manager's tenure with
    a team lasts exactly one season -- once it ends, the team goes back to
    AI control and the manager's slot frees up to claim a team again (same
    league or a different one) for the next season. Achievements/level are
    unaffected since SeasonHistory is owner-scoped, not team-scoped."""
    teams = db.query(Team).filter(Team.league_id == league.id, Team.is_bot.is_(False)).all()
    for team in teams:
        _release_team_to_bot(db, team)
    return len(teams)
