# Strategy research registry

All eight designs are BLOCKED, not profitable recommendations. Full descriptions and gate objects: `analysis/strategies.json`.

1. S1: Single spread — scoring benchmark, then test opponent adjustment and shrinkage in rolling folds.
2. S2: Single total — lagged pace, drive efficiency and red-zone residuals.
3. S3: Single moneyline — discrete margin distribution and calibrated win/tie probabilities, not a mean-only transformation.
4. S4: QB prop — lagged CPOE/intended air yards plus dropback volume and active status.
5. S5: Receiver prop — target share, routes and air-yards share; not inferred from receiving yards alone.
6. S6: RB prop — carries, snaps, box count, role changes and script uncertainty.
7. S7: Cross-game parlay — calibrated joint outcomes, offered combo price and common-shock stress test; no assumed independence.
8. S8: QB/receiver same-game combo — joint attempts/completions/target allocation and calibrated threshold events; no team-correlation proxy.

Metric definitions checked: https://nextgenstats.nfl.com/glossary . Observations: https://www.nfl.com/standings/ and https://www.nfl.com/scores/ . These references do not recommend or validate the designs. Opportunity, pace, routes, market prices, paired outcomes and historical forecasts are not verified in this snapshot. Never fill those gaps with invented data.
