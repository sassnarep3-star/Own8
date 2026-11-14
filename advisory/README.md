# advisory/ — decision hub (session d6bada32)

Static pages that summarise what is known and unknown about the NFL Own8 project, list the
suggestions awaiting the owner's choice, and record flags and sources.

| Page | What it is |
| --- | --- |
| `index.html` | Executive summary and status table |
| `suggestions.html` | Suggestions with options and a recommendation. Nothing is implemented until chosen. |
| `questions.html` | Questions, what is known (with sources), what is missing, how to find out |
| `flagged.html` | Flagged for Review: stale data, conflicts, anomalies, legal flags |
| `sources.html` | Every source, how it was read, and what it supports |

## Rebuild and check

```
python3 injury-depth/build.py     # regenerates injury-depth/data/*.json and index.html
python3 advisory/build.py         # regenerates the five pages above
python3 advisory/check_links.py   # local links, anchors, https allowlist, every table row has a source link
```

Stdlib only. The page content is written in `advisory/build.py`; the Week 10 rows are transcribed in
`injury-depth/data/w10_transcription.tsv`.

## Rules these pages follow

- Official sources only for NFL facts (nfl.com) and for law (the Singapore regulator, gra.gov.sg).
- Repo files and GitHub pages are cited as internal evidence, never as official data.
- Third-party pages (for example depth-chart or odds sites) are not used as evidence.
- A value that cannot be confirmed is left blank and marked UNVERIFIED.
- Not betting advice. Research only.
