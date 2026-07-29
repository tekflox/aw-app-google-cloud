#!/usr/bin/env bash
# Standalone test — no framework runtime required. Run this INSIDE the
# aw-workspace container (as root) to prove the install script actually
# installs the Google Cloud CLI and that `gcloud version` works after.
#
# Usage (from inside the container, with this repo copied in):
#   bash tests/standalone_test.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== install_gcloud.sh =="
bash scripts/install_gcloud.sh

echo "== version =="
gcloud version

echo "== gcloud config list (expected: may be empty) =="
gcloud config list 2>&1 || true

echo "OK: gcloud cli installed and functional"
