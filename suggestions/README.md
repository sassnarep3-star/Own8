# Suggestions & decision-readiness workspace (session aa2d8cbe)

A dedicated, reviewable workspace for **improvement suggestions** and the
**information needed before any decision**, plus an independent **re-review** of
the canonical workspace against live official sources. Scope is new directories
only (`suggestions/**`, `review/**`) plus a section of `COORDINATION.md`; no
other session's files are edited.

## What is here

- `suggestions/index.html` — landing page for the workspace.
- `suggestions/pages/suggestions.html` — prioritized improvement suggestions
  (SU-01..SU-10) with priority, rationale, scope, verification required, status
  and an official/methodology source. Status starts at `proposed` so a reviewer
  can choose the best path before implementing.
- `suggestions/pages/decision-questions.html` — decision-readiness register
  (DQ-01..DQ-08): the question, what we already have, what we lack, why it
  matters, a suggested discovery action, and the official source.
- `suggestions/pages/lineup-impact.html` — injury / backup-deficiency signal
  framework (LI-01..LI-06): what to track when 2nd/3rd/4th-string backups replace
  starters on offense and defense. Verified examples are transcribed from the
  official Week 9 injury report; the depth-chart "string" designation is left
  blank/unverified until an official roster/depth-chart source confirms it.
- `suggestions/pages/executive-summary.html` — executive summary of important
  details, every verified statement source-linked.
- `review/index.html`, `review/pages/repo-review.html` — independent line-by-line
  re-review (RV-01..RV-06) with source links and a files-reviewed table.

## Data and generation

Structured data lives in `suggestions/results/*.json` and
`review/results/review-findings.json`. Pages are generated, not hand-edited:

```sh
python3 suggestions/scripts/build_pages.py   # regenerate all HTML from JSON
python3 suggestions/scripts/check_links.py   # verify local + official-allowlist links
```

## Verification rule

Every data table row carries a link to an official source. If a value cannot be
confirmed from an official source it is left **blank** and flagged
`UNVERIFIED` — never inferred or filled in. Suggestions are project-design
proposals, not verified external facts; their linked source is the official
reference or methodology the proposal relies on.

## Live routes (after Pages deploy)

- https://sassnarep3-star.github.io/Own8/suggestions/
- https://sassnarep3-star.github.io/Own8/review/
