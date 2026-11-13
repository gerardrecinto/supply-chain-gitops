#!/usr/bin/env bash
# Promote a build from the staging repo to prod only if Xray has no blocking violations.
# Usage: promote.sh JFROG_URL BUILD_NAME BUILD_NUMBER   (token in JFROG_ACCESS_TOKEN)
set -euo pipefail
url="$1" name="$2" number="$3"

jf build-scan "$name" "$number" --url "$url" --access-token "$JFROG_ACCESS_TOKEN" --fail=true
jf rt build-promote "$name" "$number" app-prod-local \
  --url "$url" --access-token "$JFROG_ACCESS_TOKEN" --status released --comment "gates passed"
