# Integration contract — competition module

Scope: no new `.github/` workflow, root navigation or Pages setting is created
here, preserving active parallel-session claims and the existing root Pages
source (`main`, `/`). Static files under `competition/` are directly publishable
by that configuration; no separate hosting workflow is necessary.

## Build/check hook for the integration owner

Run in a full-history checkout with Python 3.10+:

```sh
python3 -m unittest discover -s competition/tests -v
python3 competition/scripts/pipeline.py
python3 competition/scripts/build_site.py
python3 competition/scripts/check_site.py
```

All writes stay in `competition/`. No dependency install or credential is
necessary for these snapshot checks. No source fetch or strategy publication is
performed by a build. Navigation integration requested: add `competition/` to the
shared root navigation; link `competition/flagged.html` from the shared review
index. These requests are also logged in COORDINATION.md / PR #16.

## Prospective automation is explicitly NOT enabled

Do not install a schedule that silently reuses the November 4 snapshot. The
necessary production inputs/adapters are absent:

1. Source refresh with retained upstream responses and trustworthy individual
   price update / observation instants. Never promote a provider footer clock or
   browser load time to an inferred quote-update time.
2. Reviewed exact-market/jurisdiction rules and final participation evidence.
3. Externally preregistered strategy versions, frozen chronological folds,
   calibrated distributions and full trial-family accounting.
4. An independent registration/receipt adapter. `GithubReceipts` uses `gh` only
   when explicitly called by the publishing API; it is not run by this build.
5. Official event/score/player-stat refresh, resolved contract identity, reviewed
   closing quotes and idempotent grading/revision checks.
6. A report adapter that reconstructs production evidence by re-reading external
   receipts and official outcomes. The current snapshot report rejects a nonempty
   production prediction ledger rather than accept self-reported returns.
7. Trusted external ledger checkpoints; hash chains alone cannot detect a removed
   tail when an attacker can also replace the only stored checkpoint.

The publication API may require an integration-owned GitHub token with
issues-write permission; do not place a token in source, chat, the static site,
receipts, client JavaScript or generated data. Authentication is configured via
normal GitHub runtime mechanisms, never requested from the user here.

The remaining production handoff is a published review flag (C-F11). Engine
unit tests are synthetic capability tests, not real competition results. No
real-money bet executor is included or planned by this module.
