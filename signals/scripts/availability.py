#!/usr/bin/env python3
"""
SB5 — availability tiers and the DEPTH of a replacement, from official sources only.

The operator's requirement: "track injuries and know any deficiencies in defenses such as 2nd, 3rd
or 4th string backups having to replace starters due to lineups. Also the same for offenses."

The honest answer has three parts, and this file produces all three:

  1. WHAT IS PUBLISHED.  A capability matrix built from probes actually performed on 2026-11-14
     (signals/data/raw/probes-2026-11-14.txt). The depth-chart URL returns 404. The roster publishes
     ACT and nothing about order. The injury report publishes practice and game status and nothing
     about who replaces whom. The Game Book publishes, after the game, the eleven men who actually
     started on each side of the ball, the substitutions, who did not play and who was inactive.

  2. WHAT CAN THEREFORE BE SAID BEFORE KICKOFF.  Almost nothing, and this file refuses to say it.
     A pregame tier for an unplayed game is blank with the reason attached. That is not a gap in the
     work; it is the finding.

  3. WHAT CAN BE SAID AFTER THE GAME — THE DEPTH MEASUREMENT.  For two clubs we have two official
     Game Books in the same season (weeks 5 and 10). Comparing the eleven starting slots lets us say:
       - how many of the 22 starting slots changed;
       - for each change, whether the incoming player was already dressed for that club in the
         earlier game (i.e. a man already on the 46, the club's own next man up) or was a body that
         had not appeared at all (a deeper replacement, which is the situation the operator cares
         about);
       - how many of the changes line up with an official injury designation (Out / Doubtful /
         Questionable) in the Week 10 report, and how many do not.
     That last split is the whole point: a change WITH an official injury flag is explainable; a
     change WITHOUT one cannot be attributed to injury from an official source, and is left blank.

Every row keeps the exact URL it came from. Something a source does not print is never filled in.

Run: python3 signals/scripts/availability.py
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
OUT = R / "signals" / "data"
RAW = OUT / "raw"

W10_URL = "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf"
W5_URL = "https://static.www.nfl.com/image/upload/v1791805921/gamecenter/aa94b906-4feb-11f1-abca-2c54536568a9.pdf"
W10_GAME = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"
W5_GAME = "https://www.nfl.com/games/giants-at-commanders-2026-reg-5"
INJ = "https://www.nfl.com/injuries/league/2026/reg10"
DEPTH_404 = "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart"
ROSTER = "https://www.nfl.com/teams/kansas-city-chiefs/roster"


def parse(path):
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if parts[0] == "meta":
            continue
        if parts[0] in ("side",):
            _, side, unit, slot, jersey, name = parts
            rows.append({"kind": "starter", "side": side, "unit": unit, "slot": slot,
                         "jersey": jersey, "name": name})
        elif parts[0] == "sub":
            _, side, pos, jersey, name = parts
            rows.append({"kind": "sub", "side": side, "pos": pos, "jersey": jersey, "name": name})
        elif parts[0] == "dnp":
            _, side, pos, jersey, name = parts
            rows.append({"kind": "dnp", "side": side, "pos": pos, "jersey": jersey, "name": name})
        elif parts[0] == "ina":
            _, side, pos, jersey, name = parts
            rows.append({"kind": "inactive", "side": side, "pos": pos, "jersey": jersey, "name": name})
    return rows


def parse_injuries(path):
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("obs") or line.startswith("WAS|John") is None:
            if not line or line.startswith("#") or line.startswith("obs"):
                continue
        parts = line.split("|")
        if len(parts) != 6 or parts[0] not in ("WAS", "NYG"):
            continue
        team, player, pos, injury, practice, status = parts
        out[(team, player)] = {"position": pos, "injury": injury or None,
                               "practice": practice or None, "game_status": status or None}
    return out


SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def name_key_full(full):
    """'Lucas Patrick' -> ('l', 'patrick'); 'J.J. McCarthy' -> ('j.j', 'mccarthy')."""
    toks = [t for t in full.replace(".", ". ").split() if t]
    toks = [t for t in toks if t.lower().strip(".") not in SUFFIXES]
    if not toks:
        return (None, None)
    last = toks[-1].lower().strip(".")
    first = toks[0].lower().strip(".")
    return (first, last)


def name_key_abbrev(abbrev):
    """'L.Patrick' -> ('l', 'patrick'); 'A.J.Brown' would be ('a.j', 'brown')."""
    if "." not in abbrev:
        return (None, abbrev.lower())
    head, _, last = abbrev.rpartition(".")
    return (head.lower().replace(".", ""), last.lower())


def match_injury(inj, side, abbrev):
    """
    Join a Game Book abbreviation to an injury-report full name. Conservative:
    a unique last name matches outright; otherwise the first initial must also agree.
    Returns (row_or_None, how, note). Ambiguity returns None rather than a guess.
    """
    first, last = name_key_abbrev(abbrev)
    cands = [(k, v) for k, v in inj.items() if k[0] == side and name_key_full(k[1])[1] == last]
    if not cands:
        return None, "no match", "no injury-report row for this surname"
    if len(cands) == 1:
        return cands[0][1], "unique surname", ""
    initial = first.replace(".", "")[:1]
    narrowed = [(k, v) for k, v in cands if (name_key_full(k[1])[0] or "")[:1] == initial]
    if len(narrowed) == 1:
        return narrowed[0][1], "surname + first initial", ""
    return None, "ambiguous", ("%d injury rows share this surname and the initial does not single one "
                               "out; left unmatched" % len(cands))


def starters(rows, side, unit):
    return [r for r in rows if r["kind"] == "starter" and r["side"] == side and r["unit"] == unit]


def roster_of(rows, side):
    """Every player the PDF lists for that club, in any capacity."""
    return {r["name"]: r for r in rows if r["side"] == side}


def main():
    w10 = parse(RAW / "gamebook-w10-was-at-nyg-lineups.txt")
    w5 = parse(RAW / "gamebook-w5-nyg-at-was-lineups.txt")
    inj = parse_injuries(RAW / "injuries-w10-was-nyg-recheck.txt")

    # ------------------------------------------------------------------ 1. capability matrix
    capability = [
        {"capability": "Pregame depth chart with 1st/2nd/3rd string order",
         "url": DEPTH_404, "observed": "404 — '404 - Flag on the Play.'; no chart, no player, no status",
         "published": False, "answers_which_tier": None,
         "consequence": "A pregame '2nd-string' or '3rd-string' label cannot come from this route. "
                        "Any such label in this repository would be invented, so none is published."},
        {"capability": "Roster with a status code",
         "url": ROSTER, "observed": "Roster table: name, jersey, position, status column reads ACT, "
                                    "height, weight, experience, college. No depth order, no starter flag.",
         "published": True, "answers_which_tier": "none",
         "consequence": "ACT proves a player is on the active roster. It is silent on who starts."},
        {"capability": "Injury report — practice participation and game status",
         "url": INJ, "observed": "Player, Position, Injuries, Practice Status, Game Status for 28 clubs. "
                                 "Week 11 report was not observable: /reg11 returned the Week 10 page.",
         "published": True, "answers_which_tier": "availability flag only",
         "consequence": "Answers 'who is ruled out or limited'. Never answers 'who takes his place'."},
        {"capability": "Official Game Book — starting lineups by slot, substitutions, DNP, inactives",
         "url": W10_URL, "observed": "Both clubs' offensive and defensive starting slots with jersey "
                                     "numbers, the full substitution list, Did Not Play and Not Active.",
         "published": True, "answers_which_tier": "starter vs dressed vs not dressed",
         "consequence": "This is the ONLY official route that shows who actually started. It exists "
                        "after the game. It gives no ordinal depth, so 'depth of replacement' must be "
                        "measured as a change against a previous official listing, not read off a chart."},
        {"capability": "Game-day inactives as a pregame list",
         "url": "https://www.nfl.com/news/", "observed": "The NFL publishes an inactives article per "
                                                          "slate; it appears close to kickoff and is a "
                                                          "moving target. Not present for the Week 11 "
                                                          "slate at capture time.",
         "published": True, "answers_which_tier": "available vs not available, 90 minutes out",
         "consequence": "Useful for a live desk, not for a pre-week model. A snapshot is stale in hours."},
    ]

    # ------------------------------------------------------------------ 2. the depth measurement
    # METHOD NOTE, and a correction to this file's own first draft.
    # The obvious approach — line the two books up row by row and call any difference a change —
    # is WRONG. The two Game Books do not list the same positions in the same order: the Week 5
    # book lists the NYG offence as WR, LT, LG, C, RG, RT, TE, WR, QB, FB, RB while the Week 10 book
    # lists WR, TE, LT, LG, C, RG, RT, LB(see IR-1), WR, TE, QB, RB. Row-by-row matching turns a
    # reordering into a fake "replacement" and would have invented roughly twenty of them.
    #
    # So the comparison is restricted to slots that have an unambiguous identity: the five offensive
    # line positions and the quarterback, each of which appears exactly once per club per book, plus
    # the running back. These are the positions where continuity actually matters for the offensive
    # signal. Skill positions and defensive fronts are compared as SETS, with the caveat stated.
    SINGLE_SLOTS = ["LT", "LG", "C", "RG", "RT", "QB", "RB"]

    def by_slot(rows, side, unit):
        out = {}
        for r in rows:
            if r["kind"] != "starter" or r["side"] != side or r["unit"] != unit:
                continue
            out.setdefault(r["slot"], []).append(r)
        return out

    changes = []
    for side in ("WAS", "NYG"):
        for unit in ("offense", "defense"):
            g10 = by_slot(w10, side, unit)
            g5 = by_slot(w5, side, unit)
            for slot in SINGLE_SLOTS if unit == "offense" else []:
                a, b = g10.get(slot, []), g5.get(slot, [])
                if len(a) != 1 or len(b) != 1:
                    continue
                n10, n5 = a[0], b[0]
                if n10["name"] == n5["name"]:
                    continue
                dressed_w5 = roster_of(w5, side)
                dressed_w10 = roster_of(w10, side)
                came_from_w5_46 = n10["name"] in dressed_w5
                outgoing_row = dressed_w10.get(n5["name"])
                outgoing_status = (outgoing_row or {}).get("kind")
                inj_out, how_out, note_out = match_injury(inj, side, n5["name"])
                inj_in, how_in, note_in = match_injury(inj, side, n10["name"])
                flag_out = (inj_out or {}).get("game_status")
                flag_in = (inj_in or {}).get("game_status")
                explained = flag_out in ("Out", "Doubtful") or flag_in in ("Out", "Doubtful")
                changes.append({
                    "team": side, "unit": unit, "slot": slot,
                    "week10_starter": f"{n10['jersey']} {n10['name']}",
                    "week5_starter": f"{n5['jersey']} {n5['name']}",
                    "incoming_was_dressed_in_week5": came_from_w5_46,
                    "incoming_depth_class": (
                        "SAME 46 — the replacement was already on the club's game-day listing in "
                        "Week 5, i.e. next man up" if came_from_w5_46 else
                        "BELOW THE 46 — the replacement did not appear anywhere on the club's Week 5 "
                        "game-day listing, so he came from deeper on the roster"),
                    "outgoing_player_week10_status": (
                        f"listed as {outgoing_status} in the Week 10 game book" if outgoing_status
                        else "not listed anywhere in the Week 10 game book"),
                    "official_injury_flag_outgoing": flag_out,
                    "official_injury_flag_incoming": flag_in,
                    "official_injury_detail": (inj_out or {}).get("injury") or (inj_in or {}).get("injury"),
                    "injury_join_method": f"outgoing: {how_out}; incoming: {how_in}",
                    "injury_join_note": (note_out or "") + (note_in or ""),
                    "attributable_to_injury_from_official_source": explained,
                    "attribution_note": (
                        "Official game status Out or Doubtful, so the change is consistent with the "
                        "published report." if explained else
                        "No Out/Doubtful designation is published for either man. The change cannot be "
                        "attributed to injury from an official source; the cause stays blank."),
                    "source_url": W10_URL, "baseline_source_url": W5_URL,
                    "game_url": W10_GAME, "baseline_game_url": W5_GAME,
                })

    # set-level churn for the positions that cannot be matched one to one
    def names(rows, side, unit):
        return {r["name"] for r in rows
                if r["kind"] == "starter" and r["side"] == side and r["unit"] == unit}

    sets = []
    for side in ("WAS", "NYG"):
        for unit in ("offense", "defense"):
            n10, n5 = names(w10, side, unit), names(w5, side, unit)
            sets.append({
                "team": side, "unit": unit,
                "week10_starters_listed": len(n10), "week5_starters_listed": len(n5),
                "held_over": len(n10 & n5), "incoming": len(n10 - n5), "outgoing": len(n5 - n10),
                "incoming_names": sorted(n10 - n5), "outgoing_names": sorted(n5 - n10),
                "why_a_set": "Personnel grouping changes between games, so a starting 'slot' on defence "
                             "is not a stable identity. Set overlap is the only defensible comparison.",
                "source_url": W10_URL, "baseline_source_url": W5_URL,
            })

    # unexplained absences: started in Week 5, absent from the ENTIRE Week 10 game-day listing,
    # and carrying no Out / Doubtful official designation. These are the cases the operator's
    # requirement is really about, and the ones no official source explains.
    absences = []
    for side in ("WAS", "NYG"):
        book10 = roster_of(w10, side)
        for r in w5:
            if r["side"] != side or r["kind"] != "starter":
                continue
            if r["name"] in book10:
                continue
            inj_row, how, note = match_injury(inj, side, r["name"])
            flag = (inj_row or {}).get("game_status")
            absences.append({
                "team": side, "player_week5_starter": r["name"], "week5_slot": r["slot"],
                "present_in_week10_game_book": False,
                "official_injury_flag": flag,
                "official_injury": (inj_row or {}).get("injury"),
                "join_method": how,
                "explained_by_official_source": flag in ("Out", "Doubtful"),
                "classification": ("ABSENT — EXPLAINED by an official Out/Doubtful designation"
                                   if flag in ("Out", "Doubtful") else
                                   "ABSENT — UNEXPLAINED. He started in Week 5, does not appear anywhere "
                                   "in the Week 10 game-day listing, and carries no Out/Doubtful flag. "
                                   "The cause is not published, so it stays blank."),
                "source_url": W10_URL, "baseline_source_url": W5_URL,
            })

    # extractions that must be flagged rather than silently used
    irregularities = [{
        "id": "IR-1",
        "finding": "In the Week 10 Game Book, the New York Giants offence column prints "
                   "'LB 52 A.Reese' as its eighth row, while the same player also appears in the "
                   "defence column. A linebacker is not an offensive starter.",
        "evidence": "'| RT | 72 J.Eluemunor | LB | 52 A.Reese |' then '| LB | 52 A.Reese | CB | "
                    "20 G.Newsome |' in the retrieved table for the Week 10 PDF.",
        "impact": "The offence column may be missing one genuine starter, or the extraction may have "
                  "duplicated a defence cell across the column boundary. Either way, the NYG offence "
                  "listing has 12 rows where 11 are expected.",
        "disposition": "The ambiguous row is excluded from slot comparison and from the tier table. "
                       "The count is published as observed. Nothing is guessed to fill the gap.",
        "source_url": W10_URL,
    }, {
        "id": "IR-2",
        "finding": "The Week 5 Game Book lists the Washington Commanders' 2026 Week 5 starting "
                   "centre as 63 L.Patrick; the Week 10 injury report lists Lucas Patrick with a "
                   "concussion, Did Not Participate, Out.",
        "evidence": "Week 5 book: 'C 63 L.Patrick'. Week 10 report: "
                    "'WAS|Lucas Patrick|C|Concussion|Did Not Participate In Practice|Out'.",
        "impact": "This is the single cleanest example in the sample of a starter lost to a reported "
                  "injury, and it is the case the tier method should catch.",
        "disposition": "Recorded as an attributed change. 67 N.Allegretti started at centre in Week 10.",
        "source_url": INJ,
    }]

    # ------------------------------------------------------------------ 3. tier classification
    # Every player is placed in exactly one bucket, and each bucket names the field it came from.
    tiers = []
    for side, label in (("WAS", "Washington Commanders"), ("NYG", "New York Giants")):
        rows = [r for r in w10 if r["side"] == side]
        for r in rows:
            if r["kind"] == "starter":
                tier = "OFFICIAL_STARTER"
                basis = "printed in a starting slot on the Week 10 Game Book lineup"
            elif r["kind"] == "sub":
                tier = "OFFICIAL_DRESSED_NOT_STARTING"
                basis = "printed under Substitutions on the Week 10 Game Book"
            elif r["kind"] == "dnp":
                tier = "OFFICIAL_DRESSED_DID_NOT_PLAY"
                basis = "printed under Did Not Play on the Week 10 Game Book"
            elif r["kind"] == "inactive":
                tier = "OFFICIAL_INACTIVE"
                basis = "printed under Not Active on the Week 10 Game Book"
            else:
                tier = "UNCLASSIFIED"
                basis = ""
            inj_row = inj.get((side, r["name"]))
            tiers.append({
                "team": side, "team_name": label,
                "player": r["name"], "jersey": r["jersey"],
                "position": r["slot"] if r["kind"] == "starter" else r["pos"],
                "tier": tier, "tier_basis": basis,
                "official_injury_flag": (inj_row["game_status"] if inj_row and inj_row["game_status"] else None),
                "official_injury": (inj_row["injury"] if inj_row and inj_row["injury"] else None),
                "depth_ordinal": None,
                "depth_ordinal_reason": "No official source publishes an ordinal (2nd/3rd/4th string). "
                                        "Left blank deliberately; see the capability matrix.",
                "source_url": W10_URL,
            })

    # ------------------------------------------------------------------ 4. what a pregame version would need
    blocked = [{
        "question": "Which backups are behind which starters, before kickoff, for Week 11?",
        "status": "NOT KNOWABLE from any official source probed on 2026-11-14",
        "what_exists": "A post-game lineup (Game Book), a roster without order, and an injury report "
                       "without depth.",
        "what_would_make_it_knowable": "An official pregame depth chart (currently 404) or an official "
                                       "pregame starting-lineup announcement. Neither was observed.",
        "therefore": "Every Week 11 pregame tier cell is blank in this repository, and the reason is "
                     "recorded per row rather than filled with a guess.",
        "source_url": DEPTH_404,
    }, {
        "question": "Did a 2nd, 3rd or 4th string player replace a starter in Week 10?",
        "status": "PARTIALLY KNOWABLE, after the fact",
        "what_exists": "For WAS and NYG: yes, measured — see depth_changes below.",
        "what_would_make_it_knowable": "A Game Book per club per week. That exists for every completed "
                                       "game; it has simply not been transcribed for all of them.",
        "therefore": "The measurement method is proven on two clubs. Scaling it to 32 clubs is "
                     "mechanical work, not a new idea, and is the highest-value next task.",
        "source_url": W10_URL,
    }]

    attrib = [c for c in changes if c["attributable_to_injury_from_official_source"]]
    unexplained = [c for c in changes if not c["attributable_to_injury_from_official_source"]]
    deep = [c for c in changes if not c["incoming_was_dressed_in_week5"]]

    out = {
        "generated": "2026-11-14", "session": "8ef7f6bb",
        "title": "Availability tiers and depth of replacement — what official sources publish, measured",
        "how_to_read": {
            "tier": "OFFICIAL_* means the label was read off an official field. UNCLASSIFIED is never used.",
            "depth_ordinal": "Always blank. No official source publishes 1st/2nd/3rd string, so the "
                             "ordinal is not available and is not invented.",
            "depth_of_replacement": "Measured as a change against a second official listing for the "
                                    "same club, and classified SAME 46 vs BELOW THE 46.",
            "attribution": "A change is attributed to injury only where the official report carries "
                           "Out or Doubtful. Anything else stays blank.",
        },
        "capability_matrix": capability,
        "depth_changes": changes,
        "starter_set_churn": sets,
        "unexplained_absences": absences,
        "irregularities": irregularities,
        "tiers": tiers,
        "pregame_gaps": blocked,
        "summary": {
            "clubs_measured": 2,
            "weeks_compared": [5, 10],
            "method_correction_included": "row-by-row matching was rejected as unsound; see the "
                                          "METHOD NOTE in scripts/availability.py and IR-1",
            "single_identity_slots_compared": 7,
            "slots_changed": len(changes),
            "changes_with_official_out_or_doubtful_flag": len(attrib),
            "changes_with_no_official_explanation": len(unexplained),
            "changes_where_incoming_was_below_the_week5_46": len(deep),
            "unexplained_absences": len([a for a in absences if not a["explained_by_official_source"]]),
            "what_this_proves": (
                "Depth of replacement IS measurable from official sources, but only retrospectively and "
                "only at the cost of transcribing a Game Book per club per week. It is NOT knowable "
                "before kickoff. That distinction is the answer to the requirement, and it is the "
                "same answer the repository gave before — now with a working method and two clubs of "
                "evidence behind it instead of an assertion."),
        },
        "next_task_to_scale": {
            "task": "Transcribe the Week 11 Game Books for all 32 clubs and run this comparison against "
                    "Week 10, producing a full depth-change table.",
            "cost": "One PDF retrieval and ~60 transcribed lines per game, 16 games.",
            "why_it_matters": "It would let the model test whether a below-the-46 replacement predicts "
                              "a worse outcome than a same-46 replacement. That is a testable signal, "
                              "which is more than any current strategy has.",
            "blocking": "Nothing. It is available now and was not done here only because it is a "
                        "separate, large transcription task.",
        },
        "caveats": [
            "Two clubs, two weeks. Nothing here generalises to the league on this sample.",
            "A slot change can be caused by scheme, formation, or a coaching decision. The injury "
            "attribution is therefore one-directional: Out/Doubtful explains a change, but no flag "
            "does not prove there was no injury.",
            "The Week 5 baseline is the prior meeting; a club's 46 changes across a season for "
            "reasons unrelated to injury, so BELOW THE 46 is a lower bound on depth, not a precise rank.",
            "No Week 11 injury report was observable (probe P4), so no Week 11 pregame row exists.",
        ],
    }
    (OUT / "availability-tiers.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT / "availability-tiers.json")
    print("tiers:", len(tiers), "slot changes:", len(changes), "attributable:", len(attrib),
          "below-46:", len(deep))
    for c in changes:
        print(f"  {c['team']} {c['slot']:3s} {c['week5_starter']:22s} -> {c['week10_starter']:22s} "
              f"flag={c['official_injury_flag_outgoing']} "
              f"{'SAME46' if c['incoming_was_dressed_in_week5'] else 'BELOW46'}")
    for a in absences:
        print(f"  absent {a['team']} {a['player_week5_starter']:20s} flag={a['official_injury_flag']} "
              f"{'explained' if a['explained_by_official_source'] else 'UNEXPLAINED'}")
    for x in sets:
        print(f"  set {x['team']} {x['unit']:7s} held={x['held_over']} in={x['incoming']} out={x['outgoing']}")


if __name__ == "__main__":
    main()
