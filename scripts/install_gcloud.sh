#!/usr/bin/env bash
# Installs the Google Cloud CLI from Google's official apt repository.
# Idempotent: safe to re-run on install and on every reconcile pass after a
# workspace recreation.
#
# Every privileged step goes through sudo: the workspace container's default
# user is unprivileged `ubuntu` (uid 1001) with NOPASSWD sudo baked into the
# image. Without it this failed on EVERY boot with "Could not open lock file
# /var/lib/apt/lists/lock - open (13: Permission denied)", so gcloud was never
# actually installed. Note the redirections too — `sudo cmd > /root/file` still
# opens the file as the *calling* user, hence `sudo tee` for both writes.
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
sudo -n apt-get update -qq
sudo -n apt-get install -y --no-install-recommends apt-transport-https ca-certificates curl gnupg

sudo -n install -d -m 0755 /usr/share/keyrings
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | gpg --dearmor \
  | sudo -n tee /usr/share/keyrings/cloud.google.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo -n tee /etc/apt/sources.list.d/google-cloud-sdk.list >/dev/null

sudo -n apt-get update -qq
sudo -n apt-get install -y --no-install-recommends google-cloud-cli

gcloud version
