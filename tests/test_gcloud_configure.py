"""Unit tests for google_cloud_app/gcloud_configure.py.

Run: .venv/aw/bin/python -m pytest tests/test_gcloud_configure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from google_cloud_app import gcloud_configure  # noqa: E402


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_apply_settings_maps_field_names(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return FakeResult()

    monkeypatch.setattr(gcloud_configure.subprocess, "run", fake_run)
    applied = gcloud_configure.apply_settings(
        {
            "gcloud_project": "example-project",
            "gcloud_account": "svc@example.iam.gserviceaccount.com",
            "gcloud_compute_region": "southamerica-east1",
            "gcloud_compute_zone": "",
        }
    )
    assert applied == ["project", "account", "compute/region"]
    assert ["gcloud", "config", "set", "project", "example-project", "--quiet"] in calls


def test_apply_settings_skips_empty_values(monkeypatch):
    monkeypatch.setattr(gcloud_configure.subprocess, "run", lambda cmd, **kw: FakeResult())
    assert gcloud_configure.apply_settings({}) == []


def test_config_set_raises_on_failure(monkeypatch):
    monkeypatch.setattr(
        gcloud_configure.subprocess,
        "run",
        lambda cmd, **kw: FakeResult(returncode=1, stderr="boom"),
    )
    try:
        gcloud_configure.config_set("project", "example-project")
        assert False, "expected GcloudConfigureError"
    except gcloud_configure.GcloudConfigureError as e:
        assert "boom" in str(e)


def test_activate_service_account_writes_temp_key_and_deletes_it(monkeypatch):
    calls = []
    deleted = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return FakeResult()

    monkeypatch.setattr(gcloud_configure.subprocess, "run", fake_run)
    monkeypatch.setattr(gcloud_configure.os, "unlink", lambda path: deleted.append(path))
    email = gcloud_configure.activate_service_account(
        '{"client_email": "svc@example.iam.gserviceaccount.com", "private_key": "x"}'
    )
    assert email == "svc@example.iam.gserviceaccount.com"
    assert calls[0][0:4] == ["gcloud", "auth", "activate-service-account", email]
    assert deleted


def test_activate_service_account_rejects_invalid_json():
    try:
        gcloud_configure.activate_service_account("{bad")
        assert False, "expected GcloudConfigureError"
    except gcloud_configure.GcloudConfigureError as e:
        assert "invalid" in str(e)


def test_status_configured(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return FakeResult(stdout="{}")

    monkeypatch.setattr(
        gcloud_configure.subprocess,
        "run",
        fake_run,
    )
    result = gcloud_configure.status()
    assert result["configured"] is True
    assert calls == [
        ["gcloud", "config", "list", "--format=json"],
        ["gcloud", "auth", "list", "--format=json"],
    ]
