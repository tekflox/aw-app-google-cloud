"""
Entrypoint referenced by aw-app.json's runtime.entrypoint
("google_cloud_app.plugin:GoogleCloudAppPlugin").

Plugs into the real F4 framework runtime and uses the gated ``ctx`` facades
rather than raw shell:

* ``ctx.commands`` (``commands:install``) — install the `gcloud` CLI THROUGH the
  facade (journaled; reverted on uninstall via scripts/uninstall.sh).
* ``ctx.secrets`` (``secrets:own``) — Google Cloud defaults and optional
  service-account JSON live in the workspace-side secure store; the app
  applies them via `gcloud config set` / `gcloud auth activate-service-account`
  on activate, and the settings route writes + re-applies them.
* ``ctx.routes`` (``routes:register``) — a small settings sub-app to save
  configuration + read status.
"""

from __future__ import annotations

import json
import logging
import os

from . import gcloud_configure

log = logging.getLogger("aw_apps.google_cloud")

_CONFIG_FIELDS = (
    "gcloud_project",
    "gcloud_account",
    "gcloud_compute_region",
    "gcloud_compute_zone",
    "gcloud_service_account_json",
)


def _stored_settings(ctx) -> dict:
    return {field: ctx.secrets.read(field) for field in _CONFIG_FIELDS if ctx.secrets.read(field)}


class GoogleCloudAppPlugin:
    async def activate(self, ctx) -> None:
        self.ctx = ctx
        with open(os.path.join(ctx.package_dir, "aw-app.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        for cli in manifest.get("contributes", {}).get("system_clis", []):
            ctx.commands.install_system_cli(
                cli["name"], cli["installer"], uninstall="scripts/uninstall.sh"
            )
        log.info("aw-app-google-cloud activated: gcloud cli installed")

        # If settings are already stored, apply them now — this also runs
        # on every reconcile pass after workspace recreation.
        stored = _stored_settings(ctx)
        if stored:
            try:
                applied = gcloud_configure.apply_settings(stored)
                log.info("gcloud configure: applied %s from stored settings", applied)
            except gcloud_configure.GcloudConfigureError as e:
                log.warning("gcloud configure: failed to apply stored settings: %s", e)

        ctx.routes.register(self._build_routes(ctx))

    async def deactivate(self) -> None:
        # gcloud cli removal is driven by the framework's journal reverse-replay
        # (scripts/uninstall.sh); the secret namespace is purged by the runtime.
        log.info("aw-app-google-cloud deactivated")

    def _build_routes(self, ctx):
        from fastapi import Body, FastAPI

        api = FastAPI()

        @api.post("/settings")
        async def save_settings(data: dict = Body(...)):
            """Generic config-window submit (the framework's Apps view posts
            here). Routes the `x-secret` service-account JSON and plain
            gcloud defaults to the secret store, then applies whichever
            fields were given via `gcloud config set` / auth activation. Fields are all
            optional so a partial save (e.g. only the region) works."""
            values = {field: data[field] for field in _CONFIG_FIELDS if data.get(field)}
            if not values:
                return {"ok": True, "applied": []}
            for field, value in values.items():
                ctx.secrets.write(field, value)
            try:
                applied = gcloud_configure.apply_settings(values)
                return {"ok": True, "applied": applied}
            except gcloud_configure.GcloudConfigureError as e:
                return {"ok": True, "applied": [], "error": str(e)}

        @api.get("/status")
        async def status():
            has_service_account = "gcloud_service_account_json" in ctx.secrets.keys()
            gcloud_status = gcloud_configure.status()
            return {
                "has_service_account": has_service_account,
                "project": ctx.secrets.read("gcloud_project"),
                "account": ctx.secrets.read("gcloud_account"),
                "region": ctx.secrets.read("gcloud_compute_region"),
                "zone": ctx.secrets.read("gcloud_compute_zone"),
                **gcloud_status,
            }

        @api.post("/logout")
        async def logout():
            """Drops the stored settings. Does not revoke gcloud auth locally;
            a fresh apply on the next activate/reconcile would just re-write
            config if secrets remained, and account revocation is out of scope
            for this route."""
            for field in _CONFIG_FIELDS:
                ctx.secrets.delete(field)
            return {"ok": True}

        return api
