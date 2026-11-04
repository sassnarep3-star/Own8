# Own8 — verification and fail-closed evidence layer

**Historical research only. No actionable picks, proven skill, current odds feed or real-money wagering.**

Dashboard: https://sassnarep3-star.github.io/Own8/docs/evidence-lab/

## Reproduce without prompts or external dependencies

From repository root:

```sh
python3 evidence-lab/analyze.py
python3 evidence-lab/build.py
python3 evidence-lab/check.py
python3 evidence-lab/publish.py
```

Or test just the engine:

```sh
python3 -m unittest discover -s verification -p 'test_*.py' -v
```

The published mirror at `docs/evidence-lab/` is included by the shared Pages artifact staging of `docs/`; it does not edit shared navigation or workflow files. Run commands from the source directory named above, not the public mirror.

The build is offline and reads the captured official NFL sample. To intentionally refresh that immutable source capture via the permitted GitHub API:

```sh
python3 evidence-lab/capture.py
```

`capture.py` uses the already configured `gh` authentication. No secrets are stored. It captures three small official publisher files at a pinned commit; it is not a live NFL/sportsbook updater.

## Evidence

The official [NFL Big Data Bowl games file](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) supplies 91 games. The [official schema](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md) identifies 2017 Weeks 1–6. The [publisher README](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/README.md) identifies the repository as the NFL Big Data Bowl data homepage. See `evidence/manifest.json` for hashes and retrieval time.

**Verified** here means displayed historical fact fields exactly match the immutable official file capture. It does not mean independent gamebook corroboration. Derived forecasts and correlations are labeled; unknown market/prop/performance values remain null/blank. Policy thresholds are project assumptions, not official NFL requirements.

## Contents

- `index.html`, `evidence.html`, `lines.html`, `strategies.html`, `correlations.html`, `gates.html`, `flagged.html`, `sources.html`: static dashboard.
- `engine.py`: tested betting math, push settlement, dependence primitives, strict gates and chronological point forecasts.
- `capture.py`: explicit immutable official source retrieval.
- `analyze.py` → `results.json`: official evidence ledger and exploratory analysis.
- `build.py`: generate the eight HTML pages.
- `check.py` → `checks.json`, `repo-review.json`: regression, hash, per-row fact, gate, reproduction and read-only repository link checks.
- `EXECUTIVE_SUMMARY.md`, `METHODOLOGY.md`: conclusions, scope, strategy and validation policy.

## Parallel scope and integration

Session 34f42e88 owns only `evidence-lab/**` plus its own coordination log section. Root and historical dashboard owners were notified on PRs #6/#8; their files are not overwritten. Their claims are not certified by this package. Historical findings are revision-bound in `repo-review.json`; fixes in other PRs require a new check.

The check scans all tracked repository text for inventory and a narrow set of known risky code/copy patterns. That scan is **not** semantic line-by-line external verification of all existing facts. Direct NFL website retrieval was not available in this environment. Broader official re-verification remains flagged.

No luck-free strategy is claimed. No missing official data is fabricated. See [Flagged for Review](flagged.html) before interpreting any model output.
