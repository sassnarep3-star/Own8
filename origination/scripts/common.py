"""Shared helpers for session 4bc92a5f's origination lab. Standard library only."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../origination
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

# nfl.com team URL slug -> abbreviation exactly as printed in the nfl.com scores text render
# (e.g. "RAMSLos Angeles RamsLARLos Angeles Rams" -> LAR; Arizona is printed "AZ").
SLUG_TO_ABBR = {
    "arizona-cardinals": "AZ", "atlanta-falcons": "ATL", "baltimore-ravens": "BAL", "buffalo-bills": "BUF",
    "carolina-panthers": "CAR", "chicago-bears": "CHI", "cincinnati-bengals": "CIN", "cleveland-browns": "CLE",
    "dallas-cowboys": "DAL", "denver-broncos": "DEN", "detroit-lions": "DET", "green-bay-packers": "GB",
    "houston-texans": "HOU", "indianapolis-colts": "IND", "jacksonville-jaguars": "JAX", "kansas-city-chiefs": "KC",
    "las-vegas-raiders": "LV", "los-angeles-chargers": "LAC", "los-angeles-rams": "LAR", "miami-dolphins": "MIA",
    "minnesota-vikings": "MIN", "new-england-patriots": "NE", "new-orleans-saints": "NO", "new-york-giants": "NYG",
    "new-york-jets": "NYJ", "philadelphia-eagles": "PHI", "pittsburgh-steelers": "PIT", "san-francisco-49ers": "SF",
    "seattle-seahawks": "SEA", "tampa-bay-buccaneers": "TB", "tennessee-titans": "TEN", "washington-commanders": "WAS",
}
ABBR_TO_SLUG = {v: k for k, v in SLUG_TO_ABBR.items()}

SCORES_URL = "https://www.nfl.com/scores/2026/week-{w}"
GAME_URL = "https://www.nfl.com/games/{slug}"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
DIVISION_URL = "https://www.nfl.com/standings/division/2026/REG"
TEAM_URL = "https://www.nfl.com/teams/{slug}/"


def read_rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            yield line.split("|")


def load_json(name, base=OUT):
    with open(os.path.join(base, name), encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj, name, base=OUT):
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def rec(s):
    """'3-1-0' -> (3,1,0)"""
    a = [int(x) for x in s.split("-")]
    assert len(a) == 3, s
    return tuple(a)


def pct(w, l, t):
    g = w + l + t
    return (w + 0.5 * t) / g if g else 0.0
