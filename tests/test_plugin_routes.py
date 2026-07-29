"""End-to-end test of the /settings + /status + /logout routes through a real
FastAPI TestClient, with gcloud_configure.config_set/status monkeypatched (no
real `gcloud` binary needed) and a minimal fake ``ctx`` (secrets facade only -
the piece the routes actually touch).

Run: .venv/aw/bin/python -m pytest tests/test_plugin_routes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from google_cloud_app import gcloud_configure, plugin  # noqa: E402


class FakeSecrets:
    def __init__(self):
        self.store: dict[str, str] = {}

    def read(self, key):
        return self.store.get(key)

    def write(self, key, value):
        self.store[key] = value
        return {"key": key, "written": True}

    def delete(self, key):
        removed = key in self.store
        self.store.pop(key, None)
        return {"key": key, "deleted": removed}

    def keys(self):
        return list(self.store)


class FakeCtx:
    def __init__(self):
        self.secrets = FakeSecrets()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(gcloud_configure, "config_set", lambda key, value: None)
    monkeypatch.setattr(gcloud_configure, "activate_service_account", lambda data: "svc@example")
    ctx = FakeCtx()
    app = plugin.GoogleCloudAppPlugin()
    api = app._build_routes(ctx)
    return TestClient(api), ctx


def test_save_settings_writes_secrets_and_applies(client, monkeypatch):
    tc, ctx = client
    applied = []
    monkeypatch.setattr(
        gcloud_configure,
        "config_set",
        lambda key, value: applied.append((key, value)),
    )
    resp = tc.post(
        "/settings",
        json={
            "gcloud_project": "example-project",
            "gcloud_account": "svc@example.iam.gserviceaccount.com",
            "gcloud_compute_region": "southamerica-east1",
        },
    )
    body = resp.json()
    assert body["ok"] is True
    assert sorted(body["applied"]) == ["account", "compute/region", "project"]
    assert ctx.secrets.read("gcloud_project") == "example-project"
    assert ctx.secrets.read("gcloud_account") == "svc@example.iam.gserviceaccount.com"
    assert ctx.secrets.read("gcloud_compute_region") == "southamerica-east1"
    assert ("project", "example-project") in applied


def test_save_settings_partial_field_only(client, monkeypatch):
    tc, ctx = client
    applied = []
    monkeypatch.setattr(
        gcloud_configure,
        "config_set",
        lambda key, value: applied.append((key, value)),
    )
    resp = tc.post("/settings", json={"gcloud_compute_region": "us-central1"})
    body = resp.json()
    assert body["ok"] is True
    assert body["applied"] == ["compute/region"]
    assert ctx.secrets.read("gcloud_compute_region") == "us-central1"


def test_save_settings_no_fields_is_noop(client):
    tc, _ = client
    resp = tc.post("/settings", json={})
    assert resp.json() == {"ok": True, "applied": []}


def test_save_settings_configure_error_surfaces(client, monkeypatch):
    tc, _ = client

    def raise_error(key, value):
        raise gcloud_configure.GcloudConfigureError("gcloud config set failed: boom")

    monkeypatch.setattr(gcloud_configure, "config_set", raise_error)
    resp = tc.post("/settings", json={"gcloud_project": "example-project"})
    body = resp.json()
    assert body["ok"] is True
    assert body["applied"] == []
    assert "boom" in body["error"]


def test_status_reports_configured_state(client, monkeypatch):
    tc, ctx = client
    ctx.secrets.write("gcloud_service_account_json", "{}")
    ctx.secrets.write("gcloud_project", "example-project")
    ctx.secrets.write("gcloud_compute_region", "southamerica-east1")
    monkeypatch.setattr(
        gcloud_configure, "status", lambda: {"configured": True, "config_raw": "{}", "accounts_raw": "[]"}
    )
    resp = tc.get("/status")
    body = resp.json()
    assert body["has_service_account"] is True
    assert body["project"] == "example-project"
    assert body["region"] == "southamerica-east1"
    assert body["configured"] is True


def test_status_reports_unconfigured_when_no_secrets(client, monkeypatch):
    tc, _ = client
    monkeypatch.setattr(
        gcloud_configure,
        "status",
        lambda: {"configured": False, "config_raw": "<not set>", "accounts_raw": "[]"},
    )
    resp = tc.get("/status")
    body = resp.json()
    assert body["has_service_account"] is False
    assert body["configured"] is False


def test_logout_clears_stored_credentials(client):
    tc, ctx = client
    ctx.secrets.write("gcloud_project", "example-project")
    ctx.secrets.write("gcloud_service_account_json", "{}")
    resp = tc.post("/logout")
    assert resp.json() == {"ok": True}
    assert "gcloud_project" not in ctx.secrets.keys()
    assert "gcloud_service_account_json" not in ctx.secrets.keys()
