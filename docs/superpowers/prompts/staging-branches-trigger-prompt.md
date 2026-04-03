# Task: Add cross-repo trigger from staging-branches to commcare-hq

## Goal

When `commcare-hq-staging.yml` is updated in `dimagi/staging-branches` (on the `main` branch), automatically trigger the `rebuild-staging` workflow in `dimagi/commcare-hq`.

## Context

### What already exists

- `dimagi/commcare-hq` has a `workflow_dispatch` workflow at `.github/workflows/rebuild-staging.yml` that runs `./scripts/rebuildstaging` to rebuild the `autostaging` branch.
- That workflow needs to be triggered from the `staging-branches` repo when the config file changes.

### What needs to be created

A GitHub Actions workflow in `dimagi/staging-branches` that:
1. Triggers on pushes to `main` that modify `commcare-hq-staging.yml`
2. Triggers the `rebuild-staging` workflow in `dimagi/commcare-hq` via `workflow_dispatch`

### Desired approach

Use `workflow_dispatch` (NOT `repository_dispatch`). `workflow_dispatch` is simpler because the target workflow already accepts it — no changes needed on the commcare-hq side. It also provides better visibility in the GitHub Actions UI (shows as a manual trigger with a clear link to the workflow), and requires shallower permissions (action:write instead of contents:write).

I would also strongly prefer using a GitHub App and its credentials, rather than a PAT.
