# Research: Cloud Testing Infrastructure with OAuth

**Feature**: 001-cloud-testing-oauth
**Date**: 2026-01-02
**Status**: Phase 0 Complete

## Overview

This document consolidates research findings for implementing a two-tier testing infrastructure with OAuth authentication for the google_doc_utils Python library. All technical clarifications from the plan's Technical Context have been resolved.

---

## Technology Stack Research

### Python Package Manager: uv

**Decision**: Use `uv` for dependency management

**Rationale**:
- **Speed**: 10-100x faster than pip/pip-tools for dependency resolution and installation
- **Modern**: Rust-based, supports PEP 517/518, PEP 621 (pyproject.toml)
- **Lock file**: Generates `uv.lock` for reproducible builds across environments
- **Python version management**: Can manage Python versions via `.python-version` file
- **CI/CD friendly**: Single binary, no bootstrapping required
- **Active development**: Maintained by Astral (creators of Ruff)

**Alternatives considered**:
- **pip + pip-tools**: Traditional, slower dependency resolution, requires separate tools for locking
- **Poetry**: Heavier, slower, more opinionated about project structure
- **PDM**: Good alternative, but uv has better performance and simpler model

**Best practices**:
- Use `pyproject.toml` for all configuration (no setup.py)
- Commit `uv.lock` to version control for reproducibility
- Use `uv sync` in CI/CD to install exact versions from lock file
- Use `uv pip compile` to generate requirements.txt if needed for compatibility

---

## OAuth 2.0 for Desktop Applications

### Google OAuth Flow for Testing

**Decision**: Desktop OAuth flow with local callback server for initial authentication, environment variables for automated environments

**Rationale**:
- **Desktop flow**: Standard OAuth 2.0 flow for installed applications (non-web)
- **Local callback**: Temporary HTTP server on `localhost:8080` (or dynamic port) to capture authorization code
- **Refresh tokens**: Long-lived tokens enable testing without repeated authentication
- **Environment variables**: `GOOGLE_OAUTH_REFRESH_TOKEN`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` for CI/CD

**Alternatives considered**:
- **Service accounts**: Require Google Workspace domain admin approval, not suitable for consumer Gmail accounts
- **Web OAuth flow**: Requires hosted redirect URI, unnecessary complexity for local development
- **API keys**: Insufficient permissions for user-specific Google Docs access

**Best practices**:
- Use `google-auth-oauthlib` library (official Google library)
- Store refresh tokens in `.credentials/token.json` (gitignored)
- Use minimal OAuth scopes: `https://www.googleapis.com/auth/documents` and `https://www.googleapis.com/auth/drive.file`
- Implement token refresh logic with `google-auth` library
- Handle OAuth errors gracefully (expired/revoked tokens)

**Implementation approach**:
```python
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

def get_credentials():
    creds = None
    if os.path.exists('.credentials/token.json'):
        with open('.credentials/token.json', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        with open('.credentials/token.json', 'wb') as token:
            pickle.dump(creds, token)

    return creds
```

---

## Two-Tier Testing Strategy

### Tier A: Credential-Free Tests

**Decision**: Use pytest fixtures with mocked Google API responses

**Rationale**:
- **Accessibility**: Cloud agents and developers without credentials can run tests
- **Speed**: No network I/O, tests run in milliseconds
- **Reliability**: No dependency on Google API availability or quota
- **Security**: No credential leakage risk

**Best practices**:
- Store mock responses in `tests/fixtures/google_docs_responses.json`
- Use `pytest-mock` or `unittest.mock` for patching Google API clients
- Create realistic fixtures based on actual Google API responses
- Update fixtures when Google changes API response schemas
- Mark tests with `@pytest.mark.tier_a` custom marker

**Implementation approach**:
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_docs_service():
    """Fixture providing mocked Google Docs API service"""
    with patch('google_api.docs_client.build') as mock_build:
        mock_service = Mock()
        mock_service.documents().get().execute.return_value = {
            'title': 'Test Document',
            'body': {'content': [...]}
        }
        mock_build.return_value = mock_service
        yield mock_service

@pytest.mark.tier_a
def test_document_parsing(mock_docs_service):
    # Test runs without real credentials
    result = parse_document('fake_doc_id')
    assert result['title'] == 'Test Document'
```

### Tier B: Credential-Required Tests

**Decision**: Use real Google API calls with pre-flight credential validation

**Rationale**:
- **Integration validation**: Ensures OAuth flow and API integration actually work
- **API contract verification**: Detects breaking changes in Google APIs
- **Real-world testing**: Tests against actual Google Docs/Drive behavior

**Best practices**:
- Mark tests with `@pytest.mark.tier_b` custom marker
- Implement pre-flight check in `conftest.py` to validate credentials before running
- Skip Tier B tests if credentials unavailable (not fail)
- Clean up test resources after execution (best effort)
- Use unique resource identifiers (timestamp + random suffix) for parallel execution

**Pre-flight check approach**:
```python
import pytest
from google.auth.exceptions import RefreshError

@pytest.fixture(scope="session", autouse=True)
def preflight_tier_b_check(request):
    """Validates credentials before any Tier B tests run"""
    if 'tier_b' not in request.config.getoption('-m', default=''):
        return  # Skip if not running Tier B tests

    try:
        creds = get_credentials()
        # Make a lightweight API call to validate credentials
        service = build('drive', 'v3', credentials=creds)
        service.about().get(fields='user').execute()
    except RefreshError:
        pytest.skip("Invalid or expired OAuth credentials. Run bootstrap_oauth.py to re-authenticate.")
    except Exception as e:
        pytest.skip(f"Pre-flight credential check failed: {e}")
```

---

## GitHub Actions Integration

### Environment Protection for Tier B Tests

**Decision**: Use GitHub Environment with required reviewers to protect credentials

**Rationale**:
- **Security**: Credentials never exposed to untrusted PR code without approval
- **Simplicity**: Built-in GitHub feature, no custom workflow logic needed
- **Audit trail**: GitHub tracks who approved credential access and when
- **Universal protection**: Works for both fork PRs and same-repo branches

**Best practices**:
- Create GitHub Environment named `tier-b-testing`
- Configure required reviewers (maintainers only)
- Store OAuth credentials as environment secrets: `TIER_B_OAUTH_REFRESH_TOKEN`, `TIER_B_OAUTH_CLIENT_ID`, `TIER_B_OAUTH_CLIENT_SECRET`
- Use separate workflow files: `tier-a-tests.yml` (auto-run), `tier-b-tests.yml` (requires approval)

**Workflow structure**:
```yaml
# .github/workflows/tier-a-tests.yml
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

# .github/workflows/tier-b-tests.yml
name: Tier B Tests (Requires Approval)
on: [pull_request, workflow_dispatch]
jobs:
  test:
    runs-on: ubuntu-latest
    environment: tier-b-testing  # Requires manual approval
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

---

## Test Resource Isolation

### Dynamic Resource Creation with Unique Identifiers

**Decision**: Generate unique resource names using timestamp + random suffix

**Rationale**:
- **Parallel safety**: Minimizes conflicts when multiple test runs execute simultaneously
- **Debugging**: Timestamp in name helps identify when resource was created
- **Cleanup**: Enables identification of orphaned resources for manual cleanup

**Best practices**:
- Format: `test-{feature}-{timestamp}-{random}` (e.g., `test-doc-20260102153045-a3f2`)
- Use `datetime.utcnow().strftime('%Y%m%d%H%M%S')` for timestamp
- Use `secrets.token_hex(4)` or `uuid.uuid4().hex[:8]` for random suffix
- Implement context manager for automatic cleanup
- Log created resource IDs for debugging

**Implementation approach**:
```python
import secrets
from datetime import datetime
from contextlib import contextmanager

@contextmanager
def isolated_test_doc(service, title_prefix="test-doc"):
    """Create a test document with unique ID, cleanup on exit"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(4)
    title = f"{title_prefix}-{timestamp}-{random_suffix}"

    # Create document
    doc = service.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']

    try:
        yield doc_id
    finally:
        # Best-effort cleanup
        try:
            service.files().delete(fileId=doc_id).execute()
        except Exception as e:
            print(f"Warning: Failed to cleanup {doc_id}: {e}")
```

---

## Pytest Configuration

### Custom Markers for Tier A/B Tests

**Decision**: Use pytest custom markers with strict checking

**Rationale**:
- **Clear intent**: Test tier is explicit in test code
- **Selective execution**: Can run subsets via `pytest -m tier_a` or `pytest -m tier_b`
- **Documentation**: Markers serve as documentation of test requirements

**Configuration** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
markers = [
    "tier_a: Credential-free tests using fixtures and mocks",
    "tier_b: Credential-required integration tests against real Google APIs",
]
addopts = "--strict-markers -v"
```

**Usage**:
```python
import pytest

@pytest.mark.tier_a
def test_auth_logic_without_api():
    """Test authentication logic using mocks"""
    pass

@pytest.mark.tier_b
def test_oauth_flow_real_api():
    """Test real OAuth flow against Google APIs"""
    pass
```

---

## Google API Client Libraries

### Official Python Client Libraries

**Decision**: Use `google-api-python-client` for Docs/Drive APIs

**Rationale**:
- **Official**: Maintained by Google, guaranteed API compatibility
- **Comprehensive**: Covers all Google Docs and Drive API endpoints
- **Discovery-based**: Auto-generates client from API discovery documents
- **Well-documented**: Extensive official documentation and examples

**Dependencies**:
```toml
[project]
dependencies = [
    "google-auth>=2.27.0",
    "google-auth-oauthlib>=1.2.0",
    "google-auth-httplib2>=0.2.0",
    "google-api-python-client>=2.115.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.12.0",
    "pytest-cov>=4.1.0",
]
```

**API scope selection**:
- `https://www.googleapis.com/auth/documents` - Full CRUD access to Google Docs
- `https://www.googleapis.com/auth/drive.file` - Access only to files created by the app (safer than full drive scope)

**Alternatives considered**:
- `https://www.googleapis.com/auth/drive` - Too broad, grants access to all Drive files
- Service accounts - Require domain admin approval, unsuitable for consumer accounts

---

## Proof-of-Concept Test

### "Gondwana" Document Test

**Decision**: Hardcoded test against specific Google Doc to validate end-to-end flow

**Document ID**: `1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4`
**Expected first word**: "Gondwana"

**Rationale**:
- **Smoke test**: Quick validation that OAuth + API integration works
- **Minimal setup**: No dynamic resource creation needed
- **Clear success criteria**: Simple assertion on known content
- **Fast**: <5 seconds expected execution time

**Implementation approach**:
```python
import pytest
from google_api.docs_client import DocsClient

@pytest.mark.tier_b
def test_proof_of_concept_gondwana(google_credentials):
    """Validates OAuth and API integration by reading known document"""
    doc_id = '1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4'

    client = DocsClient(credentials=google_credentials)
    doc = client.get_document(doc_id)

    # Extract first word from document content
    first_word = extract_first_word(doc)

    assert first_word == "Gondwana", (
        f"Expected first word 'Gondwana', got '{first_word}'. "
        f"Document may have been modified or inaccessible."
    )
```

---

## Bootstrap Script Design

### Interactive OAuth Setup

**Decision**: Standalone script that guides users through OAuth setup

**Rationale**:
- **First-run experience**: Critical for developer onboarding
- **Clear instructions**: Step-by-step prompts reduce confusion
- **Output flexibility**: Generates both local token file and environment variable format

**Script features**:
- Detect if credentials already exist
- Launch browser for OAuth consent
- Capture authorization code via local callback server
- Save refresh token to `.credentials/token.json`
- Display environment variable format for CI/CD setup
- Validate credentials with test API call

**Script location**: `scripts/bootstrap_oauth.py`

**Usage**:
```bash
uv run scripts/bootstrap_oauth.py
```

**Output example**:
```
✓ OAuth authentication successful!
✓ Refresh token saved to .credentials/token.json

For CI/CD environments, add these secrets:
  GOOGLE_OAUTH_REFRESH_TOKEN=<redacted>
  GOOGLE_OAUTH_CLIENT_ID=<redacted>
  GOOGLE_OAUTH_CLIENT_SECRET=<redacted>

Run tests:
  Tier A (no credentials): uv run pytest -m tier_a
  Tier B (with credentials): uv run pytest -m tier_b
```

---

## Summary of Research Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| Package manager | uv | Speed, modern PEP support, lock files |
| OAuth flow | Desktop flow + local callback | Standard for installed apps, works with consumer Gmail |
| OAuth library | google-auth-oauthlib | Official Google library |
| Testing framework | pytest | Fixture ecosystem, markers, plugin support |
| Tier A tests | Mocked fixtures | Accessibility for cloud agents, speed, security |
| Tier B tests | Real API calls | Integration validation, API contract verification |
| Pre-flight check | Session-scoped pytest fixture | Early failure detection, clear error messages |
| GitHub protection | Environment with reviewers | Built-in security, simple, audit trail |
| Resource isolation | Timestamp + random suffix | Parallel safety, debugging, cleanup |
| Proof-of-concept | Hardcoded "Gondwana" doc | Fast smoke test, minimal setup |
| Bootstrap script | Interactive CLI | Developer onboarding, credential setup |

---

## Open Questions / Future Considerations

1. **OAuth client credentials distribution**: How will developers/CI get `client_secrets.json`?
   - **Current assumption**: Project maintainer provides client ID/secret (documented in setup)
   - **Future**: Consider OAuth app in testing mode vs production mode

2. **Fixture maintenance**: Who updates fixtures when Google APIs change?
   - **Current assumption**: Developers monitor API changes manually
   - **Future**: Automated fixture generation from Tier B test recordings

3. **Orphaned resource cleanup**: How often should manual cleanup run?
   - **Current assumption**: Ad-hoc when Drive storage fills up
   - **Future**: Scheduled cleanup script in CI (weekly?)

4. **Multi-account testing**: Should we support multiple OAuth profiles?
   - **Current assumption**: Single user sufficient for v1
   - **Future**: Profile-based credentials if needed

5. **Rate limiting**: How to handle Google API quota exhaustion?
   - **Current assumption**: Fail tests, retry later
   - **Future**: Exponential backoff, quota monitoring

---

**Research Status**: ✓ Complete
**Next Phase**: Phase 1 - Design (data model, contracts, quickstart)
