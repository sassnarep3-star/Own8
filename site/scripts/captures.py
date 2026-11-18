#!/usr/bin/env python3
"""Parses the stored official captures into JSON and writes the SHA-256 manifest.

Inputs : site/data/captures/*.md  (text copied from fetch-tool output, see the header of each file)
Outputs: site/data/injuries-w11.json, site/data/gamebook-w10-lac-bal.json,
         site/data/captures/manifest.json (sha256 + byte count of every capture file)
Run    : python3 site/scripts/captures.py     (check.py re-parses and re-hashes; it fails on any drift)
Standard library only.
"""
import hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(SITE, "data", "captures")
INJ_MD = os.path.join(CAP, "nfl-injuries-reg11-2026-11-18.md")
GB_MD = os.path.join(CAP, "nfl-gamebook-w10-lac-bal.md")
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg11"
GB_URL = "https://static.www.nfl.com/image/upload/v1794916121/gamecenter/ab78ad5a-4feb-11f1-abca-2c54536568a9.pdf"
GAMECENTRE_URL = "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"
RETRIEVED = "2026-11-18T06:27:14Z"  # upper bound: the sandbox clock read after the last fetch-tool call


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_rows(text):
    """Yields (section, cells) for each data row of a markdown table (header and separator skipped)."""
    section, header_seen = "", False
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            header_seen = False
            continue
        if not line.startswith("|"):
            continue
        c = cells(line)
        if all(set(x) <= set("-") and x for x in c):
            continue  # separator
        if not header_seen:
            header_seen = True
            continue
        yield section, c


def parse_injuries(text):
    players, nir = [], []
    for section, c in table_rows(text):
        if len(c) == 6:
            team, player, pos, inj, prac, game = c
            players.append({
                "game": "IND@HOU",
                "team": team, "player": player, "position": pos,
                "injury": inj or None,            # blank on the page as read
                "practice_status": prac or None,
                "game_status": game or None,      # blank on the page as read
                "source_url": INJ_URL,
                "retrieved_utc": RETRIEVED,
            })
        elif len(c) == 5:
            game, kick, net, away, home = c
            nir.append({"game": game, "kickoff_et": kick, "network": net,
                        "away_status": away, "home_status": home,
                        "source_url": INJ_URL, "retrieved_utc": RETRIEVED})
    return players, nir


def parse_gamebook(text):
    scoring, lineup, inactive = [], [], []
    for section, c in table_rows(text):
        if len(c) == 6 and c[0] in ("Chargers", "Ravens") and c[1].isdigit():
            scoring.append({"team": c[0], "qtr": int(c[1]), "time": c[2], "play": c[3],
                            "visitor_total": int(c[4]), "home_total": int(c[5])})
        elif len(c) == 5 and c[0] in ("Chargers", "Ravens") and c[1] in ("Offense", "Defense"):
            lineup.append({"side": c[0], "unit": c[1], "position": c[2],
                           "number": c[3], "player": c[4]})
        elif len(c) == 3 and c[0] in ("Chargers", "Ravens") and c[1] in ("Did Not Play", "Not Active"):
            inactive.append({"side": c[0], "status": c[1], "players": c[2]})
    last = scoring[-1]
    final = {"visitor": "Los Angeles Chargers", "home": "Baltimore Ravens",
             "visitor_score": last["visitor_total"], "home_score": last["home_total"]}
    return scoring, lineup, inactive, final


def sha256(path):
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest(), len(data)


def main():
    with open(INJ_MD, encoding="utf-8") as f:
        inj_text = f.read()
    with open(GB_MD, encoding="utf-8") as f:
        gb_text = f.read()

    players, nir = parse_injuries(inj_text)
    scoring, lineup, inactive, final = parse_gamebook(gb_text)

    inj_json = {
        "source_url": INJ_URL, "retrieved_utc": RETRIEVED, "capture": "data/captures/nfl-injuries-reg11-2026-11-18.md",
        "week": 11,
        "note": ("Week 11 official injury report as read on 2026-11-18. Only the Thursday game lists players. "
                 "12 games show 'No Injuries Reported' for both clubs at read time, so the report is an early read: "
                 "later reads are needed before any absence is treated as final. Injury and game-status cells are blank on the page as read."),
        "players": players, "games_no_injuries_reported": nir,
        "counts": {"players_listed": len(players), "games_listed": 1 + len(nir), "games_no_injuries": len(nir)},
    }
    gb_json = {
        "game": "Los Angeles Chargers at Baltimore Ravens", "week": 10, "date": "2026-11-16",
        "game_centre_url": GAMECENTRE_URL, "game_book_url": GB_URL, "retrieved_utc": RETRIEVED,
        "capture": "data/captures/nfl-gamebook-w10-lac-bal.md",
        "status_on_game_centre": "Final",
        "venue": "M&T Bank Stadium, Baltimore, MD",
        "final": final,
        "scoring_plays": scoring, "lineups": lineup, "inactives": inactive,
        "note": ("Score taken from the Game Book scoring-play table (last running total). The quarter table in the PDF "
                 "text is offset by one row and is not used. Lineups are as printed by the Game Book."),
    }
    outs = {
        os.path.join(SITE, "data", "injuries-w11.json"): inj_json,
        os.path.join(SITE, "data", "gamebook-w10-lac-bal.json"): gb_json,
    }
    for path, obj in outs.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write("\n")

    manifest = {
        "description": ("SHA-256 of each stored official capture. Each capture is text copied from fetch-tool output "
                        "(not raw HTTP bytes; shell curl to nfl.com fails with a TLS error). The hash proves the stored text "
                        "has not changed since capture; it does not prove the server bytes."),
        "captures": [],
    }
    for name, url, kind, retrieved in (
        ("nfl-injuries-reg11-2026-11-18.md", INJ_URL, "official injury report (Week 11)", RETRIEVED),
        ("nfl-gamebook-w10-lac-bal.md", GB_URL, "official NFL Game Book PDF (Week 10, LAC@BAL)", RETRIEVED),
    ):
        path = os.path.join(CAP, name)
        h, n = sha256(path)
        manifest["captures"].append({"file": f"site/data/captures/{name}", "kind": kind, "source_url": url,
                                     "retrieved_utc": retrieved, "sha256": h, "bytes": n})
    with open(os.path.join(CAP, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(f"injury rows {len(players)}, NIR games {len(nir)}; scoring rows {len(scoring)}, lineup rows {len(lineup)}, "
          f"inactive rows {len(inactive)}, final {final['visitor_score']}-{final['home_score']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
