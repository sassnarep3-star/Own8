# Own8 category site

Built by `python3 site/scripts/content.py` (registers) and `python3 site/scripts/build.py` (HTML). Checked by `python3 site/check.py`.

- Inputs: `site/data/*.json` (verified captures and registers) and read-only repo artifacts (`ledger/`, `origination/`, `requirements/`, `market/`).
- Model baseline B0 and its grading: `site/scripts/model_b0.py`. Week 11 fair lines frozen at commit beca9d2.
- Every table row has a source link. Values that cannot be confirmed are marked UNVERIFIED and left blank.
- Paper research only. No real-money betting, stakes or rewards.

## Official captures (added 2026-11-18, session 2e1f91d7)

Raw official text is stored in `data/captures/` with a SHA-256 manifest. Each capture is fetch-tool text copied into a file (shell curl to nfl.com fails with a TLS error in this sandbox), so the hash proves the stored file is unchanged, not that it equals nfl.com server bytes.

```sh
python3 site/scripts/captures.py   # parse captures to JSON and refresh manifest.json
python3 site/scripts/build.py      # build the pages
python3 site/check.py              # links, row sources, sha256 manifest, capture-to-JSON drift
```
