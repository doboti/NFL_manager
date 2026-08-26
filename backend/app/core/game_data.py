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

# --- college football: a hand-picked 32-team subset (real ESPN rosters exist
# for these, unlike CFL/ELF) shaped exactly like the NFL structure above so
# the same season/playoff/division code works for both leagues unmodified.
# Codes are "CF-"-prefixed so they can never collide with an NFL code.
COLLEGE_TEAMS = [
    {"code": "CF-ALA", "name": "Alabama Crimson Tide", "espn_id": "333"},
    {"code": "CF-UGA", "name": "Georgia Bulldogs", "espn_id": "61"},
    {"code": "CF-AUB", "name": "Auburn Tigers", "espn_id": "2"},
    {"code": "CF-TENN", "name": "Tennessee Volunteers", "espn_id": "2633"},
    {"code": "CF-LSU", "name": "LSU Tigers", "espn_id": "99"},
    {"code": "CF-FLA", "name": "Florida Gators", "espn_id": "57"},
    {"code": "CF-TAM", "name": "Texas A&M Aggies", "espn_id": "245"},
    {"code": "CF-MISS", "name": "Ole Miss Rebels", "espn_id": "145"},
    {"code": "CF-TEX", "name": "Texas Longhorns", "espn_id": "251"},
    {"code": "CF-OU", "name": "Oklahoma Sooners", "espn_id": "201"},
    {"code": "CF-OKST", "name": "Oklahoma State Cowboys", "espn_id": "197"},
    {"code": "CF-BAY", "name": "Baylor Bears", "espn_id": "239"},
    {"code": "CF-TCU", "name": "TCU Horned Frogs", "espn_id": "2628"},
    {"code": "CF-KSU", "name": "Kansas State Wildcats", "espn_id": "2306"},
    {"code": "CF-UTAH", "name": "Utah Utes", "espn_id": "254"},
    {"code": "CF-ND", "name": "Notre Dame Fighting Irish", "espn_id": "87"},
    {"code": "CF-OSU", "name": "Ohio State Buckeyes", "espn_id": "194"},
    {"code": "CF-MICH", "name": "Michigan Wolverines", "espn_id": "130"},
    {"code": "CF-MSU", "name": "Michigan State Spartans", "espn_id": "127"},
    {"code": "CF-PSU", "name": "Penn State Nittany Lions", "espn_id": "213"},
    {"code": "CF-WIS", "name": "Wisconsin Badgers", "espn_id": "275"},
    {"code": "CF-IOWA", "name": "Iowa Hawkeyes", "espn_id": "2294"},
    {"code": "CF-NEB", "name": "Nebraska Cornhuskers", "espn_id": "158"},
    {"code": "CF-USC", "name": "USC Trojans", "espn_id": "30"},
    {"code": "CF-ORE", "name": "Oregon Ducks", "espn_id": "2483"},
    {"code": "CF-UCLA", "name": "UCLA Bruins", "espn_id": "26"},
    {"code": "CF-WASH", "name": "Washington Huskies", "espn_id": "264"},
    {"code": "CF-CLEM", "name": "Clemson Tigers", "espn_id": "228"},
    {"code": "CF-FSU", "name": "Florida State Seminoles", "espn_id": "52"},
    {"code": "CF-MIA", "name": "Miami Hurricanes", "espn_id": "2390"},
    {"code": "CF-UNC", "name": "North Carolina Tar Heels", "espn_id": "153"},
    {"code": "CF-VT", "name": "Virginia Tech Hokies", "espn_id": "259"},
]
COLLEGE_TEAM_NAMES_BY_CODE = {t["code"]: t["name"] for t in COLLEGE_TEAMS}
COLLEGE_TEAM_ESPN_ID_BY_CODE = {t["code"]: t["espn_id"] for t in COLLEGE_TEAMS}


def team_logo_url(league_key: str, code: str) -> str | None:
    """ESPN's team logo CDN uses a predictable path -- no need to fetch or
    store anything, just build the URL from data we already have."""
    if league_key == "nfl":
        return f"https://a.espncdn.com/i/teamlogos/nfl/500/{code.lower()}.png"
    if league_key == "college":
        espn_id = COLLEGE_TEAM_ESPN_ID_BY_CODE.get(code)
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{espn_id}.png" if espn_id else None
    return None


# Curated real team/school brand colors (primary, secondary), used to theme
# the dashboard once a manager claims that team -- hand-picked rather than
# extracted from the logo images at runtime for reliability.
DEFAULT_TEAM_COLORS = {"primary": "#34d399", "secondary": "#22d3ee"}  # gridiron-accent fallback

TEAM_COLORS: dict[str, dict[str, str]] = {
    # NFL
    "ARI": {"primary": "#97233F", "secondary": "#000000"},
    "ATL": {"primary": "#A71930", "secondary": "#000000"},
    "BAL": {"primary": "#241773", "secondary": "#9E7C0C"},
    "BUF": {"primary": "#00338D", "secondary": "#C60C30"},
    "CAR": {"primary": "#0085CA", "secondary": "#101820"},
    "CHI": {"primary": "#0B162A", "secondary": "#C83803"},
    "CIN": {"primary": "#FB4F14", "secondary": "#000000"},
    "CLE": {"primary": "#311D00", "secondary": "#FF3C00"},
    "DAL": {"primary": "#003594", "secondary": "#869397"},
    "DEN": {"primary": "#FB4F14", "secondary": "#002244"},
    "DET": {"primary": "#0076B6", "secondary": "#B0B7BC"},
    "GB": {"primary": "#203731", "secondary": "#FFB612"},
    "HOU": {"primary": "#03202F", "secondary": "#A71930"},
    "IND": {"primary": "#002C5F", "secondary": "#A2AAAD"},
    "JAX": {"primary": "#101820", "secondary": "#D7A22A"},
    "KC": {"primary": "#E31837", "secondary": "#FFB81C"},
    "LAC": {"primary": "#0080C6", "secondary": "#FFC20E"},
    "LAR": {"primary": "#003594", "secondary": "#FFA300"},
    "LV": {"primary": "#000000", "secondary": "#A5ACAF"},
    "MIA": {"primary": "#008E97", "secondary": "#FC4C02"},
    "MIN": {"primary": "#4F2683", "secondary": "#FFC62F"},
    "NE": {"primary": "#002244", "secondary": "#C60C30"},
    "NO": {"primary": "#D3BC8D", "secondary": "#101820"},
    "NYG": {"primary": "#0B2265", "secondary": "#A71930"},
    "NYJ": {"primary": "#125740", "secondary": "#000000"},
    "PHI": {"primary": "#004C54", "secondary": "#A5ACAF"},
    "PIT": {"primary": "#FFB612", "secondary": "#101820"},
    "SEA": {"primary": "#002244", "secondary": "#69BE28"},
    "SF": {"primary": "#AA0000", "secondary": "#B3995D"},
    "TB": {"primary": "#D50A0A", "secondary": "#34302B"},
    "TEN": {"primary": "#0C2340", "secondary": "#4B92DB"},
    "WSH": {"primary": "#5A1414", "secondary": "#FFB612"},
    # College
    "CF-ALA": {"primary": "#9E1B32", "secondary": "#828A8F"},
    "CF-UGA": {"primary": "#BA0C2F", "secondary": "#000000"},
    "CF-AUB": {"primary": "#0C2340", "secondary": "#E87722"},
    "CF-TENN": {"primary": "#FF8200", "secondary": "#58595B"},
    "CF-LSU": {"primary": "#461D7C", "secondary": "#FDD023"},
    "CF-FLA": {"primary": "#0021A5", "secondary": "#FA4616"},
    "CF-TAM": {"primary": "#500000", "secondary": "#8E8C84"},
    "CF-MISS": {"primary": "#14213D", "secondary": "#CE1126"},
    "CF-TEX": {"primary": "#BF5700", "secondary": "#333F48"},
    "CF-OU": {"primary": "#841617", "secondary": "#EAAA00"},
    "CF-OKST": {"primary": "#FF7300", "secondary": "#000000"},
    "CF-BAY": {"primary": "#154734", "secondary": "#FFB81C"},
    "CF-TCU": {"primary": "#4D1979", "secondary": "#A3A9AC"},
    "CF-KSU": {"primary": "#512888", "secondary": "#A7A8AA"},
    "CF-UTAH": {"primary": "#CC0000", "secondary": "#000000"},
    "CF-ND": {"primary": "#0C2340", "secondary": "#AE9142"},
    "CF-OSU": {"primary": "#BB0000", "secondary": "#666666"},
    "CF-MICH": {"primary": "#00274C", "secondary": "#FFCB05"},
    "CF-MSU": {"primary": "#18453B", "secondary": "#B0B0B0"},
    "CF-PSU": {"primary": "#041E42", "secondary": "#B0B0B0"},
    "CF-WIS": {"primary": "#C5050C", "secondary": "#000000"},
    "CF-IOWA": {"primary": "#FFCD00", "secondary": "#000000"},
    "CF-NEB": {"primary": "#E41C38", "secondary": "#000000"},
    "CF-USC": {"primary": "#990000", "secondary": "#FFC72C"},
    "CF-ORE": {"primary": "#154733", "secondary": "#FEE123"},
    "CF-UCLA": {"primary": "#2D68C4", "secondary": "#F2A900"},
    "CF-WASH": {"primary": "#4B2E83", "secondary": "#B7A57A"},
    "CF-CLEM": {"primary": "#F56600", "secondary": "#522D80"},
    "CF-FSU": {"primary": "#782F40", "secondary": "#CEB888"},
    "CF-MIA": {"primary": "#F47321", "secondary": "#005030"},
    "CF-UNC": {"primary": "#7BAFD4", "secondary": "#13294B"},
    "CF-VT": {"primary": "#630031", "secondary": "#CF4420"},
}


def team_colors(code: str | None) -> dict[str, str]:
    if code is None:
        return DEFAULT_TEAM_COLORS
    return TEAM_COLORS.get(code, DEFAULT_TEAM_COLORS)


def team_logo_url_by_code(code: str | None) -> str | None:
    """Infers the league from the code's prefix (college codes are always
    "CF-"-prefixed) so a bare team code is enough to build the logo URL --
    no need to look up the team's league via a relationship or extra query."""
    if code is None:
        return None
    return team_logo_url("college", code) if code.startswith("CF-") else team_logo_url("nfl", code)

COLLEGE_DIVISIONS = {
    "National South": ["CF-ALA", "CF-UGA", "CF-AUB", "CF-TENN"],
    "National West": ["CF-LSU", "CF-FLA", "CF-TAM", "CF-MISS"],
    "National Big12": ["CF-TEX", "CF-OU", "CF-OKST", "CF-BAY"],
    "National Mixed": ["CF-TCU", "CF-KSU", "CF-UTAH", "CF-ND"],
    "American East": ["CF-OSU", "CF-MICH", "CF-MSU", "CF-PSU"],
    "American North": ["CF-WIS", "CF-IOWA", "CF-NEB", "CF-USC"],
    "American West": ["CF-ORE", "CF-UCLA", "CF-WASH", "CF-CLEM"],
    "American ACC": ["CF-FSU", "CF-MIA", "CF-UNC", "CF-VT"],
}
COLLEGE_TEAM_DIVISION_BY_CODE = {code: division for division, codes in COLLEGE_DIVISIONS.items() for code in codes}
COLLEGE_TEAM_CONFERENCE_BY_CODE = {
    code: division.split(" ")[0] for code, division in COLLEGE_TEAM_DIVISION_BY_CODE.items()
}

# --- league registry: lets league-generic code (season_manager, bots, ...)
# look up the right team/division data by League.key instead of branching.
LEAGUES = {
    "nfl": {
        "name": "NFL",
        "teams": NFL_TEAMS,
        "team_names_by_code": NFL_TEAM_NAMES_BY_CODE,
        "divisions": NFL_DIVISIONS,
        "team_conference_by_code": NFL_TEAM_CONFERENCE_BY_CODE,
    },
    "college": {
        "name": "College Football",
        "teams": COLLEGE_TEAMS,
        "team_names_by_code": COLLEGE_TEAM_NAMES_BY_CODE,
        "divisions": COLLEGE_DIVISIONS,
        "team_conference_by_code": COLLEGE_TEAM_CONFERENCE_BY_CODE,
    },
}

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

# --- training: sessions needed per +1 OVR, banded by current rating (#20) --
# fast early growth, then a real, deliberate wall approaching the 90s so a
# rating that high stays meaningful instead of something everyone reaches.
TRAINING_SESSIONS_PER_POINT = [
    (80, 1),
    (90, 4),
    (95, 10),
    (100, 25),
]


def sessions_required_for_next_point(overall: int) -> int:
    for threshold, sessions in TRAINING_SESSIONS_PER_POINT:
        if overall < threshold:
            return sessions
    return TRAINING_SESSIONS_PER_POINT[-1][1]


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

# --- player salaries (daily upkeep, deducted from every team incl. bots) ---
BASE_DAILY_SALARY = 1_500


def player_daily_salary(overall: int) -> int:
    return round(BASE_DAILY_SALARY * (overall / 50) ** 2)


def player_market_value(base_price: float, ovr: int, age: int) -> float:
    """Cubic base curve, same as before, plus a compounding rarity premium
    above 80 OVR (#20 follow-up) -- without it a 99 OVR player cost about
    10% of the 1,000,000 starting budget, cheap enough to buy an entire
    elite roster on day one even though the generation formula makes 90+ a
    genuine rarity. At 8% per point above 80, a 99 OVR player now runs
    roughly half the starting budget -- a real splurge, not pocket change."""
    value = base_price * (ovr / 50) ** 3
    if ovr > 80:
        value *= 1.08 ** (ovr - 80)
    return value * (35 - age)
