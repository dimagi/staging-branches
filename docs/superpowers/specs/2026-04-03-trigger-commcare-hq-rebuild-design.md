# Design: Cross-repo trigger from staging-branches to commcare-hq

## Goal

When `commcare-hq-staging.yml` is updated on `main` in `dimagi/staging-branches`, automatically trigger the `rebuild-staging` workflow in `dimagi/commcare-hq` via `workflow_dispatch`.

## Workflow

**File:** `.github/workflows/trigger-commcare-hq-rebuild.yml`

**Trigger:**
- `push` to `main` branch
- Only when `commcare-hq-staging.yml` is modified

**Steps:**
1. Generate a short-lived installation access token using `actions/create-github-app-token@v1` with the GitHub App credentials
2. Use `gh workflow run rebuild-staging.yml --repo dimagi/commcare-hq` with the minted token to trigger the rebuild

**Secrets required on `dimagi/staging-branches`:**
- `STAGING_BRANCHES_APP_ID` — the GitHub App's App ID
- `STAGING_BRANCHES_APP_PRIVATE_KEY` — the GitHub App's private key (PEM format)

## GitHub App Setup

1. **Create the app** at https://github.com/organizations/dimagi/settings/apps/new
   - Name: `Staging Branches Automations`
   - Homepage URL: `https://github.com/dimagi/staging-branches`
   - Uncheck "Active" under Webhook (no webhook needed)
   - Repository permissions: **Actions: Read & Write**
   - No other permissions needed
   - Where can this GitHub App be installed? **Only on this account**
2. **Note the App ID** from the app's settings page (General > About)
3. **Generate a private key** from the app's settings page (General > Private keys > Generate a private key). Save the downloaded `.pem` file.
4. **Install the app** at `https://github.com/organizations/dimagi/settings/installations`
   - Select **Only select repositories** and choose `dimagi/commcare-hq`
5. **Add secrets** to `dimagi/staging-branches` at https://github.com/dimagi/staging-branches/settings/secrets/actions
   - `STAGING_BRANCHES_APP_ID`: paste the App ID
   - `STAGING_BRANCHES_APP_PRIVATE_KEY`: paste the full contents of the `.pem` file

## Why workflow_dispatch over repository_dispatch

- The target workflow (`rebuild-staging.yml`) already accepts `workflow_dispatch` — no changes needed on the commcare-hq side
- Better visibility in GitHub Actions UI (shows as a manual trigger)
- Requires only `actions:write` permission, not `contents:write`

## Why a GitHub App over a PAT

- Scoped to specific repos and permissions (principle of least privilege)
- Not tied to any individual user account
- Tokens are short-lived (auto-expire)
- Auditable in org settings
