"""Career achievements, computed on the fly from a manager's SeasonHistory
rows (owner_id-scoped, so they follow the person across any team they've
ever released and re-claimed) -- no separate "earned" table to keep in sync,
just a pure function over data that already exists."""

from dataclasses import dataclass
from typing import Callable

from app.models.season_history import SeasonHistory

PLAYOFF_RESULT_ORDER = ["missed_playoffs", "conference_semifinal", "conference_final", "runner_up", "champion"]


@dataclass
class _Stats:
    seasons: int
    total_wins: int
    playoff_appearances: int
    conference_appearances: int
    championships: int
    best_season_wins: int
    had_undefeated_season: bool


def _compute_stats(history: list[SeasonHistory]) -> _Stats:
    return _Stats(
        seasons=len(history),
        total_wins=sum(h.wins for h in history),
        playoff_appearances=sum(1 for h in history if h.playoff_result != "missed_playoffs"),
        conference_appearances=sum(1 for h in history if h.playoff_result in ("runner_up", "champion")),
        championships=sum(1 for h in history if h.playoff_result == "champion"),
        best_season_wins=max((h.wins for h in history), default=0),
        had_undefeated_season=any(h.wins > 0 and h.losses == 0 and h.ties == 0 for h in history),
    )


@dataclass
class Achievement:
    code: str
    name: str
    description: str
    check: Callable[[_Stats], bool]


ACHIEVEMENTS: list[Achievement] = [
    Achievement("first_season", "Első szezon", "Végigvitted az első szezonodat.", lambda s: s.seasons >= 1),
    Achievement(
        "playoff_berth", "Rájátszásba jutott", "Legalább egyszer bejutottál a rájátszásba.",
        lambda s: s.playoff_appearances >= 1,
    ),
    Achievement(
        "conference_champion", "Konferenciabajnok", "Eljutottál legalább egyszer a döntőig.",
        lambda s: s.conference_appearances >= 1,
    ),
    Achievement("champion", "Bajnok", "Megnyertél legalább egy bajnoki címet.", lambda s: s.championships >= 1),
    Achievement(
        "dynasty", "Dinasztia", "Legalább két bajnoki címet szereztél.", lambda s: s.championships >= 2
    ),
    Achievement(
        "undefeated_season", "Veretlen szezon", "Volt olyan szezonod, amit vereség nélkül zártál.",
        lambda s: s.had_undefeated_season,
    ),
    Achievement("wins_10", "10 győzelem", "Összesen 10 győzelmet szereztél a pályafutásod során.", lambda s: s.total_wins >= 10),
    Achievement("wins_50", "50 győzelem", "Összesen 50 győzelmet szereztél a pályafutásod során.", lambda s: s.total_wins >= 50),
    Achievement("wins_100", "100 győzelem", "Összesen 100 győzelmet szereztél a pályafutásod során.", lambda s: s.total_wins >= 100),
    Achievement("veteran_5", "Veterán menedzser", "Legalább 5 szezont irányítottál végig.", lambda s: s.seasons >= 5),
    Achievement("veteran_10", "Legendás menedzser", "Legalább 10 szezont irányítottál végig.", lambda s: s.seasons >= 10),
]


def compute_achievements(history: list[SeasonHistory]) -> list[dict]:
    stats = _compute_stats(history)
    return [
        {"code": a.code, "name": a.name, "description": a.description, "earned": a.check(stats)}
        for a in ACHIEVEMENTS
    ]
