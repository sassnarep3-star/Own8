# Decision ledger (session 6652101e)

A namespace that holds the price-snapshot store, the verified results feed, the fair / market / difference
lines, the demotion gate, the signal-versus-staking leaderboard, and the suggestions you choose from.

Start at [ledger/index.html](index.html). Every table row links to an official nfl.com or nextgenstats.nfl.com
page, or to a NIST handbook page for a statistical rule. A value without an official source is left blank and flagged.

## Files

| Path | What it is |
| --- | --- |
| `data/results-feed.json` | 149 final scores: 136 from the verified W1-W9 log, the Week 10 Thursday final, and 12 Sunday finals added in a separately timestamped source addendum; the unresolved LAC at BAL result is excluded. |
| `data/week10-results-addendum.json` | 12 Week 10 finals independently checked against official scores and game centers, one unresolved game left blank, a UTC capture timestamp, and an explicit raw-body/hash limitation. |
| `data/price-snapshots.json` | 39 originated markets (13 games x side, total, moneyline, in that order). Each carries the verified locked FanDuel line from the nfl.com picks article (`official_locked_*`). Opening and closing values are null — no official page publishes them. |
| `data/price-probe.json` | The official page probe that found no line on the game-centre page, with its scope. The picks article (the verified price source) was found later; see flag LF-01 and finding F-01. |
| `data/lines-columns.json` | 13 Week 10 games: fair, market and difference as separate columns. |
| `data/strategy-registry.json` | 14 strategies with the gates each product must pass, and status. |
| `data/demotion-rules.json` | Pre-registered demotion rules D1-D8 and re-promotion rule P1. |
| `data/suggestions.json` | Suggestions SG-L1..SG-L7 with options. None is implemented. |
| `data/flags.json` | Irregularities and unverified items, each with source links. |
| `results/leaderboard-split.json` | Signal block and staking block per strategy; rank uses the signal block only. |
| `results/demotion-decisions.json` | Output of the demotion gate for the current registry. |
| `scripts/build_ledger.py` | Builds all of the above from the read-only inputs in `origination/`. |
| `scripts/demotion_gate.py` | The demotion evaluator. |
| `scripts/test_ledger.py` | 24 unit tests. Demotion fixtures are synthetic and labelled as such. |
| `scripts/check_ledger.py` | Verifies row counts, official links, internal links and that no unverified value exists. |

## Reproduce

Run from the repository root. Standard library only.

```sh
python3 ledger/scripts/build_ledger.py
python3 ledger/scripts/demotion_gate.py
python3 -m unittest discover -s ledger/scripts -p 'test_ledger.py' -v
python3 ledger/scripts/check_ledger.py
```

## Inputs (read only)

`origination/data/games-2026-w1-w9.json`, `origination/results/w10-lines.json`,
`origination/results/validation-w10.json`, `origination/results/leaderboard-w10.json`,
`market/data/raw/official-prices-w10.json` (the verified locked FanDuel lines from the
nfl.com Week 10 picks article, captured by session 949f49b0), and
`ledger/data/week10-results-addendum.json` (the separately dated 2026-11-17 official score
audit). The 136-game forecast corpus and the original Week 10 model artifact remain unchanged;
no files in `origination/` or `market/` were edited.

## What this namespace does not do

It does not place or settle bets, calculate ROI, or issue rewards. The Week 10 companion page reports only point-error diagnostics on 12 official finals; it is not a strategy score, validation gate, or leaderboard result. No real money or stakes are involved.
