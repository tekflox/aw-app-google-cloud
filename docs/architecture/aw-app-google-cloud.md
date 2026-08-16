---
repo: architecture
path: docs/architecture/aw-app-google-cloud.md
source: generated
edited: false
checksum: sha256:122cd8b87233070d88b3d9e5fb29f252bea7b132c2af472ffcb474f08589deec
---
# Google Cloud CLI

- **repo**: aw-app-google-cloud
- **layer**: app
- **technologies**: python
- **health** (derived): planned

Installs the Google Cloud CLI (`gcloud`) into the workspace and provides a settings panel for project/account defaults and optional service-account JSON setup.

## Connections
- `http` → **aw-workspace** — routes mounted at /api/apps/google-cloud

## MCP tools
_none exposed_

## Requirements
_none documented_
