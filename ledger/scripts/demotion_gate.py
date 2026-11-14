"""Demotion gate: sends a LIVE strategy back to PAPER when a rule in data/demotion-rules.json fires.

Fail-closed by construction: a missing value, a null gate or a missing evidence window is a failure
for a LIVE strategy. PAPER and BLOCKED strategies are never changed by this gate.
Standard library only. Run from the repository root:

    python3 ledger/scripts/demotion_gate.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.dirname(HERE)
RULES_PATH = os.path.join(LEDGER, "data", "demotion-rules.json")
REGISTRY_PATH = os.path.join(LEDGER, "data", "strategy-registry.json")
OUT_PATH = os.path.join(LEDGER, "results", "demotion-decisions.json")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate(strategy, rules):
    """Return a decision for one strategy. Only status LIVE can be demoted."""
    sid = strategy.get("id")
    status = strategy.get("status")
    if status != "LIVE":
        return {"id": sid, "status_before": status, "status_after": status, "action": "NO_ACTION",
                "reasons": [],
                "note": "Not LIVE. This gate never changes PAPER or BLOCKED strategies."}
    reasons = []
    gates = strategy.get("gates") or {}
    applicable = rules["applicability"][strategy["applicability_key"]]
    if gates.get("G1") is not True:
        reasons.append("D1 provenance: G1 is %r" % (gates.get("G1"),))
    if gates.get("G8") is not True:
        reasons.append("D2 market dependence: G8 is %r" % (gates.get("G8"),))
    failed = [g for g in applicable if gates.get(g) is not True]
    if failed:
        reasons.append("D3 applicable gate(s) not passed (null counts as fail): " + ", ".join(failed))
    win = strategy.get("live_window")
    if win is None:
        reasons.append("D4 no live evidence window exists (fail-closed)")
    else:
        minimum = rules["minimum_live_window_games"][strategy["sample_rule"]]
        n = win.get("n")
        if n is None or n < minimum:
            reasons.append("D4 live window n=%r is below the minimum %d" % (n, minimum))
        lcb = win.get("skill_pct_lcb")
        if lcb is None or lcb < 0:
            reasons.append("D5 skill_pct_lcb is %r (must be >= 0)" % (lcb,))
        p = win.get("p_holm")
        if p is None or p >= 0.05:
            reasons.append("D6 Holm-adjusted p is %r (must be < 0.05)" % (p,))
        h1, h2 = win.get("half1_diff"), win.get("half2_diff")
        if h1 is None or h2 is None or h1 >= 0 or h2 >= 0:
            reasons.append("D7 halves not both improving: half1=%r half2=%r" % (h1, h2))
        age = win.get("days_since_last_official_result")
        if age is None or age > 14:
            reasons.append("D8 days since last official result is %r (must be <= 14)" % (age,))
    if reasons:
        return {"id": sid, "status_before": "LIVE", "status_after": "PAPER", "action": "DEMOTE_TO_PAPER",
                "reasons": reasons}
    return {"id": sid, "status_before": "LIVE", "status_after": "LIVE", "action": "KEEP_LIVE", "reasons": []}


def run(registry, rules):
    decisions = [evaluate(s, rules) for s in registry["strategies"]]
    counts = {}
    for d in decisions:
        counts[d["action"]] = counts.get(d["action"], 0) + 1
    return {
        "rules_file": "ledger/data/demotion-rules.json",
        "strategies_evaluated": len(decisions),
        "live_strategies": sum(1 for s in registry["strategies"] if s.get("status") == "LIVE"),
        "action_counts": counts,
        "decisions": decisions,
    }


def main():
    registry = load_json(REGISTRY_PATH)
    result = run(registry, load_json(RULES_PATH))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("demotion gate: %d strategies, %d LIVE, actions %s" % (
        result["strategies_evaluated"], result["live_strategies"], result["action_counts"]))


if __name__ == "__main__":
    main()
