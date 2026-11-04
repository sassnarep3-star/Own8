# Own8 · NFL Research Lab

**Live dashboard:** https://sassnarep3-star.github.io/Own8/

An evidence-first workspace for originating NFL lines and evaluating singles, parlays and player-prop combinations. **Research only: no validated betting edge, eligible strategy, placed wager, settled leaderboard or cash reward is claimed. Luck cannot be eliminated.**

## Executive assessment · 2026-11-04

- Independently retrieved selected official fields: **32** standings rows (W/L/T/PCT/PF/PA/NET), **15** Week 9 matchup/date pairs and **27** rendered Week 8 NGS passing rows (name/team/ATT/YDS/CPOE). Not full-season player totals or a live feed.
- **15 experimental baseline lines**, clearly labeled project calculations. Untrained shrinkage model, zero assumed home advantage; Madrid is neutral. No calibrated probability, direct operator quote, EV or recommendation.
- Three descriptive cross-team correlations, **not** bet-leg correlations or skill evidence. Actual parlay/prop-combo correlations remain blank.
- **Eight blocked strategy hypotheses** and **eleven strict gates**. CONDITIONAL/missing is not PASS. The leaderboard has no ranks, ROI, scores or rewards until qualified, settled evidence exists.
- All **104 baseline files / 7,901 text lines** inventoried by hash/line count; **502 legacy structured rows** enumerated. This is mechanical review coverage, **not a claim of independently verifying every historical sentence**. Unsupported legacy numeric values are withheld from published tables.
- Fourteen material audit findings plus 34 concurrent review-register entries and prior F-01–F-13 IDs are published on **Flagged for Review**. Review flags do not block site publication; missing evidence blocks strategy eligibility.

## Official references and scope

- [NFL standings](https://www.nfl.com/standings/) — selected 32-team numeric fields checked 2026-11-04.
- [NFL Week 9 schedule](https://www.nfl.com/schedules/2026/by-week/week-9) — matchups/dates and Madrid label checked; kickoff time zone and venue withheld.
- [NFL Next Gen Stats Week 8 passing](https://nextgenstats.nfl.com/stats/passing/2026/REG/8) — selected fields of 27 rendered rows checked.
- [NGS glossary](https://nextgenstats.nfl.com/glossary) — feature definitions, not endorsement of proposed signals.
- [NIST on association](https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm) — association does not prove causation.
- [Washington regulator requirements](https://www.wsgc.wa.gov/tribal-partnerships/sports-wagering/sports-wagering-requirements-and-rules) — jurisdiction context, not personalized legal advice.

See `data/verified/sources.json` for exact checked scope and retrieval dates. `data/evidence/` contains selected-field **transcriptions, not raw original HTML**. A linked URL or matching captures alone is not verification.

## Reproduce without manual input (Python standard library only)

```sh
python3 -m unittest discover -s tests -v
python3 scripts/audit.py
python3 scripts/analyze.py
python3 scripts/verify_snapshot.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 -m http.server 8000 --bind 0.0.0.0 --directory _site
```

The fixed-input pipeline is automated. It does **not** implement continuous official-data collection, quote refresh, real-time injury monitoring, a trained multi-season backtest, a live settled forecast ledger or full sportsbook-specific parlay settlement. Those gaps are explicit; no user credentials, purchase or manual entry is requested. The source snapshot remains dated instead of being silently relabeled current.

The integrated PR #19 snapshot, math helpers and 18 inherited regression tests are retained alongside this session’s 12 tests. All 30 test methods must pass. The current site does not promote every inherited observation as independently rechecked by this session.

## Repository layout

- `data/verified/` — independently checked selected fields; the only current analysis inputs.
- `data/evidence/` — transcribed source excerpts. `data/review-findings.json` — current review findings.
- `analysis/` — reproducible dashboard outputs, checks, hashes and baseline audit inventory.
- `scripts/engine.py` + `tests/` — tested gate, probability, price, settlement and validation primitives.
- `research/methodology.md` — full research protocol, proposed signal designs, holdout/multiplicity controls, ranking/reward rules and limitations.
- `index.html`, `pages/`, `assets/`, `public-data/` — generated dashboard and reviewable downloads.
- `_site/` — ignored, isolated deploy artifact. No legacy HTML/raw unverified numeric datasets are included. `_config.yml` also excludes historical trees if legacy main/root publishing is used as fallback.
- `.github/workflows/pages.yml` — tests/build checks on branch/PR and one artifact deployment on main. The direct sandbox settings call was denied HTTP 403; the deploy job uses the scoped pages:write workflow token, integrating PR #19’s publishing approach.
- `archive/pre-audit-2026-11-04/` — superseded scripts, analysis and research, **not authoritative**. Other legacy `data/` files remain for provenance only. Do not feed them to the current pipeline.
- `COORDINATION.md` — task scope, verification limits and deployment record.

Every published table row includes an official-site review link. Project calculations and proposed policies are labeled as such; reference links do not imply official endorsement. Blank cells represent unavailable/unverified values, never invented zeroes. Link checks validate internal paths/fragments, HTTPS/allowlists and row references, **not universal external uptime or factual support**.

## Safety

Research only; no wagering, account integration, paid contest, cash/value prizes or profit guarantee. Proposed reward badges have no monetary value. See the [Washington State Gambling Commission](https://www.wsgc.wa.gov/tribal-partnerships/sports-wagering/sports-wagering-requirements-and-rules) and [official help/self-exclusion resources](https://www.wsgc.wa.gov/responsible-gaming-self-exclusion). Do not infer legal permission from approximate location.
