# Independent integration QA — 2026-11-04

This is a **read-only audit** of PR [#6](https://github.com/sassnarep3-star/Own8/pull/6) at `d6e88e72bb233625891b9fea00fab32bf2969774`. It does **not** certify every NFL data cell. The live root site on main and the unmerged PR #6 are different products.

## Executive summary

- **Release gate: not cleared for PR #6 as written.** The user's requirement that *every table row* have an official-source link conflicts with most of PR #6's third-party-derived betting backtests. The NFL [official rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook/) is an official source for rules, **not** for historical betting odds. Keep results as labeled, exploratory, non-official research, or leave the unverified values blank in the official-only dashboard; do not describe the whole site as official-source verified.
- **Unverified source-link presence:** `python3 verification/check_pr6.py` counted **276 rendered table rows**, **246 without an official NFL link in the row** (includes explanatory/metadata tables; thus this is a strict literal application of the user's every-row requirement, not 246 independently disproven facts). [Detailed per-page output](pr6-row-sources.json). All **21/21** rows on `site/official-facts.html` contain official NFL links, but a link alone does not verify the text.
- **No luck-free guarantee:** PR #6 calls S2 a “genuine, luck-free skill signal” on its home page. CLV +0.801 and z=5.68 are *derived* from [LeeSharpe's third-party games](https://github.com/LeeSharpe/nfldata/blob/master/data/games.csv) and [mrcaseb's third-party odds](https://github.com/mrcaseb/nfl-data/blob/master/data/nfl_lines_odds.csv.gz), not an official market record. Statistical tests reduce sensitivity to sampling luck; they cannot remove chance, selection effects, data errors, or guarantee profitability. Label this an **exploratory historical signal** pending independent source and prospective validation.
- **Stale live injury claim:** the baseline site's assertion that Week 9 reports are unavailable is contradicted by the NFL's published [2026 Week 9 injury report](https://www.nfl.com/injuries/league/2026/reg9), checked 2026-11-04. The official page lists JAX and BAL player practice statuses and explicitly displays blank game statuses in this snapshot. The previous [audit](../audit/index.html) has already flagged this. Do not infer game availability from blank cells. PR #8 independently addresses invalid candidates and unverified market values but its description still calls the W9 report unpublished.
- **Branch coordination:** PRs [#6](https://github.com/sassnarep3-star/Own8/pull/6) and [#8](https://github.com/sassnarep3-star/Own8/pull/8) both touch the root site and coordination files. PR #6 reported `CONFLICTING` with main during this check. Integrate their changes without silently overwriting #8's withdrawn candidates. Do not merge a conflicted or broken site.

## Reproduce and scope

```bash
git fetch origin arena/28cc78aa-own8
python3 verification/check_pr6.py > /tmp/pr6-rows.json
```

The checker reads *git objects*, does not modify other owners' files, and tests only whether the link host inside a rendered table row is `nfl.com`, a subdomain of `nfl.com`, or the NFL-owned GitHub organization `nfl-football-ops`. It does **not** fetch external URLs, prove link availability, independently verify calculations, or classify official sources outside NFL domains (e.g. official government agencies). Local methodology links and third-party mirrors are correctly counted as *not* official NFL citations. Re-run after each integration change; counts may change.

## Independent official-source checks performed

| Checked item | Source | Finding |
| --- | --- | --- |
| 2026 kickoff changes | [NFL Football Operations rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook/) | Official page explicitly lists Rule 6-1-3, 6-1-5, 6-1-6; consistent with PR #6 fact F20. |
| Week 9 injury report exists | [NFL 2026 Week 9 injuries](https://www.nfl.com/injuries/league/2026/reg9) | NFL page exists and lists JAX/BAL players. Contradicts baseline F-04/current PR #8 description; not a game-status verification. |
| Official rules PDF provenance | [NFL 2026 rules PDF](https://media.nfl.com/content/dam/communications/Official%20Playing%20Rules/2026%20Official%20Playing%20Rules.pdf) | Fetched first chunk (cover and 2026 change list); **other 20 fact quotations not independently checked**. |

The row-count audit is a static code/HTML check, *not* independent game-by-game validation of historical third-party odds, player props, or strategy ROI. Those remain **unverified against an official source**. Do not treat a comparison between two non-NFL mirrors as official verification.
