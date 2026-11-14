# Own8 decision-review subsite

A standalone, source-linked dashboard for the open decision questions, missing information, suggested discovery work, lineup/injury requirements, and unresolved irregularities in Own8. It is intended to be linked from the canonical dashboard and published under `/Own8/decision-review/` using the repository's existing root GitHub Pages source.

## Rebuild and check

From the repository root:

```sh
python3 decision-review/build.py
python3 decision-review/check.py
```

The builder uses Python's standard library only. The checker validates source IDs, official HTTPS host allowlists, required source links on every data row, missing-value handling, local links/anchors, and static table rows. It does not make external HTTP requests; source retrievals are recorded in `data/sources.json` and were bounded page extractions, not retained raw HTTP.

## Evidence rules

- `data/questions.json`, `data/suggestions.json`, `data/availability.json`, and `data/flags.json` are structured project content; they are not official NFL publications.
- A link to an official source is context or a verification target unless the exact field and retrieval scope are described as checked. Project implementation state is cross-checked against the named repository files.
- Unknown player, role, injury, market, and performance values remain `null` or blank. No starter, 2nd-, 3rd-, or 4th-string player is named or inferred.
- The role-tier labels are an Own8 schema proposal, not a claim that the NFL uses those exact labels.
- Recommendations are proposed decisions, not approved implementation or official NFL/NIST/GRA rules.
- The current NFL Week 11 injury-page request returned Week 10 content in this bounded retrieval. This is shown as an irregularity; no current-week injury claim is made.
- The module contains no sportsbook credentials, private feed, real-money wagering, payout, or live betting recommendation.

## Current release boundary

The module recommends research-only / fail-closed work now, with a paper-only shadow competition as a future gated option. Real-money wagering or rewards of value are held for a separate product-specific legal and regulatory review. This is not legal advice or a project-specific legal classification.
