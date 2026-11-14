"""Parse the verbatim Week 10 transcription into structured JSON.

Input : a57af0ab/data/raw/injury-w10-transcription.txt  (row-by-row copy of nfl.com injury report)
Output: a57af0ab/data/injuries-2026-w10.json
Stdlib only. No values are inferred: blank fields stay blank.
"""
import json
import pathlib
import collections

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "data" / "raw" / "injury-w10-transcription.txt"
OUT = HERE / "data" / "injuries-2026-w10.json"
REPORT_URL = "https://www.nfl.com/injuries/league/2026/reg10"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"

# Position -> official-report position group (groupings are ours, labelled as such).
GROUP = {
    "QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
    "T": "OL", "G": "OL", "C": "OL",
    "DE": "DL", "DT": "DL",
    "LB": "LB",
    "CB": "DB", "S": "DB", "SAF": "DB",
    "K": "ST", "P": "ST", "LS": "ST",
}
GROUP_ORDER = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "ST"]
GAME_STATUSES = ["Out", "Doubtful", "Questionable"]


def parse():
    games, rows = [], []
    current = None
    for lineno, line in enumerate(RAW.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if parts[0] == "GAME":
            _, slug, when, network, first, second, chunks = parts
            current = {
                "game_slug": slug,
                "game_page_url": f"https://www.nfl.com/games/{slug}-2026-reg-10",
                "day_time_as_printed": when,
                "network_as_printed": network,
                "first_listed_team": first,
                "second_listed_team": second,
                "report_chunks": chunks,
                "line": lineno,
            }
            games.append(current)
        elif parts[0] == "ROW":
            if current is None:
                raise SystemExit(f"line {lineno}: ROW before any GAME")
            if len(parts) != 7:
                raise SystemExit(f"line {lineno}: expected 7 fields, got {len(parts)}")
            _, team, player, pos, injuries, practice, game_status = parts
            if team not in (current["first_listed_team"], current["second_listed_team"]):
                raise SystemExit(f"line {lineno}: team {team} not in game {current['game_slug']}")
            if pos not in GROUP:
                raise SystemExit(f"line {lineno}: unknown position {pos!r}")
            flags = []
            if "Not injury related" in injuries:
                flags.append("NOT_INJURY_RELATED_PER_REPORT")
            if game_status == "Out" and practice == "Full Participation in Practice":
                flags.append("OUT_WITH_FULL_PRACTICE_VERBATIM")
            if not game_status and practice == "Did Not Participate In Practice":
                flags.append("DNP_NO_GAME_STATUS_YET")
            rows.append({
                "id": f"W10-{len(rows) + 1:03d}",
                "week": 10,
                "season": 2026,
                "game_slug": current["game_slug"],
                "team": team,
                "player": player,
                "position": pos,
                "position_group": GROUP[pos],
                "injuries": injuries,
                "practice_status": practice,
                "game_status": game_status,
                "flags": flags,
                "source_urls": [REPORT_URL, current["game_page_url"]],
            })
    return games, rows


def summarize(games, rows):
    teams = collections.OrderedDict()
    for g in games:
        for t in (g["first_listed_team"], g["second_listed_team"]):
            teams[t] = {"team": t, "game_slug": g["game_slug"], "rows": 0,
                        "groups": {k: {"listed": 0, "out": 0, "doubtful": 0, "questionable": 0, "dnp": 0}
                                   for k in GROUP_ORDER}}
    for r in rows:
        t = teams[r["team"]]
        t["rows"] += 1
        grp = t["groups"][r["position_group"]]
        grp["listed"] += 1
        if r["game_status"] in GAME_STATUSES:
            grp[r["game_status"].lower()] += 1
        if r["practice_status"] == "Did Not Participate In Practice":
            grp["dnp"] += 1
    out = []
    for t in teams.values():
        flags = []
        for gname, g in t["groups"].items():
            absent = g["out"] + g["doubtful"]
            if absent >= 2:
                flags.append(f"{gname}: {absent} listed Out or Doubtful (starter status unverified)")
        t["position_group_flags"] = flags
        out.append(t)
    return out


def main():
    games, rows = parse()
    teams = summarize(games, rows)
    per_game = collections.Counter(r["game_slug"] for r in rows)
    for g in games:
        g["rows"] = per_game[g["game_slug"]]
    doc = {
        "title": "Official NFL Week 10 (2026) injury report — transcribed rows",
        "captured_utc_date": "2026-11-14",
        "source_report": REPORT_URL,
        "source_schedule": SCHEDULE_URL,
        "report_publish_time": "NOT DISPLAYED ON PAGE (flagged)",
        "games_on_report": len(games),
        "teams_on_report": len(teams),
        "teams_on_bye_per_schedule": ["CHI", "DEN", "PHI", "TB"],
        "rows_total": len(rows),
        "position_group_definition": "Groups are this project's labels: QB; RB (incl. FB); WR; TE; OL (T, G, C); DL (DE, DT); LB; DB (CB, S); ST (K, P, LS).",
        "starter_backup_status": "BLANK — no official nfl.com depth chart was retrieved (https://www.nfl.com/teams/new-york-giants/depth-chart returned 404 on 2026-11-14).",
        "games": games,
        "teams": teams,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"games={len(games)} teams={len(teams)} rows={len(rows)} -> {OUT.relative_to(HERE.parent)}")
    for g in games:
        print(f"  {g['game_slug']:<22} rows={g['rows']}")


if __name__ == "__main__":
    main()
