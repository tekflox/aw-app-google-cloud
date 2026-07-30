# aw-app-google-cloud

AW workspace app that installs the **Google Cloud CLI** (`gcloud`)
into the workspace and provides a settings panel for Google Cloud defaults
and optional service-account JSON setup.

This mirrors [`aw-app-aws`](https://github.com/tekflox/aw-app-aws)'s shape:
an in-process app with `commands:install`, `routes:register`, `secrets:own`,
and focused tests around a framework-free configure helper.

## Layout

- `aw-app.json` — the manifest (id `google-cloud`, tier `inprocess`).
- `schemas/aw-app.schema.json` — local structural validator.
- `scripts/install_gcloud.sh` — idempotent installer using Google's official
  apt repository (`packages.cloud.google.com`) and package
  `google-cloud-cli`.
- `scripts/uninstall.sh` — removes `google-cloud-cli` through apt.
- `google_cloud_app/plugin.py` — `GoogleCloudAppPlugin` entrypoint;
  `activate(ctx)` installs the CLI via `ctx.commands`, applies already-stored
  settings via `ctx.secrets` + `gcloud_configure`, and mounts
  `POST /api/apps/google-cloud/settings`, `GET /api/apps/google-cloud/status`,
  and `POST /api/apps/google-cloud/logout`.
- `google_cloud_app/gcloud_configure.py` — pure subprocess wrappers for
  `gcloud config set`, `gcloud auth activate-service-account`, and local
  status reads.
- `tests/validate_manifest.py` — validates `aw-app.json` against the schema
  and checks referenced installer scripts exist.
- `tests/test_gcloud_configure.py` — unit tests for the configure helper.
- `tests/test_plugin_routes.py` — route tests through a real FastAPI
  `TestClient` with a fake `ctx`.
- `tests/standalone_test.sh` — installs the Google Cloud CLI for real and
  checks `gcloud version`; run inside the aw-workspace container.

## Configuration

`config_schema` in `aw-app.json` declares these fields:

- `gcloud_project` — default project (`gcloud config set project`).
- `gcloud_account` — default account (`gcloud config set account`).
- `gcloud_compute_region` — default Compute Engine region.
- `gcloud_compute_zone` — default Compute Engine zone.
- `gcloud_service_account_json` — optional service-account key JSON
  (`x-secret`, stored in the zero-knowledge secret store, activated with
  `gcloud auth activate-service-account`).

`POST /api/apps/google-cloud/settings` accepts any subset of these fields,
writes them to `ctx.secrets`, and applies them immediately. `activate()`
re-applies stored settings on every boot/reconcile pass so configuration
survives workspace recreation.

Interactive user OAuth is intentionally not automated here. Run
`gcloud auth login` or `gcloud auth application-default login` manually inside
the workspace when a human account flow is required.

## Tests

```bash
.venv/aw/bin/python tests/validate_manifest.py
.venv/aw/bin/python -m pytest tests/test_gcloud_configure.py tests/test_plugin_routes.py
```

## Out of scope

- No nav/window entry — this is an install-a-CLI + settings app.
- No production workspace installation — the orchestrator installs and
  validates (`gcloud version`, `gcloud config list`) after the repo lands.
- No local auth revocation on logout — logout drops stored AW settings only.
