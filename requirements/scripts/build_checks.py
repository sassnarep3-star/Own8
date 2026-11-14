#!/usr/bin/env python3
"""Merge every check family into one results file, so no script can silently erase another's checks.

Run order is fixed and enforced here: the capture checks must exist, then the availability checks.
The merged file carries a per-family count so a reviewer can see that nothing went missing.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

capture = json.load(open(os.path.join(RES, "checks-capture.json"), encoding="utf-8"))
avail = json.load(open(os.path.join(RES, "checks-availability.json"), encoding="utf-8"))

families = [("capture, reconciliation and out-of-sample grading", capture["checks"]),
            ("availability register and luck decomposition", avail["checks"])]
checks = [c for _, cs in families for c in cs]
summary = dict(capture["summary"])
summary.update(
    checks_total=len(checks),
    checks_failed=sum(1 for c in checks if not c["pass"]),
    families={name: dict(total=len(cs), failed=sum(1 for c in cs if not c["pass"])) for name, cs in families},
)
with open(os.path.join(RES, "checks.json"), "w", encoding="utf-8") as fh:
    json.dump(dict(summary=summary, checks=checks), fh, indent=1, ensure_ascii=False)
    fh.write("\n")
print(json.dumps({k: v for k, v in summary.items() if k != "families"}, indent=1))
print(json.dumps(summary["families"], indent=1))
raise SystemExit(1 if summary["checks_failed"] else 0)
