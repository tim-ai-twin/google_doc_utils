# Quickstart: Cloud Testing Infrastructure with OAuth

**Feature**: 001-cloud-testing-oauth
**Date**: 2026-01-02
**Audience**: Developers, Cloud Agents, CI/CD Maintainers

## Overview

This guide helps you get started with the google_doc_utils testing infrastructure. Choose your path:

- **[Local Developer](#local-developer-setup)** - Set up OAuth and run tests on your machine
- **[Cloud Agent](#cloud-agent-setup)** - Run Tier A tests without credentials
- **[CI/CD Maintainer](#cicd-setup)** - Configure GitHub Actions workflows

---

## Local Developer Setup

### Prerequisites

- Python 3.11 or later
- `uv` package manager ([installation](https://github.com/astral-sh/uv))
- Google account (Gmail or Workspace)

### Step 1: Clone and Install

```bash
git clone <repository-url>
cd google_doc_utils

# Install dependencies
uv sync
```

### Step 2: Bootstrap OAuth Credentials

Run the interactive OAuth setup script:

```bash
uv run scripts/bootstrap_oauth.py
```

**What happens**:
1. Script opens browser to Google OAuth consent screen
2. You log in with your Google account
3. You grant permissions for Docs and Drive access
4. Script saves refresh token to `.credentials/token.json`

**Expected output**:
```
✓ OAuth authentication successful!
✓ Refresh token saved to .credentials/token.json

Run tests:
  Tier A (no credentials): uv run pytest -m tier_a
  Tier B (with credentials): uv run pytest -m tier_b
```

### Step 3: Run Tests

**Run all tests** (Tier A + Tier B):
```bash
uv run pytest
```

**Run only Tier A** (credential-free):
```bash
uv run pytest -m tier_a
```

**Run only Tier B** (credential-required):
```bash
uv run pytest -m tier_b
```

**Run proof-of-concept test**:
```bash
uv run pytest tests/tier_b/test_proof_of_concept.py::test_gondwana_document
```

### Step 4: Verify Setup

Expected output from Tier B tests:

```
tests/tier_b/test_proof_of_concept.py::test_gondwana_document PASSED
  ✓ Pre-flight check passed (1247ms)
  ✓ Document read successfully
  ✓ First word is "Gondwana"
```

---

## Cloud Agent Setup

Cloud agents can contribute code by running Tier A tests without credentials.

### Step 1: Install Dependencies

```bash
uv sync
```

### Step 2: Run Tier A Tests

```bash
uv run pytest -m tier_a
```

**What happens**:
- Tests run using mocked fixtures
- No network calls to Google APIs
- No credentials required

**Expected behavior**:
- All Tier A tests pass
- Tier B tests are automatically skipped with message:
  ```
  SKIPPED [1] - No credentials available (Tier A mode)
  ```

### Step 3: Make Changes

Cloud agents can:
- Modify library code
- Add/update Tier A tests
- Update fixtures in `tests/fixtures/`

Cloud agents **cannot**:
- Run Tier B tests (requires human-provided credentials)
- Validate real Google API integration

### Cloud Agent Mode

Set the `CLOUD_AGENT` environment variable to explicitly enable cloud agent mode:

```bash
export CLOUD_AGENT=true
uv run pytest
```

**What happens**:
- Environment is detected as `CLOUD_AGENT` type
- Tier B tests are automatically skipped (no credential errors)
- Credential loading defaults to environment variables

**Accepted values**: `1`, `true`, `yes` (case-insensitive)

**Use cases**:
- Running tests in remote/containerized environments
- CI/CD pipelines where only Tier A tests should run
- Development environments without Google OAuth setup

**Credential configuration for CI/CD**:

If you need Tier B tests in CI/CD, configure these environment variables:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-your-secret"
export GOOGLE_OAUTH_REFRESH_TOKEN="1//your-refresh-token"
```

Without these variables set, Tier B tests will skip gracefully.

---

## CI/CD Setup

For repository maintainers configuring GitHub Actions.

### Step 1: Obtain OAuth Credentials

On your local machine:

```bash
uv run scripts/bootstrap_oauth.py
```

At the end, the script displays environment variable format:

```
For CI/CD environments, add these secrets:
  GOOGLE_OAUTH_REFRESH_TOKEN=1//0gZ...
  GOOGLE_OAUTH_CLIENT_ID=123456789.apps.googleusercontent.com
  GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-...
```

### Step 2: Create GitHub Environment

1. Go to repository **Settings** → **Environments**
2. Click **New environment**
3. Name: `tier-b-testing`
4. Enable **Required reviewers**
5. Add maintainers as reviewers

### Step 3: Add Environment Secrets

In the `tier-b-testing` environment:

1. Click **Add secret**
2. Add each secret from Step 1:
   - `TIER_B_OAUTH_REFRESH_TOKEN`
   - `TIER_B_OAUTH_CLIENT_ID`
   - `TIER_B_OAUTH_CLIENT_SECRET`

### Step 4: Workflow Files

The repository includes two workflow files:

**`.github/workflows/tier-a-tests.yml`** - Runs automatically on all PRs:
```yaml
name: Tier A Tests (Auto)
on: [pull_request, push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest -m tier_a
```

**`.github/workflows/tier-b-tests.yml`** - Requires manual approval:
```yaml
name: Tier B Tests (Requires Approval)
on: [pull_request, workflow_dispatch]
jobs:
  test:
    runs-on: ubuntu-latest
    environment: tier-b-testing  # Protection enabled
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest -m tier_b
    env:
      GOOGLE_OAUTH_REFRESH_TOKEN: ${{ secrets.TIER_B_OAUTH_REFRESH_TOKEN }}
      GOOGLE_OAUTH_CLIENT_ID: ${{ secrets.TIER_B_OAUTH_CLIENT_ID }}
      GOOGLE_OAUTH_CLIENT_SECRET: ${{ secrets.TIER_B_OAUTH_CLIENT_SECRET }}
```

### Step 5: Approving Tier B Tests

When a PR is opened:

1. **Tier A tests run automatically** - No approval needed
2. **Tier B tests wait for approval** - Shows "Waiting for review" status
3. **Maintainer reviews code** - Check for malicious credential use
4. **Maintainer approves environment** - Click "Review deployments" → Approve
5. **Tier B tests run** - With access to credentials

---

## Common Tasks

### Re-authenticate Locally

If credentials expire or are revoked:

```bash
# Delete old credentials
rm .credentials/token.json

# Run bootstrap again
uv run scripts/bootstrap_oauth.py
```

### Update CI/CD Credentials

If refresh token expires in GitHub Actions:

1. Run `bootstrap_oauth.py` locally (as maintainer)
2. Update `TIER_B_OAUTH_REFRESH_TOKEN` secret in `tier-b-testing` environment
3. Re-run failed workflow

### Clean Up Orphaned Test Resources

If test failures leave resources in Google Drive:

```bash
uv run scripts/cleanup_test_resources.py
```

This script:
- Lists test resources created in last 7 days
- Prompts for confirmation
- Deletes confirmed resources

### Run Specific Test File

```bash
# Tier A test file
uv run pytest tests/tier_a/test_auth_logic.py

# Tier B test file
uv run pytest tests/tier_b/test_oauth_flow.py
```

### Run Tests with Coverage

```bash
uv run pytest --cov=src/extended_google_doc_utils --cov-report=html
open htmlcov/index.html
```

### Debug Test Failures

Enable verbose output:

```bash
uv run pytest -vv -s
```

Show full error tracebacks:

```bash
uv run pytest --tb=long
```

---

## Troubleshooting

### "No credentials available" when running Tier B tests locally

**Solution**: Run `uv run scripts/bootstrap_oauth.py` to authenticate

### "Pre-flight check failed: Invalid credentials"

**Causes**:
- Refresh token expired (Google revoked it)
- OAuth scopes changed
- Client ID/secret invalid

**Solution**:
```bash
rm .credentials/token.json
uv run scripts/bootstrap_oauth.py
```

### "Port 8080 already in use" during OAuth flow

**Solution**: The bootstrap script will automatically try ports 8081-8089. If all fail:
```bash
# Find and kill process using port 8080
lsof -ti:8080 | xargs kill -9
```

### Tier B tests fail in GitHub Actions

**Causes**:
- Environment approval not configured
- Secrets not set correctly
- Refresh token expired

**Solution**:
1. Verify environment `tier-b-testing` exists
2. Verify secrets are set (check for typos)
3. Re-run bootstrap locally and update secrets

### "Quota exceeded" errors

**Causes**: Too many API calls in short period

**Solution**:
- Wait 60 seconds and retry
- Reduce test parallelism
- Check for orphaned tests making excessive calls

### Tests creating resources but not cleaning up

**Expected behavior**: Some cleanup failures are normal (network errors, force-kill)

**Solution**:
```bash
# Manual cleanup script
uv run scripts/cleanup_test_resources.py
```

---

## Best Practices

### For Local Development

✅ **Do**:
- Run `pytest -m tier_a` frequently (fast, no credentials)
- Run `pytest -m tier_b` before pushing (validates real API integration)
- Keep `.credentials/` in `.gitignore` (already configured)
- Re-authenticate if tests start failing unexpectedly

❌ **Don't**:
- Commit `.credentials/token.json` to git
- Share refresh tokens via Slack/email
- Use production Google account for testing
- Hardcode document IDs in tests (except proof-of-concept)

### For Cloud Agents

✅ **Do**:
- Run `pytest -m tier_a` to validate changes
- Update fixtures if Google API responses change
- Document any Tier B test requirements in PR description

❌ **Don't**:
- Attempt to run Tier B tests (will skip)
- Request OAuth credentials
- Mock Tier B tests without understanding real API behavior

### For CI/CD Maintainers

✅ **Do**:
- Review PRs before approving Tier B environment
- Rotate refresh tokens periodically (every 6 months)
- Monitor GitHub Actions quota usage
- Keep bootstrap script instructions updated

❌ **Don't**:
- Auto-approve Tier B tests without code review
- Store credentials in repository secrets (use environments)
- Disable environment protection
- Share OAuth client secrets publicly

---

## Next Steps

After completing setup:

1. **Read the spec**: `specs/001-cloud-testing-oauth/spec.md` - Full requirements
2. **Explore data model**: `specs/001-cloud-testing-oauth/data-model.md` - Entity design
3. **Review contracts**: `specs/001-cloud-testing-oauth/contracts/` - API interfaces
4. **Check research**: `specs/001-cloud-testing-oauth/research.md` - Technology decisions

---

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Authenticate locally | `uv run scripts/bootstrap_oauth.py` |
| Run all tests | `uv run pytest` |
| Run Tier A only | `uv run pytest -m tier_a` |
| Run Tier B only | `uv run pytest -m tier_b` |
| Proof-of-concept test | `uv run pytest tests/tier_b/test_proof_of_concept.py` |
| Clean up resources | `uv run scripts/cleanup_test_resources.py` |
| Test coverage | `uv run pytest --cov` |

---

**Quickstart Status**: ✓ Complete
**Last Updated**: 2026-01-02
