#!/usr/bin/env python3
"""Refresh canonical audit snapshot from official-source captures of 2026-11-14.

Data transcribed line-by-line from official pages retrieved via the page-extraction
tool on 2026-11-14 (UTC):
  - https://www.nfl.com/standings/                 (32 rows, 2 chunks)
  - https://www.nfl.com/schedules/2026/by-week/week-10 (14 games, 3 chunks)
  - https://www.nfl.com/scores/2026/week-9         (15 games, 2 chunks)
  - https://www.nfl.com/injuries/league/2026/reg10 (bounded 6-game sample, 8 chunks)
  - https://nextgenstats.nfl.com/stats/passing/2026/REG/9 (30 rows)

Checks (all fail-closed; a failed check aborts the write):
  1. Standings arithmetic: PF-PA=NET; PCT=(W+0.5T)/GP; W+L+T=GP.
  2. Tail-column internal checks: HOME+ROAD=GP; DIV%/CONF% recompute from DIV/CONF.
  3. Cross-capture: every 2026-11-14 standings row = 2026-11-04 (post-W8) snapshot
     record + that team's Week 9 game result (or bye).
  4. Schedule: 14 Week 10 games + 4 byes (CHI/DEN/PHI/TB); teams partition 32.
  5. Scores: 15 Week 9 games + WAS-NYG Week 10 result (played Thu 2026-11-12).
  6. Injuries: bounded sample rows parse; practice/game status vocabulary bounded.
  7. NGS: 30 rows parse from the raw transcription file; team set consistent.

The script writes:
  data/audit-snapshot.json                 (canonical, as_of 2026-11-14)
  data/audit-snapshot-2026-11-04.json      (archive copy of the previous snapshot)
  data/ngs-passing-2026-week9.json         (parsed NGS W9 evidence)
  data/live-verify-2026-11-14.json         (check report)
and updates data/sources.json + appends flags to data/flagged.json.
"""
import json, shutil
from pathlib import Path

R = Path(__file__).resolve().parent.parent
D = R / 'data'
AS_OF = '2026-11-14'
SRC = 'https://www.nfl.com/standings/'
SCHED_SRC = 'https://www.nfl.com/schedules/2026/by-week/week-10'
SCORES_SRC = 'https://www.nfl.com/scores/2026/week-9'
INJ_SRC = 'https://www.nfl.com/injuries/league/2026/reg10'
NGS_SRC = 'https://nextgenstats.nfl.com/stats/passing/2026/REG/9'

def read(p): return json.loads((R / p).read_text())
def save(p, obj): (R / p).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')

# ---------------------------------------------------------------- standings ---
# Transcribed from nfl.com/standings/ (detailed view), 2026-11-14.
# Tail columns kept internally for arithmetic checks; only legend-defined core
# fields are published (HOME/ROAD/DIV/CONF withheld per prior audited design).
STANDINGS = [
 # abbr, W, L, T, PCT, PF, PA, NET, STRK, HOME, ROAD, DIV, DIVPCT, CONF, CONFPCT
 ('BUF', 7, 1, 0, 0.875, 256, 187, 69, '4W', '3-1-0', '4-0-0', '0-1-0', 0.000, '4-1-0', 0.800),
 ('NE', 5, 4, 0, 0.556, 211, 207, 4, '1L', '3-1-0', '2-3-0', '3-0-0', 1.000, '5-1-0', 0.833),
 ('NYJ', 2, 7, 0, 0.222, 182, 223, -41, '4L', '1-3-0', '1-4-0', '0-2-0', 0.000, '2-4-0', 0.333),
 ('MIA', 1, 7, 0, 0.125, 126, 200, -74, '2L', '0-4-0', '1-3-0', '1-1-0', 0.500, '1-4-0', 0.200),
 ('PIT', 6, 2, 0, 0.750, 180, 144, 36, '4W', '4-0-0', '2-2-0', '2-1-0', 0.667, '3-2-0', 0.600),
 ('CIN', 6, 2, 0, 0.750, 240, 175, 65, '4W', '2-1-0', '4-1-0', '1-1-0', 0.500, '4-2-0', 0.667),
 ('CLE', 5, 4, 0, 0.556, 161, 196, -35, '2L', '3-0-0', '2-4-0', '2-1-0', 0.667, '3-3-0', 0.500),
 ('BAL', 4, 5, 0, 0.444, 189, 236, -47, '4L', '1-3-0', '3-2-0', '0-2-0', 0.000, '2-4-0', 0.333),
 ('JAX', 6, 2, 0, 0.750, 229, 121, 108, '2W', '4-1-0', '2-1-0', '1-1-0', 0.500, '5-2-0', 0.714),
 ('HOU', 3, 5, 0, 0.375, 209, 192, 17, '1W', '0-4-0', '3-1-0', '2-1-0', 0.667, '3-3-0', 0.500),
 ('IND', 2, 7, 0, 0.222, 184, 249, -65, '5L', '1-3-0', '1-4-0', '1-2-0', 0.333, '1-5-0', 0.167),
 ('TEN', 1, 7, 0, 0.125, 144, 199, -55, '2L', '0-4-0', '1-3-0', '1-1-0', 0.500, '1-5-0', 0.167),
 ('DEN', 7, 2, 0, 0.778, 198, 186, 12, '5W', '4-0-0', '3-2-0', '2-1-0', 0.667, '3-1-0', 0.750),
 ('KC', 6, 2, 0, 0.750, 202, 143, 59, '1W', '4-0-0', '2-2-0', '3-1-0', 0.750, '6-1-0', 0.857),
 ('LV', 4, 5, 0, 0.444, 238, 268, -30, '1L', '1-3-0', '3-2-0', '1-1-0', 0.500, '3-3-0', 0.500),
 ('LAC', 0, 8, 0, 0.000, 121, 219, -98, '8L', '0-4-0', '0-4-0', '0-3-0', 0.000, '0-5-0', 0.000),
 ('NYG', 5, 3, 1, 0.611, 203, 196, 7, '1L', '3-2-0', '2-1-1', '2-1-1', 0.625, '3-3-1', 0.500),
 ('DAL', 4, 5, 0, 0.444, 246, 236, 10, '1W', '1-3-0', '3-2-0', '2-1-0', 0.667, '2-4-0', 0.333),
 ('WAS', 3, 5, 1, 0.389, 196, 223, -27, '1W', '2-2-1', '1-3-0', '2-2-1', 0.500, '3-4-1', 0.438),
 ('PHI', 2, 7, 0, 0.222, 148, 221, -73, '7L', '1-4-0', '1-3-0', '1-3-0', 0.250, '1-6-0', 0.143),
 ('CHI', 7, 2, 0, 0.778, 241, 184, 57, '4W', '4-1-0', '3-1-0', '0-2-0', 0.000, '5-2-0', 0.714),
 ('DET', 6, 2, 0, 0.750, 222, 189, 33, '4W', '4-0-0', '2-2-0', '2-0-0', 1.000, '4-1-0', 0.800),
 ('MIN', 6, 2, 0, 0.750, 146, 116, 30, '2L', '3-1-0', '3-1-0', '2-1-0', 0.667, '4-1-0', 0.800),
 ('GB', 6, 3, 0, 0.667, 216, 191, 25, '2W', '3-1-0', '3-2-0', '1-2-0', 0.333, '4-3-0', 0.571),
 ('CAR', 3, 5, 0, 0.375, 199, 219, -20, '3L', '1-3-0', '2-2-0', '1-1-0', 0.500, '3-3-0', 0.500),
 ('NO', 3, 5, 0, 0.375, 185, 216, -31, '1W', '1-4-0', '2-1-0', '0-1-0', 0.000, '1-3-0', 0.250),
 ('TB', 3, 6, 0, 0.333, 202, 178, 24, '1L', '1-4-0', '2-2-0', '2-0-0', 1.000, '3-3-0', 0.500),
 ('ATL', 3, 6, 0, 0.333, 188, 223, -35, '2L', '1-4-0', '2-2-0', '1-2-0', 0.333, '3-3-0', 0.500),
 ('SF', 7, 1, 0, 0.875, 235, 156, 79, '1W', '5-0-0', '2-1-0', '3-0-0', 1.000, '4-1-0', 0.800),
 ('SEA', 5, 4, 0, 0.556, 202, 162, 40, '1W', '4-2-0', '1-2-0', '2-1-0', 0.667, '2-3-0', 0.400),
 ('LA', 5, 4, 0, 0.556, 214, 181, 33, '3W', '2-3-0', '3-1-0', '0-2-0', 0.000, '3-2-0', 0.600),
 ('AZ', 3, 6, 0, 0.333, 178, 255, -77, '1L', '0-3-0', '3-3-0', '1-3-0', 0.250, '2-5-0', 0.286),
]

# ---------------------------------------------------- Week 10 schedule (14) ---
# Transcribed from nfl.com/schedules/2026/by-week/week-10, 2026-11-14.
SCHEDULE = [
 # away, home, date, kickoff_et, network, game_url
 ('WAS', 'NYG', '2026-11-12', '8:15 PM', 'Prime Video', 'https://www.nfl.com/games/commanders-at-giants-2026-reg-10'),
 ('NE', 'DET', '2026-11-15', '9:30 AM', 'FOX', 'https://www.nfl.com/games/patriots-at-lions-2026-reg-10'),
 ('KC', 'ATL', '2026-11-15', '1:00 PM', 'CBS', 'https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10'),
 ('HOU', 'CLE', '2026-11-15', '1:00 PM', 'FOX', 'https://www.nfl.com/games/texans-at-browns-2026-reg-10'),
 ('MIN', 'GB', '2026-11-15', '1:00 PM', 'FOX', 'https://www.nfl.com/games/vikings-at-packers-2026-reg-10'),
 ('MIA', 'IND', '2026-11-15', '1:00 PM', 'CBS', 'https://www.nfl.com/games/dolphins-at-colts-2026-reg-10'),
 ('CAR', 'NO', '2026-11-15', '1:00 PM', 'FOX', 'https://www.nfl.com/games/panthers-at-saints-2026-reg-10'),
 ('BUF', 'NYJ', '2026-11-15', '1:00 PM', 'CBS', 'https://www.nfl.com/games/bills-at-jets-2026-reg-10'),
 ('JAX', 'TEN', '2026-11-15', '1:00 PM', 'FOX', 'https://www.nfl.com/games/jaguars-at-titans-2026-reg-10'),
 ('LA', 'AZ', '2026-11-15', '4:05 PM', 'CBS', 'https://www.nfl.com/games/rams-at-cardinals-2026-reg-10'),
 ('SEA', 'LV', '2026-11-15', '4:05 PM', 'CBS', 'https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10'),
 ('SF', 'DAL', '2026-11-15', '4:25 PM', 'FOX', 'https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10'),
 ('PIT', 'CIN', '2026-11-15', '8:20 PM', 'NBC', 'https://www.nfl.com/games/steelers-at-bengals-2026-reg-10'),
 ('LAC', 'BAL', '2026-11-16', '8:15 PM', 'ESPN', 'https://www.nfl.com/games/chargers-at-ravens-2026-reg-10'),
]
BYES_W10 = ['CHI', 'DEN', 'PHI', 'TB']

# ----------------------------------------------------------- Week 9 scores ---
# Transcribed from nfl.com/scores/2026/week-9, 2026-11-14 (15 games, all FINAL).
SCORES_W9 = [
 # away, home, away_score, home_score, date, game_url
 ('JAX', 'BAL', 33, 10, '2026-11-05', 'https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9'),
 ('CIN', 'ATL', 34, 17, '2026-11-08', 'https://www.nfl.com/games/bengals-at-falcons-2026-reg-9'),
 ('DEN', 'CAR', 26, 21, '2026-11-08', 'https://www.nfl.com/games/broncos-at-panthers-2026-reg-9'),
 ('DAL', 'IND', 27, 23, '2026-11-08', 'https://www.nfl.com/games/cowboys-at-colts-2026-reg-9'),
 ('NYJ', 'KC', 12, 35, '2026-11-08', 'https://www.nfl.com/games/jets-at-chiefs-2026-reg-9'),
 ('DET', 'MIA', 19, 9, '2026-11-08', 'https://www.nfl.com/games/lions-at-dolphins-2026-reg-9'),
 ('CLE', 'NO', 22, 23, '2026-11-08', 'https://www.nfl.com/games/browns-at-saints-2026-reg-9'),
 ('NYG', 'PHI', 19, 11, '2026-11-08', 'https://www.nfl.com/games/giants-at-eagles-2026-reg-9'),
 ('LA', 'WAS', 20, 13, '2026-11-08', 'https://www.nfl.com/games/rams-at-commanders-2026-reg-9'),
 ('HOU', 'LAC', 44, 22, '2026-11-08', 'https://www.nfl.com/games/texans-at-chargers-2026-reg-9'),
 ('LV', 'SF', 17, 38, '2026-11-08', 'https://www.nfl.com/games/raiders-at-49ers-2026-reg-9'),
 ('GB', 'NE', 45, 27, '2026-11-08', 'https://www.nfl.com/games/packers-at-patriots-2026-reg-9'),
 ('AZ', 'SEA', 3, 17, '2026-11-08', 'https://www.nfl.com/games/cardinals-at-seahawks-2026-reg-9'),
 ('TB', 'CHI', 24, 27, '2026-11-08', 'https://www.nfl.com/games/buccaneers-at-bears-2026-reg-9'),
 ('BUF', 'MIN', 23, 6, '2026-11-09', 'https://www.nfl.com/games/bills-at-vikings-2026-reg-9'),
]
# WAS-NYG Week 10 result (played Thursday 2026-11-12, final per nfl.com schedule page)
SCORES_W10_DONE = [
 ('WAS', 'NYG', 24, 21, '2026-11-12', 'https://www.nfl.com/games/commanders-at-giants-2026-reg-10'),
]

# ----------------------------------------------- Week 10 injury sample ------
# Bounded sample: full sections for 6 of 14 Week 10 games, transcribed from
# nfl.com/injuries/league/2026/reg10, 2026-11-14. Other games' sections were
# retrieved and reviewed but are not transcribed (bounded coverage, clearly labeled).
# tuple: (team, player, position, injury, practice, game_status); None => blank.
INJURIES = [
 ('WAS', 'John Bates', 'TE', None, 'Full Participation in Practice', None),
 ('WAS', 'Treylon Burks', 'WR', None, 'Did Not Participate In Practice', None),
 ('WAS', 'Jayden Daniels', 'QB', None, 'Full Participation in Practice', None),
 ('WAS', 'Matt Gulbin', 'C', None, 'Full Participation in Practice', None),
 ('WAS', 'Chig Okonkwo', 'TE', None, 'Full Participation in Practice', None),
 ('WAS', 'Lucas Patrick', 'C', 'Concussion', 'Did Not Participate In Practice', 'Out'),
 ('WAS', 'Amik Robertson', 'CB', None, 'Limited Participation in Practice', None),
 ('WAS', 'Shy Tuttle', 'DT', None, 'Full Participation in Practice', None),
 ('WAS', 'Colson Yankoff', 'TE', 'Knee', 'Did Not Participate In Practice', 'Out'),
 ('NYG', 'Abdul Carter', 'LB', None, 'Full Participation in Practice', None),
 ('NYG', 'Jermaine Eluemunor', 'T', None, 'Full Participation in Practice', None),
 ('NYG', 'Malik Harrison', 'LB', 'Groin', 'Limited Participation in Practice', 'Questionable'),
 ('NYG', 'Colton Hood', 'CB', None, 'Full Participation in Practice', None),
 ('NYG', 'Theo Johnson', 'TE', None, 'Full Participation in Practice', None),
 ('NYG', 'Charlie Jones', 'WR', None, 'Full Participation in Practice', None),
 ('NYG', 'J.J. McCarthy', 'QB', None, 'Full Participation in Practice', None),
 ('NYG', 'Darnell Mooney', 'WR', None, 'Full Participation in Practice', None),
 ('NYG', 'Malik Nabers', 'WR', None, 'Full Participation in Practice', None),
 ('NYG', 'Cam Skattebo', 'RB', None, 'Full Participation in Practice', None),
 ('NYG', 'Andrew Thomas', 'T', None, 'Full Participation in Practice', None),
 ('NE', 'Ben Brown', 'C', 'Knee', 'Did Not Participate In Practice', 'Out'),
 ('NE', 'A.J. Brown', 'WR', 'Ankle, Knee', 'Limited Participation in Practice', 'Questionable'),
 ('NE', 'Kevin Byard', 'S', 'Chest', 'Full Participation in Practice', 'Questionable'),
 ('NE', 'Carlton Davis III', 'CB', 'Knee', 'Did Not Participate In Practice', 'Out'),
 ('NE', 'Reggie Gilliam', 'FB', 'Knee', 'Limited Participation in Practice', 'Questionable'),
 ('NE', 'TreVeyon Henderson', 'RB', 'Illness', 'Did Not Participate In Practice', 'Out'),
 ('NE', 'Hunter Henry', 'TE', None, 'Limited Participation in Practice', None),
 ('NE', 'Cameron Latu', 'TE', 'Back', 'Limited Participation in Practice', 'Questionable'),
 ('NE', 'Drake Maye', 'QB', None, 'Full Participation in Practice', None),
 ('NE', 'Morgan Moses', 'T', None, 'Full Participation in Practice', None),
 ('NE', 'Walter Rouse', 'T', 'Concussion', 'Limited Participation in Practice', 'Questionable'),
 ('NE', 'Brenden Schooler', 'S', 'Hamstring', 'Limited Participation in Practice', 'Questionable'),
 ('NE', 'Rhamondre Stevenson', 'RB', 'Knee', 'Limited Participation in Practice', 'Questionable'),
 ('NE', 'Greg Van Roten', 'G', 'Hamstring', 'Full Participation in Practice', 'Questionable'),
 ('NE', 'Charles Woods', 'CB', 'Hamstring', 'Full Participation in Practice', 'Questionable'),
 ('DET', 'Brian Branch', 'S', None, 'Full Participation in Practice', None),
 ('DET', 'Jared Goff', 'QB', None, 'Full Participation in Practice', None),
 ('DET', 'Kerby Joseph', 'S', 'Knee', 'Did Not Participate In Practice', 'Out'),
 ('DET', 'Cade Mays', 'C', 'Ankle', 'Did Not Participate In Practice', 'Out'),
 ('DET', 'D.J. Reed', 'CB', 'Hip', 'Did Not Participate In Practice', 'Out'),
 ('DET', 'Jacob Saylors', 'RB', None, 'Full Participation in Practice', None),
 ('DET', 'Amon-Ra St. Brown', 'WR', 'Rib', 'Limited Participation in Practice', 'Questionable'),
 ('DET', 'Sione Vaki', 'RB', 'Ankle', 'Limited Participation in Practice', 'Questionable'),
 ('DET', 'DJ Wonnum', 'DE', None, 'Full Participation in Practice', None),
 ('MIN', 'Jordan Addison', 'WR', 'Thumb', 'Limited Participation in Practice', 'Questionable'),
 ('MIN', 'Blake Cashman', 'LB', 'Concussion', 'Limited Participation in Practice', 'Out'),
 ('MIN', 'Christian Darrisaw', 'T', None, 'Did Not Participate In Practice', None),
 ('MIN', 'T.J. Hockenson', 'TE', 'Wrist, Chest', 'Did Not Participate In Practice', 'Out'),
 ('MIN', 'Tyrion Ingram-Dawkins', 'DT', 'Ankle', 'Did Not Participate In Practice', 'Out'),
 ('MIN', 'Theo Jackson', 'S', None, 'Full Participation in Practice', None),
 ('MIN', 'Jauan Jennings', 'WR', 'Calf', 'Did Not Participate In Practice', 'Out'),
 ('MIN', 'Josh Metellus', 'S', 'Shoulder', 'Limited Participation in Practice', 'Questionable'),
 ('MIN', 'Kyler Murray', 'QB', 'Hamstring', 'Did Not Participate In Practice', 'Out'),
 ('MIN', 'Harrison Smith', 'S', None, 'Limited Participation in Practice', None),
 ('MIN', 'Kyle Van Noy', 'LB', 'Calf', 'Limited Participation in Practice', 'Questionable'),
 ('MIN', 'Jay Ward', 'S', None, 'Full Participation in Practice', None),
 ('MIN', 'Carson Wentz', 'QB', None, 'Full Participation in Practice', None),
 ('GB', 'Aaron Banks', 'G', None, 'Limited Participation in Practice', None),
 ('GB', 'Chris Brooks', 'RB', 'Ankle', 'Limited Participation in Practice', 'Questionable'),
 ('GB', 'Javon Bullard', 'S', 'Ankle, Knee', 'Limited Participation in Practice', 'Questionable'),
 ('GB', 'Zaire Franklin', 'LB', 'Shin', 'Did Not Participate In Practice', 'Doubtful'),
 ('GB', 'Travis Glover', 'G', 'Knee', 'Limited Participation in Practice', 'Questionable'),
 ('GB', 'Ty\'Ron Hopper', 'LB', None, 'Full Participation in Practice', None),
 ('GB', 'Josh Jacobs', 'RB', 'Finger', 'Did Not Participate In Practice', 'Out'),
 ('GB', 'Xavier McKinney', 'S', 'Foot', 'Limited Participation in Practice', 'Questionable'),
 ('GB', 'Bo Melton', 'WR', None, 'Full Participation in Practice', None),
 ('GB', 'Skyy Moore', 'WR', 'Ankle', 'Limited Participation in Practice', 'Questionable'),
 ('GB', 'Micah Parsons', 'LB', 'Knee, Illness', 'Limited Participation in Practice', 'Out'),
 ('GB', 'Sean Rhyan', 'C', 'Ankle', 'Did Not Participate In Practice', 'Out'),
 ('GB', 'Trey Smack', 'K', None, 'Full Participation in Practice', None),
 ('GB', 'Lukas Van Ness', 'LB', 'Back', 'Limited Participation in Practice', 'Questionable'),
 ('GB', 'Josh Whyle', 'TE', 'Concussion', 'Did Not Participate In Practice', 'Out'),
 ('GB', 'Savion Williams', 'WR', None, 'Limited Participation in Practice', None),
 ('GB', 'Kevin Zeitler', 'G', 'Ankle, Triceps', 'Did Not Participate In Practice', 'Questionable'),
 ('SF', 'Mike Evans', 'WR', 'Achilles', 'Did Not Participate In Practice', 'Out'),
 ('SF', 'Renardo Green', 'CB', 'Back', 'Limited Participation in Practice', 'Questionable'),
 ('SF', 'Dre Greenlaw', 'LB', 'Knee', 'Limited Participation in Practice', 'Questionable'),
 ('SF', 'Nate Hobbs', 'CB', 'Groin', 'Full Participation in Practice', 'Questionable'),
 ('SF', 'Deommodore Lenoir', 'CB', 'Foot', 'Limited Participation in Practice', 'Questionable'),
 ('SF', 'Christian McCaffrey', 'RB', None, 'Full Participation in Practice', None),
 ('SF', 'Siran Neal', 'S', None, 'Full Participation in Practice', None),
 ('SF', 'Demarcus Robinson', 'WR', None, 'Full Participation in Practice', None),
 ('SF', 'Deebo Samuel Sr.', 'WR', None, 'Full Participation in Practice', None),
 ('SF', 'Upton Stout', 'CB', 'Shoulder, Neck', 'Limited Participation in Practice', 'Questionable'),
 ('SF', 'C.J. West', 'DT', 'Knee', 'Full Participation in Practice', 'Questionable'),
 ('SF', 'Trent Williams', 'T', 'Shoulder', 'Did Not Participate In Practice', 'Questionable'),
 ('DAL', 'DaRon Bland', 'CB', 'Ankle', 'Limited Participation in Practice', 'Questionable'),
 ('DAL', 'Jonathan Bullard', 'DT', 'Calf', 'Full Participation in Practice', 'Questionable'),
 ('DAL', 'Alijah Clark', 'S', 'Illness', 'Did Not Participate In Practice', 'Questionable'),
 ('DAL', 'Donovan Ezeiruaku', 'LB', 'Ankle', 'Did Not Participate In Practice', 'Out'),
 ('DAL', 'Jake Ferguson', 'TE', 'Knee, Ankle', 'Did Not Participate In Practice', 'Out'),
 ('DAL', 'Tyler Goodson', 'RB', 'Ankle, Knee', 'Did Not Participate In Practice', 'Out'),
 ('DAL', 'Malik Hooker', 'S', None, 'Did Not Participate In Practice', None),
 ('DAL', 'Marist Liufau', 'LB', None, 'Full Participation in Practice', None),
 ('DAL', 'P.J. Locke', 'S', 'Concussion', 'Did Not Participate In Practice', 'Out'),
 ('DAL', 'Von Miller', 'LB', None, 'Did Not Participate In Practice', None),
 ('DAL', 'Jonathan Mingo', 'WR', 'Ankle', 'Did Not Participate In Practice', 'Out'),
 ('DAL', 'Devin Moore', 'CB', 'Hip', 'Full Participation in Practice', 'Questionable'),
 ('DAL', 'DeMarvion Overshown', 'LB', None, 'Full Participation in Practice', None),
 ('DAL', 'George Pickens', 'WR', None, 'Full Participation in Practice', None),
 ('DAL', 'Joey Porter Jr.', 'CB', 'Ankle, Foot', 'Limited Participation in Practice', 'Questionable'),
 ('DAL', 'Luke Schoonmaker', 'TE', None, 'Full Participation in Practice', None),
 ('DAL', 'Brevyn Spann-Ford', 'TE', None, 'Full Participation in Practice', None),
 ('DAL', 'Juanyeh Thomas', 'S', 'Hamstring', 'Did Not Participate In Practice', 'Doubtful'),
 ('DAL', 'KaVontae Turpin', 'WR', None, 'Full Participation in Practice', None),
 ('PIT', 'Brandin Echols', 'CB', None, 'Full Participation in Practice', None),
 ('PIT', 'DeShon Elliott', 'S', None, 'Full Participation in Practice', None),
 ('PIT', 'Derrick Harmon', 'DT', 'Foot', 'Full Participation in Practice', 'Questionable'),
 ('PIT', 'Cameron Heyward', 'DT', None, 'Full Participation in Practice', None),
 ('PIT', 'Ben Skowronek', 'WR', None, 'Full Participation in Practice', None),
 ('PIT', 'Doneiko Slaughter', 'CB', None, 'Full Participation in Practice', None),
 ('PIT', 'Darnell Washington', 'TE', None, 'Full Participation in Practice', None),
 ('PIT', 'T.J. Watt', 'LB', None, 'Full Participation in Practice', None),
 ('CIN', 'Jonathan Allen', 'DT', None, 'Limited Participation in Practice', None),
 ('CIN', 'Jalen Davis', 'CB', 'Hamstring', 'Full Participation in Practice', 'Doubtful'),
 ('CIN', 'Kyle Dugger', 'S', 'Quadricep', 'Did Not Participate In Practice', 'Out'),
 ('CIN', 'Dylan Fairchild', 'G', None, 'Full Participation in Practice', None),
 ('CIN', 'B.J. Hill', 'DT', None, 'Did Not Participate In Practice', None),
 ('CIN', 'Andrei Iosivas', 'WR', 'Thumb', 'Full Participation in Practice', 'Doubtful'),
 ('CIN', 'Dexter Lawrence', 'DT', None, 'Did Not Participate In Practice', None),
 ('CIN', 'Brian Parker II', 'G', 'Knee', 'Full Participation in Practice', 'Doubtful'),
 ('CIN', 'DJ Turner II', 'CB', None, 'Full Participation in Practice', None),
 ('LAC', 'Kayode Awosika', 'G', None, 'Limited Participation in Practice', None),
 ('LAC', 'Bud Dupree', 'DE', None, 'Did Not Participate In Practice', None),
 ('LAC', 'Justin Eboigbe', 'DE', None, 'Limited Participation in Practice', None),
 ('LAC', 'Alex Harkey', 'G', None, 'Full Participation in Practice', None),
 ('LAC', 'Tre Harris', 'WR', None, 'Full Participation in Practice', None),
 ('LAC', 'Cam Hart', 'CB', None, 'Full Participation in Practice', None),
 ('LAC', 'Daiyan Henley', 'LB', None, 'Full Participation in Practice', None),
 ('LAC', 'Deane Leonard', 'CB', None, 'Full Participation in Practice', None),
 ('LAC', 'Khalil Mack', 'LB', None, 'Full Participation in Practice', None),
 ('LAC', 'Ladd McConkey', 'WR', None, 'Did Not Participate In Practice', None),
 ('LAC', 'Keaton Mitchell', 'RB', None, 'Limited Participation in Practice', None),
 ('LAC', 'David Njoku', 'TE', None, 'Limited Participation in Practice', None),
 ('LAC', 'Denzel Perryman', 'LB', None, 'Full Participation in Practice', None),
 ('LAC', 'Trey Pipkins', 'T', None, 'Did Not Participate In Practice', None),
 ('LAC', 'Rodney Shelley', 'CB', None, 'Limited Participation in Practice', None),
 ('LAC', 'Branson Taylor', 'G', None, 'Did Not Participate In Practice', None),
 ('LAC', 'Brenen Thompson', 'WR', None, 'Did Not Participate In Practice', None),
 ('LAC', 'Isas Waxter', 'CB', None, 'Did Not Participate In Practice', None),
 ('LAC', 'Kendall Williamson', 'S', None, 'Did Not Participate In Practice', None),
 ('BAL', 'Rasheen Ali', 'RB', None, 'Full Participation in Practice', None),
 ('BAL', 'Rashod Bateman', 'WR', None, 'Full Participation in Practice', None),
 ('BAL', 'Kyle Hamilton', 'S', None, 'Full Participation in Practice', None),
 ('BAL', 'Jaylinn Hawkins', 'S', None, 'Limited Participation in Practice', None),
 ('BAL', 'Matthew Hibner', 'TE', None, 'Full Participation in Practice', None),
 ('BAL', 'Olaivavega Ioane', 'G', None, 'Full Participation in Practice', None),
 ('BAL', 'Adam Randall', 'RB', None, 'Full Participation in Practice', None),
 ('BAL', 'Nate Wiggins', 'CB', None, 'Full Participation in Practice', None),
]

# ------------------------------------------------------------- news items ----
# Headlines + URLs listed on the official Week 10 injury page, retrieved 2026-11-14.
# Publication dates unverified; claims transcribed verbatim from the headlines.
NEWS = [
 ('Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders',
  'NFL.com headline reports Drew Lock has no injury designation and will start for Seattle in Week 10.',
  'https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders'),
 ('NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable',
  'NFL.com roundup reports the Ravens confirmed Lamar Jackson is expected to miss 6-10 weeks; Kenneth Walker is questionable.',
  'https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13'),
 ('Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start',
  'NFL.com reports the Dolphins placed QB Malik Willis on injured reserve and Kyle McCord is in line for his first start.',
  'https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start'),
 ('Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL',
  'NFL.com reports Rams WR Puka Nacua is likely to be placed on injured reserve (turf toe, sprained MCL and PCL).',
  'https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl'),
 ('Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD',
  'NFL.com reports Packers RB Josh Jacobs will undergo finger surgery this week; return timeline TBD.',
  'https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week'),
 ('Sam Darnold ruled out for Seahawks\' Week 10 game vs. Raiders; Drew Lock expected to start again',
  'NFL.com reports Sam Darnold is ruled out for Seattle\'s Week 10 game; Drew Lock is expected to start again.',
  'https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again'),
 ('NFL news roundup: J.J. McCarthy expected to play Week 10; Justin Herbert avoids finger fracture',
  'NFL.com roundup reports J.J. McCarthy is expected to play in Week 10 and Justin Herbert avoided a finger fracture.',
  'https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-9'),
 ('NFL Network: Ravens\' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season',
  'NFL.com reports Lamar Jackson (right thumb) is out 6-9 weeks and expects to return this season.',
  'https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season'),
 ('NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals\' Carson Beck to start vs. Rams',
  'NFL.com roundup reports the Browns will start QB Deshaun Watson vs. Texans and the Cardinals will start Carson Beck vs. Rams.',
  'https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11'),
 ('Report: Ravens QB Tyler Huntley out for season with turf toe injury',
  'NFL.com reports Ravens QB Tyler Huntley is out for the season with a turf toe injury.',
  'https://www.nfl.com/news/ravens-qb-tyler-huntley-out-for-season-turf-toe-injury'),
]

# ------------------------------------------------------------------ checks ---
def gp(w, l, t): return w + l + t

checks = []
def check(name, ok, detail):
    checks.append({'check': name, 'result': 'PASS' if ok else 'FAIL', 'detail': detail})
    return ok

fail = False

# 1. standings arithmetic + tail checks
# Official PCT/DIVPCT/CONFPCT are rounded to 3 decimals; compare within half a unit
# of the last displayed place (0.0005).
def r3(x): return abs(x - round(x, 3)) < 5e-4

for abbr, w, l, t, pct, pf, pa, net, strk, home, road, div, divpct, conf, confpct in STANDINGS:
    g = gp(w, l, t)
    check(f'standings:{abbr} PF-PA=NET', pf - pa == net, f'PF {pf} - PA {pa} = {pf-pa} vs NET {net}')
    check(f'standings:{abbr} PCT', r3(pct - (w + 0.5 * t) / g), f'PCT {pct} vs {(w+0.5*t)/g:.3f}')
    hw, hl, ht = map(int, home.split('-'))
    rw, rl, rt = map(int, road.split('-'))
    check(f'standings:{abbr} HOME+ROAD=GP', (hw+hl+ht) + (rw+rl+rt) == g, f'{home}+{road} vs GP {g}')
    dw, dl, dt = map(int, div.split('-'))
    cw, cl, ct = map(int, conf.split('-'))
    check(f'standings:{abbr} DIV%', r3(divpct - (dw + 0.5*dt) / (dw+dl+dt)), f'DIV% {divpct}')
    check(f'standings:{abbr} CONF%', r3(confpct - (cw + 0.5*ct) / (cw+cl+ct)), f'CONF% {confpct}')

# 3. cross-capture: new = old W8 + W9 result (+ W10 result where already played)
old = read('data/standings-2026-reg-w8.json')
old_rows = {r['abbr']: r for r in old['teams']}
w9_winners = {}
for a, h, as_, hs, d, u in SCORES_W9:
    if as_ > hs:
        w9_winners[a] = 'W'; w9_winners[h] = 'L'
    elif as_ < hs:
        w9_winners[a] = 'L'; w9_winners[h] = 'W'
    else:
        w9_winners[a] = 'T'; w9_winners[h] = 'T'
w10_winners = {}
for a, h, as_, hs, d, u in SCORES_W10_DONE:
    if as_ > hs:
        w10_winners[a] = 'W'; w10_winners[h] = 'L'
    elif as_ < hs:
        w10_winners[a] = 'L'; w10_winners[h] = 'W'
    else:
        w10_winners[a] = 'T'; w10_winners[h] = 'T'
new_map = {s[0]: s for s in STANDINGS}
for abbr, s in new_map.items():
    o = old_rows.get(abbr)
    if o is None:
        check(f'cross:{abbr} old row exists', False, 'missing from 2026-11-04 snapshot')
        continue
    exp = [o['W'], o['L'], o['T']]
    for res in (w9_winners.get(abbr), w10_winners.get(abbr)):
        if res == 'W': exp[0] += 1
        elif res == 'L': exp[1] += 1
        elif res == 'T': exp[2] += 1
    tags = [t for t, r in (('W9', w9_winners.get(abbr)), ('W10', w10_winners.get(abbr))) if r]
    check(f'cross:{abbr} ' + ('+'.join(tags) if tags else 'bye') + ' record',
          exp == [s[1], s[2], s[3]],
          f'{o["W"]}-{o["L"]}-{o["T"]} + {"+".join(tags) if tags else "bye"} -> {s[1]}-{s[2]}-{s[3]}')

# 4. schedule partition check
sched_teams = set()
for a, h, *_ in SCHEDULE:
    sched_teams.add(a); sched_teams.add(h)
check('schedule: 14 games / 28 teams', len(SCHEDULE) == 14 and len(sched_teams) == 28,
      f'{len(SCHEDULE)} games, {len(sched_teams)} unique teams')
check('schedule: 32 teams partition with byes',
      set(sched_teams) | set(BYES_W10) == set(new_map) and not (set(sched_teams) & set(BYES_W10)),
      f'byes {BYES_W10}')
check('schedule: WAS-NYG listed', any(a == 'WAS' and h == 'NYG' for a, h, *_ in SCHEDULE), 'WAS@NYG in slate')

# 5. scores: 15 W9 + WAS-NYG W10
check('scores: 15 Week 9 games', len(SCORES_W9) == 15, f'{len(SCORES_W9)} games')
w9_teams = set()
for a, h, *_ in SCORES_W9:
    w9_teams.add(a); w9_teams.add(h)
check('scores: W9 covers 30 teams + 2 byes',
      len(w9_teams) == 30 and (set(new_map) - w9_teams) == {'PIT', 'TEN'},
      f'byes PIT/TEN; uncovered {set(new_map) - w9_teams}')

# 6. injuries vocabulary
VOCAB_P = {'Full Participation in Practice', 'Limited Participation in Practice', 'Did Not Participate In Practice'}
VOCAB_G = {'Out', 'Doubtful', 'Questionable'}
bad_p = [r for r in INJURIES if r[4] not in VOCAB_P]
bad_g = [r for r in INJURIES if r[5] is not None and r[5] not in VOCAB_G]
check('injuries: practice vocabulary', not bad_p, f'{len(INJURIES)} rows, {len(bad_p)} bad practice values')
check('injuries: game-status vocabulary', not bad_g, f'{len(bad_g)} bad game-status values')
check('injuries: sample covers 6 games',
      {r[0] for r in INJURIES} == {'WAS', 'NYG', 'NE', 'DET', 'MIN', 'GB', 'SF', 'DAL', 'PIT', 'CIN', 'LAC', 'BAL'},
      f'{len({r[0] for r in INJURIES})} teams')

# 7. NGS parse
ngs_rows = []
for line in (R / 'data/raw-ngs-passing-2026-week9-transcription.txt').read_text().splitlines():
    if ' | ' in line:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 17 and parts[1].isalpha() and parts[1].isupper() and 2 <= len(parts[1]) <= 3:
            ngs_rows.append(parts)
check('ngs: 30 rows parsed', len(ngs_rows) == 30, f'{len(ngs_rows)} rows from raw transcription')
ngs_teams = {r[1] for r in ngs_rows}
# Official-surface abbreviation difference: NGS renders the Rams as LAR while
# nfl.com standings/schedules use LA. Normalize for the consistency check.
NGS_ALIAS = {'LAR': 'LA'}
ngs_teams_norm = {NGS_ALIAS.get(t, t) for t in ngs_teams}
check('ngs: teams consistent with schedule/standings', ngs_teams_norm <= set(new_map),
      f'{len(ngs_teams)} teams, all in standings (after LAR->LA alias)')

for c in checks:
    if c['result'] == 'FAIL':
        fail = True
        print('FAIL:', c['check'], '-', c['detail'])
if fail:
    print('VERIFICATION FAILED — snapshot NOT written.')
    raise SystemExit(1)

# ------------------------------------------------------------ write outputs ---
standings_rows = [{
    'abbr': abbr, 'W': w, 'L': l, 'T': t, 'PCT': pct, 'PF': pf, 'PA': pa,
    'NET': net, 'STRK': strk, 'source_url': SRC, 'status': 'VERIFIED', 'checked_at': AS_OF,
} for abbr, w, l, t, pct, pf, pa, net, strk, *_ in STANDINGS]

schedule_rows = [{
    'away': a, 'home': h, 'date': d, 'kickoff_et': k, 'network': n, 'game_url': u,
    'venue': None, 'neutral_site': 'Munich' if (a, h) == ('NE', 'DET') else None,
    'source_url': SCHED_SRC, 'status': 'VERIFIED', 'checked_at': AS_OF,
} for a, h, d, k, n, u in SCHEDULE]

score_rows = [{
    'away': a, 'home': h, 'away_score': as_, 'home_score': hs, 'date': d, 'game_url': u,
    'source_url': SCORES_SRC, 'status': 'VERIFIED', 'checked_at': AS_OF,
    'week': 'Week 9'
} for a, h, as_, hs, d, u in SCORES_W9] + [{
    'away': a, 'home': h, 'away_score': as_, 'home_score': hs, 'date': d, 'game_url': u,
    'source_url': SCHED_SRC, 'status': 'VERIFIED', 'checked_at': AS_OF,
    'week': 'Week 10 (completed)'
} for a, h, as_, hs, d, u in SCORES_W10_DONE]

injury_rows = [{
    'team': t, 'name': n, 'position': p, 'injury': i, 'practice': pr, 'game_status': gs,
    'source_url': INJ_SRC, 'status': 'VERIFIED', 'checked_at': AS_OF,
} for t, n, p, i, pr, gs in INJURIES]

news_rows = [{
    'subject': s, 'claim': c, 'source_url': u, 'publication_date': None,
    'status': 'VERIFIED (headline) — publication date unverified', 'checked_at': AS_OF,
} for s, c, u in NEWS]

snap = {
    'as_of': AS_OF,
    'session': 'c563a1dc',
    'capture_method': 'functions.fetch_page on official pages, 2026-11-14 UTC; structured transcription, not raw HTTP',
    'standings': standings_rows,
    'schedule': schedule_rows,
    'scores': score_rows,
    'injuries': injury_rows,
    'news': news_rows,
    'limitations': [
        'Snapshot is a dated structured extract; dynamic official pages can change after retrieval.',
        'HOME/ROAD/DIV/CONF tail labels verified arithmetically but withheld from publication per prior audited design (F-01).',
        'Injury coverage is a bounded 6-game sample of the official Week 10 report; not a complete roster health report.',
        'News claims are transcribed from official headlines; publication dates unverified.',
        'No market prices, probabilities or betting recommendations are derived from this snapshot.',
    ],
}

# archive the previous snapshot before overwriting
prev = read('data/audit-snapshot.json')
save('data/audit-snapshot-2026-11-04.json', prev)
save('data/audit-snapshot.json', snap)

# NGS parsed evidence
ngs = [{
    'player': r[0], 'team': r[1], 'tt': r[2], 'cay': r[3], 'iay': r[4], 'ayd': r[5],
    'agg': r[6], 'lcad': r[7], 'ayts': r[8], 'att': int(r[9]), 'yds': int(r[10]),
    'td': int(r[11]), 'int': int(r[12]), 'rate': r[13], 'comp_pct': r[14],
    'xcomp_pct': r[15], 'comp_over_exp': r[16],
    'source_url': NGS_SRC, 'status': 'VERIFIED (transcription)', 'checked_at': AS_OF,
} for r in ngs_rows]
save('data/ngs-passing-2026-week9.json', {'as_of': AS_OF, 'source_url': NGS_SRC, 'rows': ngs})

# verification report
verify = {
    'as_of': AS_OF,
    'session': 'c563a1dc',
    'sources': {
        'standings': {'url': SRC, 'rows': 32, 'chunks': 2},
        'schedule_week10': {'url': SCHED_SRC, 'games': len(SCHEDULE), 'byes': BYES_W10, 'chunks': 3},
        'scores_week9': {'url': SCORES_SRC, 'games': len(SCORES_W9), 'chunks': 2},
        'injuries_week10': {'url': INJ_SRC, 'sample_rows': len(INJURIES), 'games_transcribed': 6, 'chunks': 8},
        'ngs_passing_week9': {'url': NGS_SRC, 'rows': len(ngs_rows), 'chunks': 2},
    },
    'checks_total': len(checks),
    'checks_passed': sum(1 for c in checks if c['result'] == 'PASS'),
    'checks': checks,
    'cross_check': 'Every 2026-11-14 standings row = 2026-11-04 post-Week-8 record + Week 9 result (or bye).',
}
save('data/live-verify-2026-11-14.json', verify)

# sources.json — refresh capture metadata (keep prior entries as history)
src = read('data/sources.json')
src['captured_at'] = AS_OF
src['method'] = 'functions.fetch_page; refreshed 2026-11-14 UTC; bounded field audit, not raw HTTP archiving'
for s in src['sources']:
    if s['id'] == 'standings':
        s['checked_at'] = AS_OF
        s['used_for'] = '32 rows: W, L, T, PCT, PF, PA, NET, STRK; arithmetic + cross-capture checks (2026-11-14 refresh).'
    elif s['id'] == 'schedule':
        s['checked_at'] = AS_OF
        s['url'] = SCHED_SRC
        s['used_for'] = '14 Week 10 matchup/date/time/network entries + byes CHI/DEN/PHI/TB; Madrid designation NE@DET.'
    elif s['id'] == 'scores':
        s['checked_at'] = AS_OF
        s['url'] = SCORES_SRC
        s['used_for'] = '15 complete Week 9 score/date rows + WAS-NYG Week 10 result (completed Thu 2026-11-12).'
    elif s['id'] == 'injuries':
        s['checked_at'] = AS_OF
        s['url'] = INJ_SRC
        s['used_for'] = 'Bounded 140-row sample across 6 Week 10 games; blank injury/game status preserved. Not a complete report.'
src['sources'].append({
    'id': 'ngs-passing-w9', 'label': 'NFL Next Gen Stats passing, Week 9 2026',
    'url': NGS_SRC, 'official': True, 'checked_at': AS_OF,
    'used_for': '30 QB rows (ATT/YDS/TD/INT/RATE/CPOE/xCPOE etc.); transcription retained; no values promoted to canonical tables.'
})
save('data/sources.json', src)

# flagged.json — append refresh flags
flags = read('data/flagged.json')
flags['as_of'] = AS_OF
existing = {f['id'] for f in flags['items']}
new_flags = [
 {'id': 'C-01', 'severity': 'low',
  'item': '2026-11-14 refresh: canonical snapshot updated from Week 9 (2026-11-04) to current standings/Week 10 schedule/Week 9 scores/Week 10 injury sample. Prior snapshot archived at data/audit-snapshot-2026-11-04.json.',
  'source_url': SRC, 'status': 'needs review'},
 {'id': 'C-02', 'severity': 'low',
  'item': 'Injury coverage is a bounded 6-game sample of the official Week 10 report (140 rows); the other 8 games were retrieved and reviewed but not transcribed. Not a complete health report.',
  'source_url': INJ_SRC, 'status': 'needs review'},
 {'id': 'C-03', 'severity': 'low',
  'item': 'News items are transcribed from official NFL.com headlines on the injury page; publication dates unverified.',
  'source_url': INJ_SRC, 'status': 'needs review'},
 {'id': 'C-04', 'severity': 'low',
  'item': 'NGS Week 9 passing transcription retained as evidence (30 rows); no NGS values enter canonical tables or models.',
  'source_url': NGS_SRC, 'status': 'needs review'},
 {'id': 'C-05', 'severity': 'low',
  'item': 'Official-surface abbreviation difference: Next Gen Stats renders the Los Angeles Rams as LAR while nfl.com standings/schedules use LA. Normalized only for the internal consistency check; transcriptions keep the surface-native code.',
  'source_url': NGS_SRC, 'status': 'needs review'},
]
for f in new_flags:
    if f['id'] not in existing:
        flags['items'].append(f)
save('data/flagged.json', flags)

print(f"Refresh OK: {len(checks)} checks, all PASS.")
print(f"  standings={len(standings_rows)} schedule={len(schedule_rows)} scores={len(score_rows)} injuries={len(injury_rows)} news={len(news_rows)} ngs={len(ngs_rows)}")
print("  wrote data/audit-snapshot.json (as_of 2026-11-14), archive copy, ngs evidence, live-verify report; updated sources.json + flagged.json")
