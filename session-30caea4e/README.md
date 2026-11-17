# Session 30caea4e — Week 10 official finals and standings reconciliation

Captured **2026-11-17 (UTC)** from nfl.com with the fetch tool. Scope: this directory and the COORDINATION.md section "Session 30caea4e". No other file was edited.

## What was checked

| Check | Result | Evidence |
| --- | --- | --- |
| Week 10 Sunday finals on the official scores page | **12 of 12 read as "Final"** (scores printed beside each game link) | [official-w10-finals.json](official-w10-finals.json), source [nfl.com/scores/2026/week-10](https://www.nfl.com/scores/2026/week-10) |
| Thursday game WAS 24 – NYG 21 already in the repo feed | **Equal to the official page** | `reconcile.json` → `thursday_already_in_feed_check` |
| Monday game LAC @ BAL (Nov 16) | **Not verified as final.** The Game Center page prints no score and the standings still show LAC 0-8 and BAL 4-5. Left out of every computed figure. | [nfl.com/games/chargers-at-ravens-2026-reg-10](https://www.nfl.com/games/chargers-at-ravens-2026-reg-10) |
| Repo feed (137 games) + 12 official finals = 149 games, recomputed W, L, T, PF, PA for all 32 clubs, compared with the official standings | **160 of 160 cells match, 0 mismatches** | [reconcile.py](reconcile.py) → [reconcile.json](reconcile.json), standings source [nfl.com/standings](https://www.nfl.com/standings/) |

Reproduce: `python3 session-30caea4e/reconcile.py` (standard library only; exit 0 on full match).

## The 12 official Week 10 Sunday finals (away team first, as printed)

| Date | Away | Score | Home | Score | Official game page |
| --- | --- | --- | --- | --- | --- |
| Nov 15 (Munich) | NE | 10 | DET | 35 | [link](https://www.nfl.com/games/patriots-at-lions-2026-reg-10) |
| Nov 15 | KC | 35 | ATL | 13 | [link](https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10) |
| Nov 15 | HOU | 24 | CLE | 27 | [link](https://www.nfl.com/games/texans-at-browns-2026-reg-10) |
| Nov 15 | MIN | 30 | GB | 10 | [link](https://www.nfl.com/games/vikings-at-packers-2026-reg-10) |
| Nov 15 | MIA | 22 | IND | 24 | [link](https://www.nfl.com/games/dolphins-at-colts-2026-reg-10) |
| Nov 15 | CAR | 20 | NO | 17 | [link](https://www.nfl.com/games/panthers-at-saints-2026-reg-10) |
| Nov 15 | BUF | 31 | NYJ | 12 | [link](https://www.nfl.com/games/bills-at-jets-2026-reg-10) |
| Nov 15 | JAX | 40 | TEN | 23 | [link](https://www.nfl.com/games/jaguars-at-titans-2026-reg-10) |
| Nov 15 | LA | 34 | AZ | 6 | [link](https://www.nfl.com/games/rams-at-cardinals-2026-reg-10) |
| Nov 15 | SEA | 21 | LV | 13 | [link](https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10) |
| Nov 15 | SF | 46 | DAL | 40 | [link](https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10) |
| Nov 15 (SNF) | PIT | 18 | CIN | 38 | [link](https://www.nfl.com/games/steelers-at-bengals-2026-reg-10) |

Thursday (already in the feed): WAS 24 – NYG 21, [link](https://www.nfl.com/games/commanders-at-giants-2026-reg-10).

## Irregularities and flags (for manual review)

1. **Stale results feed (V-03 still open, now larger).** `ledger/data/results-feed.json` has 137 games and only one Week 10 game. The 12 official Sunday finals above are not in it. Week 10 lines therefore still cannot be graded, and the freshness rule (do not grade until all 14 settle) still holds because LAC @ BAL is unverified.
2. **Monday game status unverified.** LAC @ BAL has no printed final on the official pages read. Needs a re-read after the game page is updated.
3. **Team-code mismatch.** The feed uses `LAR` for the Rams; the official standings use `LA`. Mapped in `reconcile.py` (`ALIAS`) and not changed in the feed.
4. **Reconciliation is not independent of nfl.com.** Both the scores page and the standings page come from nfl.com. The match shows the two official pages agree, not that either is correct.
5. **Cached-page risk.** Each page was read once at the time above. Re-read before any use.

## Not done in this session (honest scope)

- No change to the results feed, the ledger, the grading, the site or the root Flagged page. Those are other sessions' or the integration session's files (see request in COORDINATION.md).
- Injury report, depth charts, Game Books and snap counts were not re-captured here.
