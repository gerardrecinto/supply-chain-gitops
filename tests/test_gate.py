import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from flags.validate import problems
from gate.policy import evaluate
from gate.sonar import gate_status

NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)


def comp(purl, lic=None, pub=None):
    c = {"purl": purl, "licenses": [{"license": {"id": lic}}] if lic else []}
    if pub:
        c["published"] = pub
    return c


def rules(sbom, findings=(), **kw):
    return [r for r, _, _ in evaluate({"components": sbom}, list(findings), NOW, **kw)]


def test_clean_sbom_passes():
    assert rules([comp("pkg:maven/a/b@1.0", "MIT")]) == []


def test_fixable_critical_blocks_but_unfixed_does_not():
    f = {"component": "pkg:maven/a/b@1.0", "cve": "CVE-1", "severity": "Critical", "fixed_version": "1.1"}
    assert rules([comp("pkg:maven/a/b@1.0")], [f]) == ["vuln-fixable"]
    f["fixed_version"] = None
    assert rules([comp("pkg:maven/a/b@1.0")], [f]) == []


def test_denied_license_and_unpinned():
    assert rules([comp("pkg:npm/x@1", "AGPL-3.0")]) == ["license"]
    assert rules([comp("pkg:npm/x")]) == ["unpinned"]


def test_curation_blocks_a_version_published_two_days_ago():
    assert rules([comp("pkg:npm/x@2", pub="2026-11-11T00:00:00Z")]) == ["curation-too-new"]
    assert rules([comp("pkg:npm/x@2", pub="2026-11-11T00:00:00Z")], allow_new={"pkg:npm/x@2"}) == []
    assert rules([comp("pkg:npm/x@2", pub="2026-10-01T00:00:00Z")]) == []


def test_flag_plan_guardrails():
    ok = {"owner": "team", "kill_switch": True,
          "stages": [{"env": "staging", "percent": 100}, {"env": "production", "percent": 5},
                     {"env": "production", "percent": 25}]}
    assert problems(ok) == []
    bad = {"owner": "", "kill_switch": False, "stages": [{"env": "production", "percent": 50}]}
    assert len(problems(bad)) == 4  # owner, kill switch, start too high, no staging


def test_sonar_gate_reads_failed_conditions():
    body = {"projectStatus": {"status": "ERROR", "conditions": [
        {"metricKey": "new_coverage", "status": "ERROR"}, {"metricKey": "new_bugs", "status": "OK"}]}}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.headers["Authorization"].startswith("Basic ")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    status, failed = gate_status(f"http://127.0.0.1:{srv.server_port}", "my:proj", "tok")
    srv.shutdown()
    assert (status, failed) == ("ERROR", ["new_coverage"])
