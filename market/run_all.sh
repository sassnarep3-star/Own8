#!/usr/bin/env bash
# Rebuild every market artefact from the stored raw captures and the official log.
# Exits non-zero if any step fails, if any verification check fails, or if any link,
# row or source invariant in the generated pages is broken.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=market

python3 -m scripts.grade
python3 -m scripts.tournament
python3 -m scripts.model
python3 market/scripts/analyze.py
python3 market/scripts/verify.py
python3 market/scripts/crawl.py
python3 market/scripts/decide.py
python3 market/scripts/build_market_site.py
python3 market/scripts/check_market.py
echo "market: all artefacts rebuilt and checked"
