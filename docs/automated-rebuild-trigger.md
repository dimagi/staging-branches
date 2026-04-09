# Automated Rebuild Trigger

This document covers how the automated staging rebuild trigger works and how to maintain it.

## Overview

There are two triggers that keep `autostaging` up to date:

1. **This repo** — `.github/workflows/trigger-commcare-hq-rebuild.yml` fires on pushes to `main` that modify `commcare-hq-staging.yml`. It triggers `rebuild-staging` in `dimagi/commcare-hq` via `workflow_dispatch`.
2. **commcare-hq** — The [`rebuild-staging` workflow](https://github.com/dimagi/commcare-hq/blob/master/.github/workflows/rebuild-staging.yml) fires on push to any branch. A `check-branch` job fetches `commcare-hq-staging.yml` and skips the rebuild if the pushed branch isn't listed. This covers pushes to `master` (the base branch) and pushes to branches already in the config. A global concurrency group with `cancel-in-progress: false` ensures at most one rebuild runs at a time, with one queued.

## How it works

1. GitHub detects a push to `main` that changes `commcare-hq-staging.yml`
2. The workflow uses [`actions/create-github-app-token`](https://github.com/actions/create-github-app-token) to mint a short-lived token from the **Staging Branches Automations** GitHub App
3. The token is used to run `gh workflow run rebuild-staging.yml --repo dimagi/commcare-hq`

## Authentication

The workflow uses a GitHub App rather than a Personal Access Token (PAT). This gives scoped permissions, short-lived tokens, and no dependency on a personal account.

**GitHub App:** Staging Branches Automations
- Configured in the [dimagi org's GitHub Apps settings](https://github.com/organizations/dimagi/settings/apps)
- Installed only on `dimagi/commcare-hq`
- Permission: Actions: Read & Write (only)

**Repo secrets** on `dimagi/staging-branches` (managed at [Settings > Secrets](https://github.com/dimagi/staging-branches/settings/secrets/actions)):
- `STAGING_BRANCHES_APP_ID` — the app's numeric ID (found on the app's General page)
- `STAGING_BRANCHES_APP_PRIVATE_KEY` — the app's private key in PEM format

### Rotating credentials

1. Go to the app's settings page in the dimagi org
2. Under **Private keys**, click **Generate a private key**
3. Update the `STAGING_BRANCHES_APP_PRIVATE_KEY` secret with the new key's contents
4. Revoke the old key from the same page

## Adding triggers for other repos

To trigger a workflow in another repo when its config file changes, copy the existing workflow and update the `paths` filter and `--repo` target. The two non-obvious requirements:

- The **Staging Branches Automations** GitHub App must be installed on the target repo
- The target repo must have a workflow that accepts `workflow_dispatch`
