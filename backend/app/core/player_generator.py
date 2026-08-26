import random

from app.models.enums import Position
from app.models.player import Player

FIRST_NAMES = [
    "James", "Michael", "Chris", "Marcus", "Devon", "Tyler", "Jordan", "Brandon",
    "Justin", "Cameron", "Xavier", "Elijah", "Malik", "Jalen", "Trevor", "Austin",
    "Isaiah", "Derrick", "Anthony", "Dominic",
]
LAST_NAMES = [
    "Johnson", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
    "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Robinson",
    "Clark", "Lewis", "Walker", "Young",
]

STARTING_ROSTER = [
    Position.QB, Position.RB, Position.RB, Position.WR, Position.WR,
    Position.TE, Position.K, Position.DEF,
]


def random_name() -> tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def generate_player(position: Position, min_age: int = 21, max_age: int = 32,
                     min_ovr: int = 50, max_ovr: int = 75) -> Player:
    """Ephemeral opponent generation for practice matches only (never
    persisted -- see matches.py's /practice route). Real free agents come
    exclusively from the ESPN import scripts (#24: a separate synthetic
    market-filler path used to seed nonsense-named players directly into
    the persistent free-agent pool whenever it ran low, and those never
    cleared out once real data arrived)."""
    first_name, last_name = random_name()
    age = random.randint(min_age, max_age)
    overall = random.randint(min_ovr, max_ovr)

    return Player(
        first_name=first_name,
        last_name=last_name,
        position=position,
        age=age,
        overall=overall,
        base_overall=overall,
    )


def generate_starting_roster() -> list[Player]:
    return [
        generate_player(position, min_age=21, max_age=29, min_ovr=55, max_ovr=68)
        for position in STARTING_ROSTER
    ]
