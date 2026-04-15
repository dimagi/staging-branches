# Automated Rebuild Trigger

This document covers how the automated staging rebuild trigger works and how to maintain it.

## Overview

There are two triggers that keep `autostaging` up to date:

1. **This repo** — `.github/workflows/trigger-commcare-hq-rebuild.yml` fires on pushes to `main` that modify `commcare-hq-staging.yml`. It triggers `rebuild-staging` in `dimagi/commcare-hq` via `workflow_dispatch`.
2. **commcare-hq** — The [`rebuild-staging` workflow](https://github.com/dimagi/commcare-hq/blob/master/.github/workflows/rebuild-staging.yml) fires on push to any branch. A `check-branch` job fetches `commcare-hq-staging.yml` and skips the rebuild if the pushed branch isn't listed. This covers pushes to `master` (the base branch) and pushes to branches already in the config. A global concurrency group with `cancel-in-progress: false` ensures at most one rebuild runs at a time, with one queued.

Additionally, merged branches are cleaned up automatically:

3. **Merged branch removal** — When a branch in the staging config is merged to `master` in commcare-hq, the `rebuild-staging` workflow detects the merge commit, checks if the merged branch is in the staging config, and triggers `.github/workflows/remove-branch.yml` in this repo instead of rebuilding. The branch is removed from the config file, and the resulting push to `main` triggers a clean rebuild via trigger 1.

## How it works

1. GitHub detects a push to `main` that changes `commcare-hq-staging.yml`
2. The workflow uses [`actions/create-github-app-token`](https://github.com/actions/create-github-app-token) to mint a short-lived token from the **Staging Branches Automations** GitHub App
3. The token is used to run `gh workflow run rebuild-staging.yml --repo dimagi/commcare-hq`

## Authentication

The workflows use a GitHub App rather than a Personal Access Token (PAT). This gives scoped permissions, short-lived tokens, and no dependency on a personal account.

**GitHub App:** Staging Branches Automations
- Configured in the [dimagi org's GitHub Apps settings](https://github.com/organizations/dimagi/settings/apps)
- Installed on `dimagi/commcare-hq` and `dimagi/staging-branches`
- Permission: Actions: Read & Write (only)

**Repo secrets** on `dimagi/staging-branches` (managed at [Settings > Secrets](https://github.com/dimagi/staging-branches/settings/secrets/actions)):
- `STAGING_BRANCHES_APP_ID` — the app's numeric ID (found on the app's General page)
- `STAGING_BRANCHES_APP_PRIVATE_KEY` — the app's private key in PEM format

**Repo secrets** on `dimagi/commcare-hq` (managed at [Settings > Secrets](https://github.com/dimagi/commcare-hq/settings/secrets/actions)):
- `STAGING_BRANCHES_APP_ID` — same app ID as above
- `STAGING_BRANCHES_APP_PRIVATE_KEY` — same private key as above

The commcare-hq secrets are used by the `rebuild-staging` workflow to trigger the `remove-branch` workflow in this repo when a staging branch is merged to master.

### Rotating credentials

1. Go to the app's settings page in the dimagi org
2. Under **Private keys**, click **Generate a private key**
3. Update the `STAGING_BRANCHES_APP_PRIVATE_KEY` secret with the new key's contents
4. Revoke the old key from the same page

## Merged branch removal

`.github/workflows/remove-branch.yml` is a `workflow_dispatch` workflow that removes a branch entry from a staging config file. It accepts two inputs:

- `file` — the config file name (e.g. `commcare-hq-staging.yml`)
- `branch` — the branch name to remove

The workflow removes only standalone branch entries (e.g. `- branch-name  # comment`), not `+`-joined conflict resolution branches (e.g. `- foo+branch-name+bar`). If the branch is not found, it exits cleanly with no commit.

### How it's triggered

When a PR is merged to `master` in commcare-hq, the `rebuild-staging` workflow:
1. Parses the merge commit message to extract the branch name
2. Checks if the branch is a standalone entry in `commcare-hq-staging.yml`
3. If found, triggers `remove-branch.yml` in this repo instead of rebuilding
4. The removal commits to `main`, which triggers `trigger-commcare-hq-rebuild.yml` for a clean rebuild

### Manual use

The workflow can also be triggered manually from the [Actions tab](https://github.com/dimagi/staging-branches/actions/workflows/remove-branch.yml) to remove a branch without editing the file by hand.

## Adding triggers for other repos

To trigger a workflow in another repo when its config file changes, copy the existing workflow and update the `paths` filter and `--repo` target. The two non-obvious requirements:

- The **Staging Branches Automations** GitHub App must be installed on the target repo
- The target repo must have a workflow that accepts `workflow_dispatch`
