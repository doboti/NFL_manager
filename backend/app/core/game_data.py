"""Static game-balance data driven by terv.md (section 2 & 3)."""

NFL_TEAMS = [
    {"code": "ARI", "name": "Arizona Cardinals"},
    {"code": "ATL", "name": "Atlanta Falcons"},
    {"code": "BAL", "name": "Baltimore Ravens"},
    {"code": "BUF", "name": "Buffalo Bills"},
    {"code": "CAR", "name": "Carolina Panthers"},
    {"code": "CHI", "name": "Chicago Bears"},
    {"code": "CIN", "name": "Cincinnati Bengals"},
    {"code": "CLE", "name": "Cleveland Browns"},
    {"code": "DAL", "name": "Dallas Cowboys"},
    {"code": "DEN", "name": "Denver Broncos"},
    {"code": "DET", "name": "Detroit Lions"},
    {"code": "GB", "name": "Green Bay Packers"},
    {"code": "HOU", "name": "Houston Texans"},
    {"code": "IND", "name": "Indianapolis Colts"},
    {"code": "JAX", "name": "Jacksonville Jaguars"},
    {"code": "KC", "name": "Kansas City Chiefs"},
    {"code": "LAC", "name": "Los Angeles Chargers"},
    {"code": "LAR", "name": "Los Angeles Rams"},
    {"code": "LV", "name": "Las Vegas Raiders"},
    {"code": "MIA", "name": "Miami Dolphins"},
    {"code": "MIN", "name": "Minnesota Vikings"},
    {"code": "NE", "name": "New England Patriots"},
    {"code": "NO", "name": "New Orleans Saints"},
    {"code": "NYG", "name": "New York Giants"},
    {"code": "NYJ", "name": "New York Jets"},
    {"code": "PHI", "name": "Philadelphia Eagles"},
    {"code": "PIT", "name": "Pittsburgh Steelers"},
    {"code": "SEA", "name": "Seattle Seahawks"},
    {"code": "SF", "name": "San Francisco 49ers"},
    {"code": "TB", "name": "Tampa Bay Buccaneers"},
    {"code": "TEN", "name": "Tennessee Titans"},
    {"code": "WSH", "name": "Washington Commanders"},
]
NFL_TEAM_NAMES_BY_CODE = {t["code"]: t["name"] for t in NFL_TEAMS}

NFL_DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WSH"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LAR", "SF", "SEA"],
}
NFL_TEAM_DIVISION_BY_CODE = {code: division for division, codes in NFL_DIVISIONS.items() for code in codes}
NFL_TEAM_CONFERENCE_BY_CODE = {code: division.split(" ")[0] for code, division in NFL_TEAM_DIVISION_BY_CODE.items()}

STADIUM_LEVELS = {
    1: {"capacity": 10_000, "base_revenue": 50_000, "upgrade_cost": 0, "upgrade_hours": 0},
    2: {"capacity": 25_000, "base_revenue": 125_000, "upgrade_cost": 500_000, "upgrade_hours": 12},
    3: {"capacity": 50_000, "base_revenue": 250_000, "upgrade_cost": 2_000_000, "upgrade_hours": 24},
    4: {"capacity": 80_000, "base_revenue": 400_000, "upgrade_cost": 5_000_000, "upgrade_hours": 48},
}
MAX_STADIUM_LEVEL = max(STADIUM_LEVELS)

MAX_ACTIVE_SPONSORS = 3

# "Sablonok" -- several sponsor contract templates, each capped at a handful of days.
SPONSOR_TEMPLATES = [
    {
        "key": "steady",
        "name": "Megbízható Partner",
        "sponsor_type": "FIXED",
        "daily_amount": 25_000,
        "win_bonus": 0,
        "duration_days": 7,
    },
    {
        "key": "performance",
        "name": "Teljesítmény Szponzor",
        "sponsor_type": "PERFORMANCE",
        "daily_amount": 8_000,
        "win_bonus": 50_000,
        "duration_days": 7,
    },
    {
        "key": "high_risk",
        "name": "Kockázatvállaló Befektető",
        "sponsor_type": "PERFORMANCE",
        "daily_amount": 3_000,
        "win_bonus": 90_000,
        "duration_days": 5,
    },
    {
        "key": "short_term",
        "name": "Villám Kampány",
        "sponsor_type": "FIXED",
        "daily_amount": 45_000,
        "win_bonus": 0,
        "duration_days": 3,
    },
    {
        "key": "local_business",
        "name": "Helyi Vállalkozás",
        "sponsor_type": "PERFORMANCE",
        "daily_amount": 15_000,
        "win_bonus": 20_000,
        "duration_days": 7,
    },
]
SPONSOR_TEMPLATES_BY_KEY = {t["key"]: t for t in SPONSOR_TEMPLATES}

BASE_TRAINING_XP = 1000

LEAGUE_TIMEZONE = "Europe/Budapest"
MATCH_HOUR = 21

# --- season / playoffs ---
REGULAR_SEASON_DAYS = 17

PLAYOFF_ROUNDS = ["conference_semifinal", "conference_final", "super_bowl"]
PLAYOFF_ROUND_NAMES = {
    "conference_semifinal": "Konferencia elődöntő",
    "conference_final": "Konferencia döntő",
    "super_bowl": "Super Bowl",
}

PLAYOFF_APPEARANCE_BONUS = 200_000
CONFERENCE_CHAMPION_BONUS = 500_000
SUPER_BOWL_WINNER_BONUS = 2_000_000

# --- bot "rubber-band" progression ---
BOT_PROGRESSION_INTERVAL_DAYS = 7
BOT_PROGRESSION_OVR_GAIN = 1


def age_xp_multiplier(age: int) -> float:
    if 18 <= age <= 21:
        return 1.5
    if 22 <= age <= 25:
        return 1.0
    if 26 <= age <= 29:
        return 0.5
    return 0.1


def xp_to_next_level(ovr: int) -> int:
    return ovr * 100


def player_market_value(base_price: float, ovr: int, age: int) -> float:
    return base_price * (ovr / 50) ** 3 * (35 - age)
