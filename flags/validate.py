"""Guardrails for a feature flag rollout plan before it is applied in LaunchDarkly.

A plan is JSON: {"key", "owner", "kill_switch": true, "stages": [{"env", "percent"}]}.
"""
import json
import sys

ALLOWED_STEPS = [1, 5, 25, 50, 100]


def problems(plan):
    out = []
    if not plan.get("owner"):
        out.append("no owner")
    if not plan.get("kill_switch"):
        out.append("no kill switch: a flag must be switchable off without a deploy")
    stages = plan.get("stages", [])
    prod = [s["percent"] for s in stages if s["env"] == "production"]
    if prod and prod[0] not in ALLOWED_STEPS[:2]:
        out.append(f"production starts at {prod[0]} percent, start at 1 or 5")
    if prod != sorted(prod):
        out.append("production percentages go backwards")
    for p in prod:
        if p not in ALLOWED_STEPS:
            out.append(f"{p} is not one of {ALLOWED_STEPS}")
    if prod and "staging" not in [s["env"] for s in stages]:
        out.append("production rollout without a staging stage")
    return out


def main(argv):
    found = problems(json.load(open(argv[1])))
    for p in found:
        print("FAIL", p)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
