#!/usr/bin/env bash
# Installs the Google Cloud CLI from Google's official apt repository.
# Idempotent: safe to re-run on install and on every reconcile pass after a
# workspace recreation.
set -euo pipefail

if command -v gcloud >/dev/null 2>&1; then
  echo "gcloud already installed: $(gcloud version | head -n 1)"
  exit 0
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "install_gcloud.sh: no apt-get on this system - unsupported base image" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends apt-transport-https ca-certificates curl gnupg

install -d -m 0755 /usr/share/keyrings
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  > /etc/apt/sources.list.d/google-cloud-sdk.list

apt-get update -qq
apt-get install -y --no-install-recommends google-cloud-cli

gcloud version
