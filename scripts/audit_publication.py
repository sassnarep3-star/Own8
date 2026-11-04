#!/usr/bin/env python3
"""Check active HTML local targets against legacy Jekyll exclusions.
This verifies deployment selection, not external liveness or Jekyll rendering.
"""
import json,re
from pathlib import Path
from urllib.parse import urlparse,unquote
R=Path(__file__).resolve().parent.parent
excluded=[json.loads(line.split('- ',1)[1]) for line in (R/'_config.yml').read_text().splitlines() if line.startswith('  - ')]
files=[R/'index.html',*list((R/'pages').glob('*.html')),*list((R/'docs').glob('*.html')),*list((R/'audit').glob('*.html')),*list((R/'strict/site').rglob('*.html'))]
errors=[];count=0
for f in files:
 for u in re.findall(r'(?:href|src)="([^"]+)"',f.read_text()):
  p=urlparse(u)
  if p.scheme or not p.path:continue
  target=(f.parent/unquote(p.path)).resolve()
  if target.is_dir():target=target/'index.html'
  if not target.is_relative_to(R):errors.append(f'{f.relative_to(R)} escapes root');continue
  rel=str(target.relative_to(R));count+=1
  if not target.exists():errors.append(f'{f.relative_to(R)} missing {u}')
  if any(rel==x or rel.startswith(x+'/') for x in excluded):errors.append(f'{f.relative_to(R)} links to excluded {rel}')
assert not errors, '\n'.join(errors)
print(f'Publication scope PASS: {len(files)} active HTML files, {count} local URLs, no excluded targets.')
