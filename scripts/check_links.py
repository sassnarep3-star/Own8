#!/usr/bin/env python3
"""Canonical compatibility entrypoint for the strict local link/source-row checker."""
from strict_check import check
if __name__=='__main__':raise SystemExit(0 if check()['status']=='PASS' else 1)
