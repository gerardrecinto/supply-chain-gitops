"""Release gate: decide from an SBOM and a scan report whether an artifact may ship.

Inputs are plain JSON. The SBOM is CycloneDX (components with purl, version, licenses, and an
optional published date). The scan report is a list of findings with the component purl, cve,
severity, and fixed_version, the same fields Xray and Trivy both export.
"""
import json
import sys
from datetime import datetime, timedelta, timezone

DENY_LICENSES = {"AGPL-3.0", "GPL-3.0", "SSPL-1.0"}
BLOCK_SEVERITIES = {"critical", "high"}
MIN_AGE_DAYS = 7  # curation: do not pull a version published in the last week


def components(sbom):
    return {c["purl"]: c for c in sbom.get("components", [])}


def evaluate(sbom, findings, now, allow_new=()):
    """Return a list of (rule, purl, detail). Empty means the artifact may ship."""
    comps = components(sbom)
    out = []
    for f in findings:
        if f["severity"].lower() in BLOCK_SEVERITIES and f.get("fixed_version"):
            out.append(("vuln-fixable", f["component"], f"{f['cve']} fixed in {f['fixed_version']}"))
    for purl, c in comps.items():
        for lic in c.get("licenses", []):
            lid = lic.get("license", {}).get("id")
            if lid in DENY_LICENSES:
                out.append(("license", purl, lid))
        pub = c.get("published")
        if pub and purl not in allow_new:
            age = now - datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if age < timedelta(days=MIN_AGE_DAYS):
                out.append(("curation-too-new", purl, f"published {age.days}d ago"))
        if "@" not in purl:
            out.append(("unpinned", purl, "no version"))
    return out


def main(argv):
    if len(argv) != 3:
        sys.exit("usage: python -m gate.policy sbom.json findings.json")
    with open(argv[1]) as a, open(argv[2]) as b:
        problems = evaluate(json.load(a), json.load(b), datetime.now(timezone.utc))
    for rule, purl, detail in problems:
        print(f"BLOCK {rule:17} {purl} {detail}")
    print("blocked" if problems else "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
