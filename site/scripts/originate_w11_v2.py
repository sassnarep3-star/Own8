#!/usr/bin/env python3
"""Produce a separately versioned Week 11 B0 line set after the Week 10 MNF result."""
import json
from pathlib import Path
import model_b0

ROOT = Path(__file__).resolve().parents[2]
stand_doc = json.loads((ROOT / 'site/data/standings-2026-11-18.json').read_text())
stand = {r['team']: {'G': r['G'], 'PF': r['PF'], 'PA': r['PA']} for r in stand_doc['rows']}
schedule = json.loads((ROOT / 'site/data/week11-schedule.json').read_text())['games']
lines = model_b0.originate_w11(stand)
for row, fixture in zip(lines, schedule):
    away, home = row['away'], row['home']
    row['inputs'] = {
        'away': {'team': away, **stand[away], 'source': 'site/data/standings-2026-11-18.json'},
        'home': {'team': home, **stand[home], 'source': 'site/data/standings-2026-11-18.json'},
        'formula': 'H=(home PF/G + away PA/G)/2; A=(away PF/G + home PA/G)/2; margin=H-A; total=H+A; P(home)=Phi(margin/13.1768)',
    }
    row['market_spread_home'] = None
    row['market_total'] = None
    row['market_ml_home'] = None
    row['difference_column'] = 'BLANK (no verified Week 11 market capture)'
    row['source_schedule'] = fixture['source_url']
    row['source_standings'] = 'https://www.nfl.com/standings/league/2026/REG'

out = {
  'version': 'B0-v2',
  'generated': '2026-11-18',
  'status': 'PROVISIONAL; pre-registered in this commit before Week 11 kickoff (2026-11-19 8:15 PM ET)',
  'supersedes': 'site/data/b0-w11-lines.json (B0-v1; frozen pre-Monday snapshot; retained unchanged)',
  'method': 'Same frozen B0 formula and sigma as v1; only the verified LAC@BAL Week 10 result is added to the standings inputs. It is a new version, not a post-hoc edit to v1.',
  'sigma_margin': model_b0.SIGMA,
  'input_snapshot': 'site/data/standings-2026-11-18.json',
  'input_source': 'https://www.nfl.com/standings/league/2026/REG',
  'result_source': 'https://static.www.nfl.com/image/upload/v1794916121/gamecenter/ab78ad5a-4feb-11f1-abca-2c54536568a9.pdf',
  'registration_rule': 'This file and its commit hash are the pre-kickoff registration. Do not edit after kickoff; any later correction requires a new versioned file.',
  'games': lines,
}
path=ROOT/'site/data/b0-w11-lines-v2.json'
path.write_text(json.dumps(out,indent=2)+'\n')
print(f'Wrote {path.relative_to(ROOT)} with {len(lines)} lines; all 13 fixtures retained.')
