# Google Cloud CLI

Google Cloud CLI adds Google Cloud command-line access to an AW Workspace. It installs `gcloud` and provides settings for project, account, region, zone, and optional service-account credentials.

## What It Does

- Installs the `gcloud` command in the workspace.
- Saves default Google Cloud settings.
- Supports service-account JSON for non-interactive authentication.
- Applies configuration so terminal sessions can use Google Cloud commands.

## Why Use It

Use this app when a workspace needs to inspect, deploy, or manage Google Cloud resources. It is useful for project setup, Compute Engine work, Cloud Run deployments, storage operations, and other workflows that depend on the official Google Cloud CLI.

## How To Use It

Install the app, open its settings, and enter the Google Cloud defaults or service-account credentials you want the workspace to use. After that, open a workspace terminal and run `gcloud` commands normally.

## What It Delivers

The app gives AW Workspace a ready Google Cloud command-line environment. Users and agents can perform cloud operations without reinstalling tools or re-entering configuration every time.
