#!/usr/bin/env bash
# Report whether the development-e2e secrets are available.
#
# Required env vars (empty when the repo cannot see the secret):
#   DEV_E2E_API_KEY_FE_ADMIN, DEV_E2E_API_KEY_OTHER_USER,
#   DEVKIT_APP_ID, DEVKIT_APP_PRIVATE_KEY
# Optional: GITHUB_OUTPUT. When set, the script writes available=true|false to it.
# Always exits 0, so a missing secret skips the run instead of failing it.
set -uo pipefail

available=true
for name in DEV_E2E_API_KEY_FE_ADMIN DEV_E2E_API_KEY_OTHER_USER DEVKIT_APP_ID DEVKIT_APP_PRIVATE_KEY; do
  if [ -z "${!name:-}" ]; then
    echo "::notice::${name} is not available to this repo; skipping the development-e2e run."
    available=false
  fi
done

echo "available=${available}" >> "${GITHUB_OUTPUT:-/dev/stdout}"
