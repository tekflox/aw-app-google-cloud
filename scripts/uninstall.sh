#!/usr/bin/env bash
# Reverses install_gcloud.sh. Called on app uninstall (journal replay per the
# ADR's Decision 7 — this script IS the revert action for the commands:install
# journal entry).
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  apt-get remove -y google-cloud-cli || true
fi
