# Session 08643438 — 2026-11-15 official re-verification

Fresh, dated re-verification of the published numbers against the official pages, performed
during final integration round 5. Every check below cites the official URL it was read from
and the read timestamp. Nothing here is inferred: mismatches would have been blanked and
flagged, never corrected.

## Sources read (2026-11-15, ~23:25–23:40 UTC)

| Official page | What was read | Chunks |
| --- | --- | --- |
| https://www.nfl.com/scores/2026/week-10 | Week 10 state at read time: 9 finals, 3 live, 2 upcoming, 4 byes | 2 |
| https://www.nfl.com/standings/league/2026/REG | 32 league standings rows, core fields (W-L-T, PF, PA) | 2 |
| https://www.nfl.com/injuries/league/2026/reg10 | Week 10 injury report shape probe (F-07) + Lions designation check | 1 |

## Checks and results (`verification.json`)

1. **Standings reconciliation — PASS 160/160 cells.** W-L-T, PF and PA for all 32 clubs
   recomputed from the committed 137-game results feed (Weeks 1–9 verified log + Week 10
   Thursday) plus the eight Week 10 Sunday finals read live, match the standings as read.
   Method and per-team cells: `verification.json`. The one alias (standings print LA, the
   repo stores LAR) is applied inside the check only and recorded there (IR-c56-01).
2. **F-07 shape probe — the 185 practice-only rows are the real official report shape,
   not a capture artifact.** The live page lists players with a Practice Status and BOTH
   the Injuries and Game Status cells blank (e.g. WAS John Bates TE — Full Participation;
   NE Hunter Henry TE — Limited). The market F-07 caveat stands as worded: per-club row
   counts are rows on the report, not players with a disclosed injury.
3. **Lions designation request (VR-08/VR-12) — superseded by the official page itself.**
   As read 2026-11-15, Kerby Joseph (Knee), Cade Mays (Ankle) and D.J. Reed (Hip) all show
   Did Not Participate + **Out**. The earlier blank cells are consistent with the report
   being a daily, timestamped series; backtests must snapshot the report as it was known.
4. **Freshness finding.** Eight Week 10 Sunday games are FINAL on nfl.com but are not yet
   in the 137-game feed (NE 10 @ DET 35; KC 35 @ ATL 13; HOU 24 @ CLE 27; MIN 30 @ GB 10;
   MIA 22 @ IND 24; CAR 20 @ NO 17; BUF 31 @ NYJ 12; JAX 40 @ TEN 23). At read time three
   games were still live (LAR @ AZ, SEA @ LV, SF @ DAL) and two upcoming (PIT @ CIN SNF,
   LAC @ BAL MNF). The Week 10 line set may only be graded after all 14 games settle —
   grading now would be lookahead. Logged as V-03 on the root Flagged for Review page.

## Reproduce

```sh
python3 session-08643438/reconcile.py   # rewrites verification.json; exit 0 only on PASS
```

## Scope note

This session edits only its own namespace (`session-08643438/**`), the shared board, the
root publication surface, the ledger price-store take-over (SG-03/X3/F-01, handoff
recorded in COORDINATION.md) and the desk flagged-page regeneration (053940d1 handoff).
Canonical datasets owned by other namespaces (origination game log, requirements
captures) were NOT rewritten; the freshness gap is published as a flag for their owners.
