"""Materialize explicitly transcribed, independently reviewed source excerpts.
Not a network collector. Excerpts are not full-page archival captures.
"""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def save(p,v):
    (R/p).parent.mkdir(parents=True,exist_ok=True)
    (R/p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
stand='''BUF 6 1 0 .857 233 181 52
NE 5 3 0 .625 184 162 22
NYJ 2 6 0 .250 170 188 -18
MIA 1 6 0 .143 117 181 -64
PIT 6 2 0 .750 180 144 36
CIN 5 2 0 .714 206 158 48
CLE 5 3 0 .625 139 173 -34
BAL 4 4 0 .500 179 203 -24
JAX 5 2 0 .714 196 111 85
HOU 2 5 0 .286 165 170 -5
TEN 1 7 0 .125 144 199 -55
IND 2 6 0 .250 161 222 -61
DEN 6 2 0 .750 172 165 7
KC 5 2 0 .714 167 131 36
LV 4 4 0 .500 221 230 -9
LAC 0 7 0 .000 99 175 -76
NYG 4 2 1 .643 163 161 2
DAL 3 5 0 .375 219 213 6
WAS 2 4 1 .357 159 182 -23
PHI 2 6 0 .250 137 202 -65
MIN 6 1 0 .857 140 93 47
CHI 6 2 0 .750 214 160 54
DET 5 2 0 .714 203 180 23
GB 5 3 0 .625 171 164 7
CAR 3 4 0 .429 178 193 -15
TB 3 5 0 .375 178 151 27
ATL 3 5 0 .375 171 189 -18
NO 2 5 0 .286 162 194 -32
SF 6 1 0 .857 197 139 58
SEA 4 4 0 .500 185 159 26
LA 4 4 0 .500 194 168 26
AZ 3 5 0 .375 175 238 -63'''
url='https://www.nfl.com/standings/'
rows=[]
for line in stand.splitlines():
    a,w,l,t,p,pf,pa,net=line.split()
    rows.append(dict(abbr=a,W=int(w),L=int(l),T=int(t),PCT=float(p),PF=int(pf),PA=int(pa),NET=int(net),source_url=url,evidence=line,status='verified snapshot'))
save('data/verified/standings.json',dict(checked_at='2026-11-04',season=2026,source_url=url,method='fetch_page chunks 0 and 1; selected columns transcribed row by row. No tail-column verification claimed.',rows=rows))
(R/'data/evidence/standings-excerpt.txt').write_text('Source: '+url+'\nChecked: 2026-11-04 via fetch_page, chunks 0 and 1\nScope: selected numeric columns only; transcription, NOT raw HTML.\nColumns: abbr W L T PCT PF PA NET\n'+stand+'\n')
# All 15 matchup/date pairs and international-game label checked against schedule chunks 0,1,2.
sched=json.loads((R.parent/'data/schedule-2026-week9.json').read_text())
games=[]
for g in sched['games']:
    games.append(dict(away=g['away'],home=g['home'],date=g['date'],neutral=g['away']=='CIN',neutral_status='verified Madrid international listing' if g['away']=='CIN' else 'not established; no home adjustment used',source_url=sched['source_url'],game_url=g['game_url'],kickoff_et=None,venue=None,status='matchup and date verified; time zone and venue withheld'))
save('data/verified/schedule.json',dict(checked_at='2026-11-04',rows=games,source_url=sched['source_url'],note='Only matchup, date and Madrid international label checked. LOCAL time labels do not establish ET. No venue or kickoff-time inference. Byes PIT, TEN checked but not model inputs.'))
# Independently read each named row from NGS Week 8 table, selected fields only.
ngs='''Joe Burrow|CIN|48|462|12.1
Deshaun Watson|CLE|39|324|-2.3
Patrick Mahomes|KC|41|321|3.8
Cam Ward|TEN|40|304|-1.7
Geno Smith|NYJ|32|290|7.2
Josh Allen|BUF|34|289|-8.4
Jordan Love|GB|41|288|8.4
Justin Herbert|LAC|32|257|2.2
Kirk Cousins|LV|26|247|16.1
Caleb Williams|CHI|34|247|0.5
Bo Nix|DEN|32|222|-5.6
Jayden Daniels|WAS|29|217|-5.3
Tanner McKee|PHI|34|212|-1.9
Malik Willis|MIA|32|211|-2.8
Kyler Murray|MIN|29|210|2
Bryce Young|CAR|41|209|-3.1
Drake Maye|NE|20|199|8.4
Dak Prescott|DAL|29|195|-1.9
Sam Darnold|SEA|34|188|-13.2
Gardner Minshew|AZ|23|188|12
Jared Goff|DET|25|176|-1.9
Aaron Rodgers|PIT|25|172|-9.7
Matthew Stafford|LAR|25|157|-5.8
Daniel Jones|IND|28|144|-0.3
Michael Penix Jr.|ATL|24|125|-22.6
Jacoby Brissett|AZ|23|119|-6.1
Joe Fagnano|BAL|21|91|-19'''
u='https://nextgenstats.nfl.com/stats/passing/2026/REG/8'
players=[]
for line in ngs.splitlines():
    n,t,a,y,c=line.split('|')
    players.append(dict(name=n,team=t,ATT=int(a),YDS=int(y),CPOE=float(c),source_url=u,status='verified Week 8 snapshot'))
save('data/verified/passing.json',dict(checked_at='2026-11-04',source_url=u,scope='27 rendered Week 8 rows; not season totals or a complete player universe. ATT, YDS and CPOE only.',rows=players))
(R/'data/evidence/passing-excerpt.txt').write_text('Source: '+u+'\nChecked 2026-11-04 via fetch_page chunk 0. Selected-field transcription, NOT raw HTML.\nname|team|ATT|YDS|CPOE\n'+ngs+'\n')
(R/'data/evidence/schedule-excerpt.txt').write_text('Source: '+sched['source_url']+'\nChecked 2026-11-04 via fetch_page chunks 0,1,2. Selected-field transcription, NOT raw HTML.\n'+'\n'.join(g['away']+' at '+g['home']+' '+g['date']+(' Madrid international game' if g['neutral'] else '') for g in games)+'\n')
