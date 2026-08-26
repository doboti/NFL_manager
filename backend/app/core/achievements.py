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
    # Human-readable "how much is left" hint for a locked achievement --
    # None for achievements where a partial-progress number wouldn't mean
    # much (e.g. "first season", a pure one-off milestone).
    progress: Callable[[_Stats], str | None] | None = None


def _wins_left(threshold: int) -> Callable[[_Stats], str | None]:
    def _progress(s: _Stats) -> str | None:
        remaining = threshold - s.total_wins
        return f"Még {remaining} győzelem kell." if remaining > 0 else None

    return _progress


def _seasons_left(threshold: int) -> Callable[[_Stats], str | None]:
    def _progress(s: _Stats) -> str | None:
        remaining = threshold - s.seasons
        return f"Még {remaining} szezon kell." if remaining > 0 else None

    return _progress


def _dynasty_progress(s: _Stats) -> str | None:
    if s.championships == 0:
        return "Még nincs bajnoki címed."
    remaining = 2 - s.championships
    return f"Még {remaining} bajnoki cím kell." if remaining > 0 else None


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
        "dynasty", "Dinasztia", "Legalább két bajnoki címet szereztél.", lambda s: s.championships >= 2,
        progress=_dynasty_progress,
    ),
    Achievement(
        "undefeated_season", "Veretlen szezon", "Volt olyan szezonod, amit vereség nélkül zártál.",
        lambda s: s.had_undefeated_season,
    ),
    Achievement(
        "wins_10", "10 győzelem", "Összesen 10 győzelmet szereztél a pályafutásod során.",
        lambda s: s.total_wins >= 10, progress=_wins_left(10),
    ),
    Achievement(
        "wins_50", "50 győzelem", "Összesen 50 győzelmet szereztél a pályafutásod során.",
        lambda s: s.total_wins >= 50, progress=_wins_left(50),
    ),
    Achievement(
        "wins_100", "100 győzelem", "Összesen 100 győzelmet szereztél a pályafutásod során.",
        lambda s: s.total_wins >= 100, progress=_wins_left(100),
    ),
    Achievement(
        "veteran_5", "Veterán menedzser", "Legalább 5 szezont irányítottál végig.",
        lambda s: s.seasons >= 5, progress=_seasons_left(5),
    ),
    Achievement(
        "veteran_10", "Legendás menedzser", "Legalább 10 szezont irányítottál végig.",
        lambda s: s.seasons >= 10, progress=_seasons_left(10),
    ),
]


def compute_achievements(history: list[SeasonHistory]) -> list[dict]:
    stats = _compute_stats(history)
    results = []
    for a in ACHIEVEMENTS:
        earned = a.check(stats)
        results.append(
            {
                "code": a.code,
                "name": a.name,
                "description": a.description,
                "earned": earned,
                "progress_text": None if earned or a.progress is None else a.progress(stats),
            }
        )
    return results
