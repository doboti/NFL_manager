import random

from app.core.game_data import player_market_value
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

BASE_MARKET_PRICE = 1000


def random_name() -> tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def generate_player(position: Position, min_age: int = 21, max_age: int = 32,
                     min_ovr: int = 50, max_ovr: int = 75, for_market: bool = False) -> Player:
    first_name, last_name = random_name()
    age = random.randint(min_age, max_age)
    overall = random.randint(min_ovr, max_ovr)

    market_price = None
    if for_market:
        market_price = max(1, round(player_market_value(BASE_MARKET_PRICE, overall, age)))

    return Player(
        first_name=first_name,
        last_name=last_name,
        position=position,
        age=age,
        overall=overall,
        base_overall=overall,
        market_price=market_price,
    )


def generate_starting_roster() -> list[Player]:
    return [
        generate_player(position, min_age=21, max_age=29, min_ovr=55, max_ovr=68)
        for position in STARTING_ROSTER
    ]


def generate_market_player() -> Player:
    position = random.choice(list(Position))
    return generate_player(position, min_age=20, max_age=36, min_ovr=45, max_ovr=90, for_market=True)
