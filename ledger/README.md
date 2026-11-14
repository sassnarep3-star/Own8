# Decision ledger (session 6652101e)

A namespace that holds the price-snapshot store, the verified results feed, the fair / market / difference
lines, the demotion gate, the signal-versus-staking leaderboard, and the suggestions you choose from.

Start at [ledger/index.html](index.html). Every table row links to an official nfl.com or nextgenstats.nfl.com
page, or to a NIST handbook page for a statistical rule. A value without an official source is left blank and flagged.

## Files

| Path | What it is |
| --- | --- |
| `data/results-feed.json` | 137 official final scores (136 from the verified W1-W9 log, plus the Thursday W10 game). |
| `data/price-snapshots.json` | 39 originated markets (13 games x side, total, moneyline, in that order). Opening and closing values are null. |
| `data/price-probe.json` | The official page probe that found no betting line, with its scope. |
| `data/lines-columns.json` | 13 Week 10 games: fair, market and difference as separate columns. |
| `data/strategy-registry.json` | 14 strategies with the gates each product must pass, and status. |
| `data/demotion-rules.json` | Pre-registered demotion rules D1-D8 and re-promotion rule P1. |
| `data/suggestions.json` | Suggestions SG-L1..SG-L7 with options. None is implemented. |
| `data/flags.json` | Irregularities and unverified items, each with source links. |
| `results/leaderboard-split.json` | Signal block and staking block per strategy; rank uses the signal block only. |
| `results/demotion-decisions.json` | Output of the demotion gate for the current registry. |
| `scripts/build_ledger.py` | Builds all of the above from the read-only inputs in `origination/`. |
| `scripts/demotion_gate.py` | The demotion evaluator. |
| `scripts/test_ledger.py` | 23 unit tests. Demotion fixtures are synthetic and labelled as such. |
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
`origination/results/validation-w10.json`, `origination/results/leaderboard-w10.json`. Nothing in `origination/` is edited.

## What this namespace does not do

It does not record any betting line, compute any ROI, or place or grade any bet. No real money, stakes or rewards are involved.
