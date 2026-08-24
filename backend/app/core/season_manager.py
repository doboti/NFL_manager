from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.game_data import (
    CONFERENCE_CHAMPION_BONUS,
    MATCH_HOUR,
    NFL_DIVISIONS,
    NFL_TEAM_CONFERENCE_BY_CODE,
    PLAYOFF_APPEARANCE_BONUS,
    REGULAR_SEASON_DAYS,
    SUPER_BOWL_WINNER_BONUS,
)
from app.core.schedule import LEAGUE_TZ
from app.models.enums import SeasonPhase
from app.models.league import League
from app.models.match import Match
from app.models.player import Player
from app.models.season_history import SeasonHistory
from app.models.team import Team

_PLAYOFF_ROUND_ORDER = ["conference_semifinal", "conference_final", "super_bowl"]


def _win_pct(team: Team) -> float:
    games = team.wins + team.losses + team.ties
    if games == 0:
        return 0.0
    return (team.wins + team.ties * 0.5) / games


def _next_match_slot(now: datetime) -> datetime:
    target_date = now.astimezone(LEAGUE_TZ).date() + timedelta(days=1)
    return datetime.combine(target_date, time(hour=MATCH_HOUR), tzinfo=LEAGUE_TZ)


def advance_regular_season_day(db: Session, league: League, now: datetime) -> None:
    """Call once per daily cycle while in the regular season. Once
    REGULAR_SEASON_DAYS is reached, kicks off the playoffs instead."""
    if league.phase != SeasonPhase.REGULAR:
        return

    league.season_day += 1
    if league.season_day >= REGULAR_SEASON_DAYS:
        start_playoffs(db, league, now)


def start_playoffs(db: Session, league: League, now: datetime) -> None:
    teams_by_code = {t.nfl_team_code: t for t in db.query(Team).filter(Team.nfl_team_code.isnot(None))}

    division_winners = []
    for codes in NFL_DIVISIONS.values():
        division_teams = [teams_by_code[c] for c in codes if c in teams_by_code]
        if not division_teams:
            continue
        division_teams.sort(key=lambda t: (-_win_pct(t), -t.wins))
        division_winners.append(division_teams[0])

    afc = sorted(
        (t for t in division_winners if NFL_TEAM_CONFERENCE_BY_CODE.get(t.nfl_team_code) == "AFC"),
        key=lambda t: -_win_pct(t),
    )
    nfc = sorted(
        (t for t in division_winners if NFL_TEAM_CONFERENCE_BY_CODE.get(t.nfl_team_code) == "NFC"),
        key=lambda t: -_win_pct(t),
    )

    for team in afc + nfc:
        team.franchise_capital += PLAYOFF_APPEARANCE_BONUS

    league.phase = SeasonPhase.PLAYOFFS
    league.current_playoff_round = "conference_semifinal"

    scheduled_at = _next_match_slot(now)
    matchups = []
    if len(afc) >= 4:
        matchups.append((afc[0], afc[3]))
        matchups.append((afc[1], afc[2]))
    if len(nfc) >= 4:
        matchups.append((nfc[0], nfc[3]))
        matchups.append((nfc[1], nfc[2]))

    for home, away in matchups:
        db.add(
            Match(
                league_id=league.id,
                season=league.season,
                home_team_id=home.id,
                away_team_id=away.id,
                played=False,
                scheduled_at=scheduled_at,
                is_playoff=True,
                playoff_round="conference_semifinal",
            )
        )
    db.flush()


def advance_playoffs(db: Session, league: League, now: datetime) -> dict | None:
    """Call once per daily cycle while in the playoffs. Schedules the next
    round once the current one is fully played, or ends the season after
    the Super Bowl."""
    if league.phase != SeasonPhase.PLAYOFFS or league.current_playoff_round is None:
        return None

    round_matches = (
        db.query(Match)
        .filter(
            Match.league_id == league.id,
            Match.is_playoff.is_(True),
            Match.playoff_round == league.current_playoff_round,
        )
        .all()
    )
    if not round_matches or any(not m.played for m in round_matches):
        return None

    winner_ids = [m.home_team_id if (m.home_score or 0) > (m.away_score or 0) else m.away_team_id for m in round_matches]
    winners = {t.id: t for t in db.query(Team).filter(Team.id.in_(winner_ids)).all()}
    scheduled_at = _next_match_slot(now)

    if league.current_playoff_round == "conference_semifinal":
        afc_winners = [winners[w] for w in winner_ids if NFL_TEAM_CONFERENCE_BY_CODE.get(winners[w].nfl_team_code) == "AFC"]
        nfc_winners = [winners[w] for w in winner_ids if NFL_TEAM_CONFERENCE_BY_CODE.get(winners[w].nfl_team_code) == "NFC"]

        for group in (afc_winners, nfc_winners):
            if len(group) == 2:
                db.add(
                    Match(
                        league_id=league.id,
                        season=league.season,
                        home_team_id=group[0].id,
                        away_team_id=group[1].id,
                        played=False,
                        scheduled_at=scheduled_at,
                        is_playoff=True,
                        playoff_round="conference_final",
                    )
                )
        league.current_playoff_round = "conference_final"
        db.flush()
        return {"event": "conference_final_scheduled"}

    if league.current_playoff_round == "conference_final":
        for team in winners.values():
            team.franchise_capital += CONFERENCE_CHAMPION_BONUS

        finalists = list(winners.values())
        if len(finalists) == 2:
            db.add(
                Match(
                    league_id=league.id,
                    season=league.season,
                    home_team_id=finalists[0].id,
                    away_team_id=finalists[1].id,
                    played=False,
                    scheduled_at=scheduled_at,
                    is_playoff=True,
                    playoff_round="super_bowl",
                )
            )
        league.current_playoff_round = "super_bowl"
        db.flush()
        return {"event": "super_bowl_scheduled"}

    if league.current_playoff_round == "super_bowl":
        champion = winners[winner_ids[0]]
        champion.franchise_capital += SUPER_BOWL_WINNER_BONUS
        season_result = end_season(db, league, now, champion.id)
        return {"event": "season_ended", "champion": champion.name, **season_result}

    return None


def reset_player_ratings(db: Session) -> dict:
    """Every player stays in the league permanently (no retirement) -- each
    new season just wipes out the previous season's training gains, so
    everyone starts back at their original imported rating."""
    all_players = db.query(Player).all()
    for player in all_players:
        player.age += 1
        player.overall = player.base_overall
        player.xp = 0

    db.flush()
    return {"aged": len(all_players), "ratings_reset": len(all_players)}


def _record_season_history(db: Session, league: League, champion_id: int) -> None:
    playoff_matches = (
        db.query(Match)
        .filter(Match.league_id == league.id, Match.season == league.season, Match.is_playoff.is_(True))
        .all()
    )
    rounds_reached: dict[int, list[str]] = {}
    for match in playoff_matches:
        rounds_reached.setdefault(match.home_team_id, []).append(match.playoff_round)
        rounds_reached.setdefault(match.away_team_id, []).append(match.playoff_round)

    for team in db.query(Team).all():
        if team.id == champion_id:
            playoff_result = "champion"
        else:
            team_rounds = rounds_reached.get(team.id)
            if not team_rounds:
                playoff_result = "missed_playoffs"
            else:
                furthest = max(team_rounds, key=_PLAYOFF_ROUND_ORDER.index)
                playoff_result = "runner_up" if furthest == "super_bowl" else furthest

        db.add(
            SeasonHistory(
                league_id=league.id,
                team_id=team.id,
                season=league.season,
                wins=team.wins,
                losses=team.losses,
                ties=team.ties,
                playoff_result=playoff_result,
            )
        )
    db.flush()


def end_season(db: Session, league: League, now: datetime, champion_id: int) -> dict:
    _record_season_history(db, league, champion_id)

    aging_result = reset_player_ratings(db)

    for team in db.query(Team).all():
        team.wins = 0
        team.losses = 0
        team.ties = 0

    league.season += 1
    league.phase = SeasonPhase.REGULAR
    league.season_day = 0
    league.current_playoff_round = None
    league.season_started_at = now

    db.flush()
    return {"new_season": league.season, **aging_result}
