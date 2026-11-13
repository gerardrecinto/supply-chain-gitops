# supply-chain-gitops

A release gate and GitOps layout for artifacts: block on fixable vulnerabilities, bad licenses, and brand-new packages, check the SonarQube quality gate, guard feature flag rollouts, and deploy by digest through Argo CD.

| Piece | Files |
|---|---|
| Release gate (SBOM and scan policy) | `gate/policy.py` reads a CycloneDX SBOM and a scan report (Xray, Trivy, or the same fields). Blocks fixable high and critical findings, denied licenses, unpinned components, and versions published in the last 7 days (the rule JFrog Curation enforces at the proxy) |
| SonarQube | `gate/sonar.py` fails the build unless the project quality gate is OK |
| LaunchDarkly | `flags/validate.py` checks a rollout plan: owner, kill switch, staging first, production starts at 1 or 5 percent and never goes backwards |
| JFrog | `jfrog/xray-policy.json`, `scripts/promote.sh` (build scan, then promote to the prod repo) |
| GitOps, Argo CD | `gitops/` Kustomize base and dev/prod overlays, `argocd/applicationset.yaml` (dev auto-syncs, prod waits for a person). Prod pins an image digest, never a tag |
| CI | `ci/azure-pipelines.yml`, `ci/harness-pipeline.yaml` (with an approval stage), `.github/workflows/ci.yml` |
| Azure and GCP | `terraform/main.tf`: Azure Container Registry and GCP Artifact Registry |
| Admin scripts | `scripts/host-audit.sh` (Linux), `scripts/runner-audit.ps1` (Windows build agents) |

```bash
python -m pytest -q tests
python -m gate.policy sbom.json findings.json     # the sample is blocked on purpose
kubectl kustomize gitops/overlays/prod
```

## Verified
- 6 pytest tests pass: the policy rules, the flag guardrails, and the SonarQube client against a local stub server.
- The sample SBOM is blocked (exit 1) for a fixable high CVE, a denied license, and a too-new package.
- Both Kustomize overlays render, and prod renders the image as `@sha256:`. YAML and JSON files parse. `shellcheck` is clean. `terraform fmt` is clean.

## Not verified
- No JFrog, SonarQube, LaunchDarkly, Harness, Argo CD, or Azure DevOps instance was available. The Xray policy JSON, `jf` commands, Harness YAML, and the ApplicationSet were written from the product docs and not applied. `gate/sonar.py` was tested only against a stub of the API.
- `terraform validate` was not run. `runner-audit.ps1` was not run (no PowerShell here). `host-audit.sh` was not run against a real host.
- The digest in the prod overlay is a placeholder. The CI job that writes the real one is not included.
