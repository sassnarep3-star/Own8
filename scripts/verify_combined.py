#!/usr/bin/env python3
"""Compatibility entrypoint. Old cross-capture agreement was not source proof."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('audit_repo.py')),run_name='__main__')
