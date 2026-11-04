#!/usr/bin/env python3
"""Build a dated, fail-closed competition evidence report (stdlib only).

No data outside competition/ is modified. Legacy review is explicitly tied to
starting commit 7c2f545, not a claim about every parallel branch's newer work.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from .core import EvidenceError, american_to_decimal, baseline_lines, number, paired_correlation, two_way_normalization
    from .evaluation import evaluate_leaderboard
    from .ledger import EvidenceBook, digest, read_chain
except ImportError:
    from core import EvidenceError, american_to_decimal, baseline_lines, number, paired_correlation, two_way_normalization
    from evaluation import evaluate_leaderboard
    from ledger import EvidenceBook, digest, read_chain

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BASE = "7c2f5459350c8a94f13cd12d4315ba92b044275a"
AS_OF = "2026-11-04"


def load(relative):
    return json.loads((ROOT / relative).read_text())


def write(name, value):
    out = ROOT / "results" / name
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def rows(name):
    with (ROOT / "data/evidence" / name).open(newline="") as f:
        return list(csv.DictReader(f))


def baseline_blob(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=REPO)


def verify_manifest():
    results = []
    for record in load("data/evidence-manifest.json"):
        path = ROOT / record["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(newline="") as f:
            count = len(list(csv.DictReader(f)))
        if actual != record["sha256"] or count != record["rows"]:
            raise EvidenceError(f"Evidence transcription changed without re-verification: {record['path']}")
        results.append({"path": record["path"], "sha256": actual, "rows": count,
                        "status": "LOCAL_INTEGRITY_PASS", "source_ids": record["source_ids"]})
    return results


def prepare_evidence():
    standings = rows("standings-2026-11-04.csv")
    teams = {}
    for t in standings:
        if t["abbr"] in teams:
            raise EvidenceError("Duplicate team")
        for k in ("W", "L", "T", "PF", "PA", "NET"):
            t[k] = int(t[k])
        t["PCT"] = float(t["PCT"])
        gp = t["W"] + t["L"] + t["T"]
        if gp <= 0 or t["NET"] != t["PF"] - t["PA"] or abs(t["PCT"] - (t["W"] + t["T"] / 2) / gp) > .000501:
            raise EvidenceError("Standings arithmetic does not reconcile")
        teams[t["abbr"]] = t
    if len(teams) != 32 or sum(t["PF"] for t in standings) != sum(t["PA"] for t in standings) or sum(t["W"] for t in standings) != sum(t["L"] for t in standings):
        raise EvidenceError("Incomplete/unbalanced league snapshot")
    fixtures = []
    for f in rows("fixtures-2026-week9.csv"):
        if f["away"] not in teams or f["home"] not in teams or f["away"] == f["home"]:
            raise EvidenceError("Bad fixture identity")
        local = datetime.strptime(f["date"] + " " + f["kickoff_est"], "%Y-%m-%d %I:%M %p").replace(tzinfo=ZoneInfo("America/New_York"))
        if local.tzname() != "EST":
            raise EvidenceError("Literal source timezone does not match conversion")
        f.update({"event_id": f["game_slug"], "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
                  "source_ids": ["NFL-SCHEDULE", "NFL-INJURIES"], "verification": "confirmed_transcription",
                  "kickoff_utc": local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
                  "kickoff_conversion": "DERIVED from official EST date/time using Python zoneinfo, not an operator timestamp",
                  "neutral_site": True if f["neutral_site"] == "true" else None,
                  "location_label": f["location_label"] or None,
                  "game_url": "https://www.nfl.com/games/" + f["game_slug"]})
        fixtures.append(f)
    if len({f["event_id"] for f in fixtures}) != 15 or len({t for f in fixtures for t in (f["away"], f["home"])}) != 30:
        raise EvidenceError("Incomplete/duplicate Week 9 fixtures")
    scores = []
    for s in rows("scores-2026-week8.csv"):
        s["away_score"], s["home_score"] = int(s["away_score"]), int(s["home_score"])
        if min(s["away_score"], s["home_score"]) < 0 or s["status"] != "Final":
            raise EvidenceError("Not a verified final score")
        s.update({"event_id": s["game_slug"], "source_url": "https://www.nfl.com/scores/2026/week-8",
                  "source_ids": ["NFL-SCORES"], "verification": "confirmed_transcription",
                  "confirmed_fields": ["away", "home", "away_score", "home_score", "date", "status"],
                  "evidence_sha256": digest(s)})
        scores.append(s)
    if len({s["event_id"] for s in scores}) != 14:
        raise EvidenceError("Duplicate/missing official final game")
    fixt_by_teams = {(f["away"], f["home"]): f for f in fixtures}
    markets = []
    for row in rows("draftkings-2026-week9.csv"):
        f = fixt_by_teams.get((row["away"], row["home"]))
        if f is None:
            raise EvidenceError("Primary quote has no exact NFL fixture join")
        for k in ("away_handicap", "home_handicap", "total"):
            row[k] = float(number(row[k]))
        for k in ("away_spread_odds", "home_spread_odds", "over_odds", "under_odds", "away_moneyline", "home_moneyline"):
            row[k] = int(row[k]); american_to_decimal(row[k])
        if row["away_handicap"] + row["home_handicap"] != 0 or row["total"] <= 0:
            raise EvidenceError("Operator market column alignment failed")
        moneyline = two_way_normalization(row["away_moneyline"], row["home_moneyline"])
        row.update({"event_id": f["event_id"], "source_ids": ["NFL-SCHEDULE", "DK-LINES"],
                    "operator_event_url": "https://sportsbook.draftkings.com/event/" + row["event_path"],
                    "source_url": "https://sportsbook.draftkings.com/leagues/football/nfl",
                    "verification": "confirmed_transcription", "checked_on_utc": AS_OF,
                    "observed_at_utc": None, "quote_updated_at_utc": None,
                    "provider_server_time_raw": "11/04/2026 3:14:47 PM", "provider_time_zone": None,
                    "freshness_status": "HOLD_UNCONFIRMED_UPDATE_TIME",
                    "two_way_ml_away_share": moneyline["a_share"], "two_way_ml_home_share": moneyline["b_share"],
                    "moneyline_overround": moneyline["overround"],
                    "spread_overround": two_way_normalization(row["away_spread_odds"], row["home_spread_odds"])["overround"],
                    "total_overround": two_way_normalization(row["over_odds"], row["under_odds"])["overround"],
                    "normalization_note": "DERIVED proportional two-way shares, conditional on non-tie/non-push settlement; not a true probability or a model forecast",
                    "kickoff_discrepancy": row["away"] == "LV" and row["home"] == "SF"})
        markets.append(row)
    if len(markets) != 15 or len({r["event_id"] for r in markets}) != 15:
        raise EvidenceError("Missing/duplicate Week 9 primary market row")
    injuries = rows("injuries-2026-week9.csv")
    for row in injuries:
        row.update({"injury": row["injury"] or None, "game_status": row["game_status"] or None,
                    "source_ids": ["NFL-INJURIES"], "participation_clearance": None})
    if len(injuries) != 28:
        raise EvidenceError("Practice snapshot row count changed")
    return standings, fixtures, scores, markets, injuries


def inherited_coverage(standings, fixtures, scores):
    """Every original row/field considered; unsupported values are EXPLICIT nulls.

    This is not a claim that the entire inherited source universe was audited.
    Evidence comparison is limited to the confirmed selected fields below.
    """
    sm = {t["abbr"]: t for t in standings}
    fm = {(f["away"], f["home"]): f for f in fixtures}
    om = {(s["away"], s["home"]): s for s in scores}
    data_paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "data"], cwd=REPO, text=True).splitlines()
    output = []
    datasets = []
    for path in data_paths:
        if not path.endswith((".json", ".csv")):
            continue
        raw = baseline_blob(path).decode()
        if path.endswith(".csv"):
            captured = list(csv.DictReader(raw.splitlines()))
        else:
            obj = json.loads(raw)
            captured = []
            if isinstance(obj, dict):
                for key in ("teams", "players", "games", "rows", "lines", "items", "sources"):
                    if isinstance(obj.get(key), list):
                        captured = obj[key]; break
        count_checked = 0
        for index, record in enumerate(captured, 1):
            if not isinstance(record, dict):
                continue
            parse_issue = None
            if None in record:
                # DictReader uses None for surplus fields. Preserve the anomaly
                # under an explicit neutral key; never shift or guess columns.
                record = dict(record)
                record["__unlabeled_surplus_columns"] = record.pop(None)
                parse_issue = "CSV row has surplus unnamed columns; affected trailing labels are not trusted"
            checked, derived = {}, {}
            if path == "data/standings-2026-reg-w8.json":
                current = sm.get(record.get("abbr"), {})
                for key in ("abbr", "W", "L", "T", "PCT", "PF", "PA", "NET", "STRK"):
                    if key in current and record.get(key) == current[key]:
                        checked[key] = current[key]
                if record.get("name") == current.get("team"):
                    checked["name"] = current["team"]
                refs = ["NFL-STANDINGS"]
            elif path == "data/schedule-2026-week9.json":
                current = fm.get((record.get("away"), record.get("home")), {})
                for key in ("away", "home", "date", "network"):
                    if key in current and record.get(key) == current[key]:
                        checked[key] = current[key]
                if record.get("kickoff_et") == current.get("kickoff_est"):
                    checked["kickoff_et"] = current["kickoff_est"]
                if record.get("game_url") == current.get("game_url"):
                    checked["game_url"] = current["game_url"]
                refs = ["NFL-SCHEDULE", "NFL-INJURIES"]
            elif path == "data/scores-2026-week8.json":
                current = om.get((record.get("away"), record.get("home")), {})
                for key in ("away", "home", "date", "away_score", "home_score", "status"):
                    if key in current and record.get(key) == current[key]:
                        checked[key] = current[key]
                refs = ["NFL-SCORES"]
            elif path == "data/nfl-2026-standings.csv":
                current = sm.get(record.get("abbr"), {})
                mapping = {"abbr":"abbr", "team":"team", "w":"W", "l":"L", "t":"T", "pct":"PCT", "pf":"PF", "pa":"PA", "net_pts":"NET", "streak":"STRK"}
                for original, fresh in mapping.items():
                    if original in record and fresh in current:
                        value = record[original]
                        if fresh in {"W", "L", "T", "PCT", "PF", "PA", "NET"}:
                            value = float(number(value))
                        if value == current[fresh]:
                            checked[original] = current[fresh]
                refs = ["NFL-STANDINGS"]
            elif "market" in path:
                refs = ["DK-LINES"]
            elif "injur" in path or "news" in path:
                refs = ["NFL-INJURIES"]
            elif "passing" in path or "rushing" in path or "receiving" in path or "interceptions" in path:
                refs = ["NFL-NGS"]
            else:
                refs = ["NFL-STANDINGS"]
            missing = sorted(set(record) - set(checked) - set(derived))
            output.append({"dataset": path, "row": index,
                           "status": "SELECTED_FIELDS_CONFIRMED" if checked else "UNVERIFIED_IN_THIS_MODULE",
                           "confirmed_fields": sorted(checked), "unverified_fields": missing, "parse_issue": parse_issue,
                           "values": {key: checked.get(key) for key in record},
                           "source_ids": refs,
                           "code_url": f"https://github.com/sassnarep3-star/Own8/blob/{BASE}/{path}",
                           "reference_note": "Official links are manual review targets; they do NOT verify blank fields or constitute an assertion that an inherited source URL is current."})
            count_checked += bool(checked)
        datasets.append({"path": path, "rows": len(captured), "rows_with_some_confirmed_fields": count_checked,
                         "rows_without_external_field_confirmation": len(captured) - count_checked,
                         "source_ids": output[-1]["source_ids"] if captured and output else ["NFL-STANDINGS"]})
    return {"baseline_commit": BASE, "scope": "All rows in starting root data JSON/CSV files inventoried; selected standings, fixtures and final-score fields independently source-checked. Archives inventoried at file level only.",
            "rows": output, "datasets": datasets,
            "confirmed_field_cells": sum(len(r["confirmed_fields"]) for r in output),
            "unverified_field_cells": sum(len(r["unverified_fields"]) for r in output)}


def repository_inventory():
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE], cwd=REPO, text=True).splitlines()
    files = []
    for path in paths:
        raw = baseline_blob(path)
        try:
            text = raw.decode("utf-8")
            lines = text.splitlines()
            kind = "AUTOMATED_TEXT_LINE_INVENTORY"
        except UnicodeDecodeError:
            lines = []; kind = "BINARY_NOT_FACT_CHECKED"
        files.append({"path": path, "bytes": len(raw), "lines": len(lines),
                      "sha256": hashlib.sha256(raw).hexdigest(), "review": kind,
                      "source_url": f"https://github.com/sassnarep3-star/Own8/blob/{BASE}/{path}"})
    code = baseline_blob("scripts/analyze.py").decode().splitlines()
    needles = [("Wrong spread convention", "edge = model_spread_home - mkt"),
               ("Conditional accepted as pass", 'in ("PASS", "CONDITIONAL")'),
               ("Invented zero performance", '"realized_pts": 0.0'),
               ("Candidate ignores complete gates", '"candidate": (edge is not None')]
    findings = []
    for title, needle in needles:
        for n, line in enumerate(code, 1):
            if needle in line:
                findings.append({"title": title, "path": "scripts/analyze.py", "line": n, "code": line.strip(),
                                 "source_ids": ["DK-FOOTBALL", "NFL-SCHEDULE"],
                                 "code_url": f"https://github.com/sassnarep3-star/Own8/blob/{BASE}/scripts/analyze.py#L{n}"})
    return {"baseline_commit": BASE, "file_count": len(files), "text_lines_inventoried": sum(f["lines"] for f in files),
            "scope_warning": "Automated inventory is NOT substantive external verification of every line. Targeted code findings plus selected-field source checks only. No claim about newer parallel-session fixes.",
            "files": files, "findings": findings}


def main():
    integrity = verify_manifest()
    standings, fixtures, scores, markets, injuries = prepare_evidence()
    checkpoint = load("data/checkpoint.json")
    chain = read_chain(ROOT / "data/ledger.jsonl", checkpoint["head"], checkpoint["record_count"])
    if chain:
        # No unreviewed backfill or synthetic fixtures are allowed in production.
        raise EvidenceError("Production receipt/outcome re-verification adapter must be installed before a nonempty ledger is promoted")
    catalog = load("data/strategy-catalog.json")["strategies"]
    analysis_instant = max(m["observation_window_utc"][1] for m in load("data/evidence-manifest.json"))
    board = evaluate_leaderboard(catalog, [], analysis_instant)
    board.update({"prospectively_registered_strategies": 0, "catalog_note": "Eight proposed hypotheses are reserved in the testing family; none has a verified preregistration receipt."})
    baseline = []
    teams = {t["abbr"]: t for t in standings}
    for f in fixtures:
        baseline.append({"event_id": f["event_id"], "away": f["away"], "home": f["home"],
                         **baseline_lines(teams[f["away"]], teams[f["home"]]),
                         "source_ids": ["NFL-STANDINGS", "NFL-SCHEDULE"],
                         "method": "B0: away=(away PF/GP + home PA/GP)/2; home=(home PF/GP + away PA/GP)/2. HFA=0 project benchmark. No validated probability/edge."})
    win_pct = {t["abbr"]: (t["W"] + .5 * t["T"]) / (t["W"] + t["L"] + t["T"]) for t in standings}
    net_pg = {t["abbr"]: t["NET"] / (t["W"] + t["L"] + t["T"]) for t in standings}
    pf_pg = {t["abbr"]: t["PF"] / (t["W"] + t["L"] + t["T"]) for t in standings}
    corr = [
        {"pair": "Net points/game vs win percentage", **paired_correlation(net_pg, win_pct), "unit": "32 teams, same season snapshot", "source_ids": ["NFL-STANDINGS", "SCIPY-R"]},
        {"pair": "Points for/game vs win percentage", **paired_correlation(pf_pg, win_pct), "unit": "32 teams, same season snapshot", "source_ids": ["NFL-STANDINGS", "SCIPY-R"]},
        {"pair": "Home final points vs away final points", **paired_correlation({s["event_id"]: s["home_score"] for s in scores}, {s["event_id"]: s["away_score"] for s in scores}), "unit": "14 games, Week 8 only; one week cluster", "source_ids": ["NFL-SCORES", "SCIPY-R"]}
    ]
    for c in corr:
        c.update({"ci_low": None, "ci_high": None, "bet_correlation": False,
                  "warning": "Descriptive association, not causal/predictive skill and not a wager-outcome correlation; inferential interval withheld without validated independent clusters."})
    for pair in ("Two spread-cover indicators in different games", "Spread-cover and total-over indicators in one game", "QB passing-over and WR receiving-over indicators", "RB rushing-over and receiving-over indicators"):
        corr.append({"pair": pair, "r": None, "n": 0, "ci_low": None, "ci_high": None, "unit": "No matched verified pregame-threshold sample", "status": "UNVERIFIED", "bet_correlation": True, "source_ids": ["SCIPY-R", "NFL-SCORES", "NFL-NGS"]})
    coverage = inherited_coverage(standings, fixtures, scores)
    inventory = repository_inventory()
    write("evidence-check.json", {"checked_on_utc": AS_OF, "status": "PASS_SELECTED_FIELDS_AND_LOCAL_INTEGRITY", "manifest": integrity,
                                   "standings_rows": len(standings), "fixtures": len(fixtures), "final_scores": len(scores),
                                   "primary_price_rows": len(markets), "practice_rows": len(injuries),
                                   "warning": "Selected-field official-source transcription, not exhaustive external verification. Local checks detect arithmetic/schema/hash issues; they do not prove upstream authenticity."})
    write("snapshot.json", {"checked_on_utc": AS_OF, "standings": standings, "fixtures": fixtures, "scores": scores, "markets": markets, "injuries": injuries})
    write("reference-lines.json", {"status": "UNVALIDATED_REFERENCE_ONLY", "lines": baseline})
    write("correlations.json", {"correlations": corr})
    write("leaderboard.json", board)
    write("entry-audit.json", coverage)
    write("repository-audit.json", inventory)
    print(json.dumps({"evidence": "PASS selected fields / local integrity", "standings": len(standings), "fixtures": len(fixtures), "scores": len(scores), "prices": len(markets), "practice": len(injuries), "legacy_rows_inventoried": len(coverage["rows"]), "legacy_files_inventoried": inventory["file_count"], "locked_predictions": len(chain), "skill_qualified": board["eligible_strategies"]}, indent=2))


if __name__ == "__main__":
    main()
