# GitHub Environments Setup Guide

This guide explains how to configure GitHub Environments for the two-tier testing strategy used in this project.

## Overview

The project uses two test tiers:
- **Tier A tests**: Run automatically on all PRs without credentials (uses fixtures/mocks)
- **Tier B tests**: Require OAuth credentials and maintainer approval before running

GitHub Environments provide a secure way to gate access to credentials, ensuring that untrusted PR code cannot access OAuth tokens without explicit maintainer approval.

## Creating the `tier-b-testing` Environment

### Step 1: Navigate to Environment Settings

1. Go to your repository on GitHub
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Name it `tier-b-testing`
5. Click **Configure environment**

### Step 2: Configure Environment Protection Rules

Under **Environment protection rules**, enable the following:

#### Required Reviewers

1. Check **Required reviewers**
2. Add maintainers who should approve Tier B test runs
3. Recommended: Add at least 2 reviewers for redundancy

This ensures that every PR must be reviewed and approved before Tier B tests can access credentials.

#### Wait Timer (Optional)

You can add a wait timer (e.g., 5 minutes) to give reviewers time to inspect PR changes before tests run. This is optional but adds an extra layer of security.

#### Deployment Branches

1. Select **Protected branches** or **Selected branches**
2. For most projects, allow only:
   - `main` branch
   - Feature branches matching a pattern (e.g., `feature/*`)

This prevents random branches from requesting credential access.

### Step 3: Configure Environment Secrets

Under **Environment secrets**, add the following secrets:

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth 2.0 Client ID | Google Cloud Console → APIs & Services → Credentials |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth 2.0 Client Secret | Same location as Client ID |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | Long-lived refresh token | Run `python scripts/bootstrap_oauth.py` locally |

#### Obtaining OAuth Credentials

1. **Client ID and Secret**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **APIs & Services** → **Credentials**
   - Create or select an OAuth 2.0 Client ID (Desktop app type)
   - Copy the Client ID and Client Secret

2. **Refresh Token**:
   - Run the bootstrap script locally:
     ```bash
     uv run python scripts/bootstrap_oauth.py
     ```
   - Complete the OAuth flow in your browser
   - The script outputs the refresh token for CI use

## Workflow Configuration

The `tier-b-tests.yml` workflow references this environment:

```yaml
jobs:
  tier-b-tests:
    runs-on: ubuntu-latest
    environment: tier-b-testing  # Triggers approval gate
    steps:
      - uses: actions/checkout@v4
      - name: Run Tier B Tests
        env:
          GOOGLE_OAUTH_CLIENT_ID: ${{ secrets.GOOGLE_OAUTH_CLIENT_ID }}
          GOOGLE_OAUTH_CLIENT_SECRET: ${{ secrets.GOOGLE_OAUTH_CLIENT_SECRET }}
          GOOGLE_OAUTH_REFRESH_TOKEN: ${{ secrets.GOOGLE_OAUTH_REFRESH_TOKEN }}
        run: |
          uv run pytest -m tier_b
```

## Approving Tier B Tests

When a PR is created:

1. Tier A tests run automatically
2. Tier B tests show as "Waiting" with an approval prompt
3. A maintainer reviews the PR code
4. If the code is safe, the maintainer clicks **Review deployments** → **Approve and deploy**
5. Tier B tests then execute with credentials

## Security Considerations

### Why Manual Approval?

Pull requests can contain arbitrary code. Without approval gates, a malicious PR could:
- Exfiltrate OAuth credentials
- Access and modify Google Docs/Drive
- Persist access beyond the test run

The environment protection ensures maintainers verify PR code before exposing credentials.

### Credential Rotation

If credentials are compromised or expire:

1. Generate a new refresh token using `bootstrap_oauth.py`
2. Update the `GOOGLE_OAUTH_REFRESH_TOKEN` secret in the environment
3. Optionally rotate the Client ID/Secret in Google Cloud Console

### Token Expiration

Google may revoke refresh tokens for non-production OAuth applications. If Tier B tests start failing with authentication errors:

1. Check the workflow logs for credential validation errors
2. Re-run `bootstrap_oauth.py` locally to obtain fresh tokens
3. Update the environment secret

## Troubleshooting

### "Waiting for review"

This is expected behavior. A maintainer must approve Tier B tests before they run.

### "Invalid credentials" Error

The refresh token may have expired or been revoked. Re-run the bootstrap script and update the environment secret.

### "Environment not found"

Ensure the environment name in `tier-b-tests.yml` exactly matches `tier-b-testing` (case-sensitive).

### Tests Skipped

If Tier B tests are skipped, check:
1. Environment secrets are configured
2. The workflow correctly passes environment variables
3. The pre-flight credential check passes

## Related Files

- `.github/workflows/tier-a-tests.yml` - Automatic Tier A test workflow
- `.github/workflows/tier-b-tests.yml` - Tier B workflow with environment protection
- `scripts/bootstrap_oauth.py` - OAuth bootstrap utility for obtaining refresh tokens
- `tests/conftest.py` - Pytest configuration with tier markers
