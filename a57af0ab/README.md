# a57af0ab — NFL review hub

Live page (after merge): https://sassnarep3-star.github.io/Own8/a57af0ab/

Contents (static HTML, no network calls at view time):

| Page | What it holds |
| --- | --- |
| `index.html` | Landing page with category cards |
| `executive-summary.html` | Key facts, what was not done, method |
| `injuries.html` | Official Week 10 (2026) injury report: 345 rows, 14 games, 28 teams, position-group counts |
| `questions.html` | 16 questions (have / missing / how to find it) and 4 decisions |
| `suggestions.html` | 14 proposed changes, awaiting selection. Nothing implemented. |
| `repo-review.html` | Repo irregularities and clean checks, each with evidence |
| `flagged.html` | Flagged for Review: items that need a human check, with source links |

Rebuild (Python 3.11+, standard library only):

```sh
python3 a57af0ab/parse_injuries.py   # raw transcription -> data/injuries-2026-w10.json
python3 a57af0ab/build.py            # JSON -> HTML pages
python3 a57af0ab/check.py            # links, source links per row, counts, blank cells
```

Rules used:
- Official sources only for NFL facts (nfl.com). Repo facts are checked with git.
- A value that cannot be confirmed from an official source is left blank and flagged. Nothing is inferred.
- Starter and backup status is blank: no official depth chart was found (see Questions Q01).
- The injury rows were transcribed once from the official page text. Structure and counts were checked by script; a second independent transcription has not been done (flag X-04).
- `data/raw/injury-w10-transcription.txt` is the row-by-row copy the JSON is built from.
