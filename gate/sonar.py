"""Fail the pipeline unless the SonarQube quality gate for a project is OK."""
import base64
import json
import os
import sys
import urllib.parse
import urllib.request


def gate_status(base_url, project_key, token):
    url = f"{base_url}/api/qualitygates/project_status?projectKey={urllib.parse.quote(project_key)}"
    # SonarQube takes the token as the basic-auth user with an empty password.
    auth = base64.b64encode(f"{token}:".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)["projectStatus"]
    failed = [c["metricKey"] for c in data.get("conditions", []) if c["status"] == "ERROR"]
    return data["status"], failed


def main(argv):
    if len(argv) != 3:
        sys.exit("usage: python -m gate.sonar BASE_URL PROJECT_KEY   (token in SONAR_TOKEN)")
    status, failed = gate_status(argv[1], argv[2], os.environ["SONAR_TOKEN"])
    print(status, ", ".join(failed))
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
