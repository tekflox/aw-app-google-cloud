"""Pure `gcloud` configuration helpers.

These functions apply stored AW app settings to the workspace's local gcloud
configuration without depending on the AW runtime, which keeps them easy to
unit-test with a mocked ``subprocess.run``.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

_FIELD_TO_GCLOUD_KEY = {
    "gcloud_project": "project",
    "gcloud_account": "account",
    "gcloud_compute_region": "compute/region",
    "gcloud_compute_zone": "compute/zone",
}


class GcloudConfigureError(RuntimeError):
    pass


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def config_set(key: str, value: str) -> None:
    """Runs `gcloud config set <key> <value> --quiet`."""
    result = _run(["gcloud", "config", "set", key, value, "--quiet"])
    if result.returncode != 0:
        raise GcloudConfigureError(f"gcloud config set {key} failed: {result.stderr.strip()}")


def activate_service_account(service_account_json: str) -> str:
    """Activates a service-account key JSON and returns its client email."""
    try:
        parsed = json.loads(service_account_json)
    except json.JSONDecodeError as e:
        raise GcloudConfigureError(f"service-account JSON is invalid: {e}") from e

    client_email = parsed.get("client_email")
    if not client_email:
        raise GcloudConfigureError("service-account JSON is missing client_email")

    fd, path = tempfile.mkstemp(prefix="aw-gcloud-sa-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(parsed, f)
        result = _run(
            [
                "gcloud",
                "auth",
                "activate-service-account",
                client_email,
                f"--key-file={path}",
                "--quiet",
            ]
        )
        if result.returncode != 0:
            raise GcloudConfigureError(
                f"gcloud auth activate-service-account failed: {result.stderr.strip()}"
            )
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    return client_email


def apply_settings(values: dict) -> list[str]:
    """Applies known settings present in ``values`` and returns what changed."""
    applied = []
    if values.get("gcloud_service_account_json"):
        activate_service_account(str(values["gcloud_service_account_json"]))
        applied.append("auth/service_account")

    for field, gcloud_key in _FIELD_TO_GCLOUD_KEY.items():
        value = values.get(field)
        if value:
            config_set(gcloud_key, str(value))
            applied.append(gcloud_key)
    return applied


def status() -> dict:
    """Returns local gcloud config/auth state without calling Google APIs."""
    config = _run(["gcloud", "config", "list", "--format=json"])
    accounts = _run(["gcloud", "auth", "list", "--format=json"])
    return {
        "configured": config.returncode == 0,
        "config_raw": config.stdout.strip() or config.stderr.strip(),
        "accounts_raw": accounts.stdout.strip() or accounts.stderr.strip(),
    }
