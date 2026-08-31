import enum


class Position(str, enum.Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"


class Tactic(str, enum.Enum):
    BALANCED = "BALANCED"
    PASS_HEAVY = "PASS_HEAVY"
    RUN_HEAVY = "RUN_HEAVY"
    BLITZ = "BLITZ"
    PREVENT = "PREVENT"


class SponsorType(str, enum.Enum):
    FIXED = "FIXED"
    PERFORMANCE = "PERFORMANCE"


class TradeStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class SeasonPhase(str, enum.Enum):
    REGULAR = "REGULAR"
    PLAYOFFS = "PLAYOFFS"
