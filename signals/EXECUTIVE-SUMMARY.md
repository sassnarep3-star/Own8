# Executive summary — Own8 signal desk, 2026-11-14

**Session:** 8ef7f6bb · **Scope:** `signals/**` · **Evidence base:** 104 walk-forward games (weeks 3–9 of
the 2026 season), 136 official final scores, 240 official Next Gen Stats quarterback rows, two official
NFL Game Books, and twelve failure-mode probes of official NFL pages.
**Site:** [signals/index.html](index.html)

---

## The one-paragraph version

This project has spent ten sessions building dashboards because the input it actually needs does not
exist in any official NFL source: **a price.** Without a price, a hit rate cannot become a return, a
rank cannot become a stake, and a model line cannot be compared with a market line. This session
stopped building and did four things instead. It measured every strategy against eight do-nothing
rules on identical games, so "skill" now means skill over a coin rather than skill over a hand-picked
benchmark. It computed the number that would make each signal worth exactly zero, so the price hurdle
is now an explicit target instead of a missing column. It rebuilt the correlation register, reproduced six of nine published
coefficients exactly, and put the game-level sample size beside the row count. And it proved, on two
clubs, that the depth of a replacement **is** measurable from the official Game Book — after the game
and never before kickoff. The headline result is uncomfortable and is published anyway: **two arms
clear the break-even rate at an assumed -110, one of them a naive five-game recency rule, and neither
is promotable.**

---

## 1. What is now established

| # | Finding | Number | Status |
|---|---|---|---|
| 1 | The best admissible spread rule beats the league-mean baseline | 9.40 vs 10.16 points MAE on 104 games | **ESTABLISHED** |
| 2 | Using future games (deliberate leakage) buys only a little | 8.02 MAE, 1.38 points better | **ESTABLISHED, EXCLUDED** |
| 3 | Break-even at an assumed -110 | 52.381% hit rate | **ARITHMETIC** |
| 4 | Arms whose interval lower bound clears break-even | 2 of 18 (B11 53.47%, S8 52.49%) | **ESTABLISHED, NOT PROMOTED** |
| 5 | Correlations that reproduce exactly | C1, C2, C5, C6, C7, C8 | **ESTABLISHED** |
| 6 | Correlations whose p-values are optimistic | C5–C8 report n = 204 team-games inside 105 games | **CAVEAT** |
| 7 | Correlations that survive a Holm correction | C5, C6 — and both are tautological | **ESTABLISHED, UNUSABLE** |
| 8 | Replacement depth is measurable from the Game Book | 3 slot changes, 1 explained, 6 unexplained absences | **METHOD PROVEN, n=2 CLUBS** |

## 2. What is not established, and why

- **No edge exists in any form.** No arm's interval clears break-even by a margin that survives the
  fact that 19 arms were tested. The largest clearing margin is 1.09 points on a naive rule.
- **No market comparison exists.** No official NFL page publishes a spread, total or price. Every
  "market" column in the repository is blank, and the blank is deliberate.
- **No out-of-sample result exists for the current slate.** 13 Week 11 fair lines were originated on
  2026-11-14 and the games were unplayed at capture. Week 10 cannot be graded either: 13 of its 14
  games were unplayed at capture time.
- **The prop work is not a betting product.** Both prop strategies score worse than the naive
  baseline (−0.17% and −0.57% skill) and neither has a line to bet against.
- **Two clubs do not make a depth model.** The availability finding is a demonstration of method.

## 3. The five requirements in the brief, answered directly

**"Originate my own NFL lines."** Done, and the limits are stated. 13 Week 11 lines with fair spread,
fair total, fair moneyline, and the break-even distance for each. No market number exists to compare
them to, so they are labelled unvalidated and no edge is claimed.

**"Generate useful signals; treat it as a leaderboard competition with rewards."** The leaderboard now
scores every arm on identical games against eight do-nothing rules. Rewards are not awarded, because
awarding a rank on 104 games rewards noise. The measured answer is that a five-game recency rule beats
a coin flip at p = 0.005 on the moneyline, and no registered strategy does meaningfully better.

**"Each strategy must pass validation gates. Determine correlation values. Remove luck."** Gates are
frozen in code. Correlations are recomputed and six of nine reproduce exactly; every value now carries
the game-level n beside the published row count. **Luck is not
removable and this repository will not pretend otherwise** — what it now does is *measure* luck: every
arm carries its interval, its exact one-sided p-value, and the number of bets needed to confirm its own
observed edge. For the best arm that number is about 580 graded bets. The repository has zero.

**"Track injuries and know deficiencies such as 2nd/3rd/4th string backups replacing starters."**
Half answerable, and now measured rather than asserted. The official depth-chart URL returns **404**,
so no pregame string ordinal exists and none is published. The official **Game Book** does name
starters by slot after the game, and comparing two of them for the same clubs shows the method works:
one change fully explained by an official Out designation (Lucas Patrick, concussion), two changes and
six absences with no published cause.

**"A clear list of questions, information and answers before any decision."** The decision queue ranks
13 questions by what blocks a decision, with the action that closes each one. Seven need no new data.
Four block everything, and one of those — a price — blocks the other three.

## 4. The decision the operator actually faces

There are only two live options, and the repository has been oscillating between them for ten sessions.

1. **Get a price.** One timestamped feed, named venue, opening and closing numbers. This unblocks every
   price column, the staking half of the leaderboard, closing-line value, and any real promotion
   decision. It is the only route to the project's stated goal.
2. **Do not get a price,** in which case the honest ceiling for this project is a published, audited,
   free research desk: line origination with a stated error, a baseline ladder, a correlation register,
   and a depth-of-replacement study. That is genuinely worth having, and it is roughly what exists now.

What is not a live option is continuing to add dashboards. There are eleven.

## 5. If exactly one thing is done this week

**Print the required sample beside every rank** (suggestion SG-02). It costs nothing, needs no new data,
and it converts the leaderboard from a ranking of noise into an honest instrument. The arithmetic
already exists in `signals/data/baseline-ladder.json`.

If exactly two things: add the price feed (SG-01), because everything else on the list is downstream of
it.

## 6. Corrections made to this session's own work

Published deliberately, because a corrected error is evidence about the noise that remains elsewhere:

- **False negative, corrected.** The first draft claimed no arm clears the break-even rate. Two do.
  The claim is now computed from the data file at build time, and the checker fails if the two diverge.
- **Broken method, replaced.** The first draft measured replacement depth by matching two Game Books row
  by row. The books order positions differently, so that approach invented about twenty replacements.
- **Wrong formula, replaced.** The first draft computed the break-even cushion from win probability
  instead of cover probability, and inverted a favourite's spread sign.
- **False accusation, withdrawn.** The first draft declared four published correlations "illegitimate
  as published" and implied their n was a mistake. It had ignored the originator's documented
  single-passer sample rule and quietly mixed in a week-9 capture that post-dated the register. All
  four coefficients reproduce exactly to six decimals on the correct sample. The verdict was withdrawn
  and the only surviving finding is the milder one: the 204 rows sit inside 105 games, so the
  p-values are optimistic.

All three are on the [Flagged for review](flagged.html) page with their evidence.
