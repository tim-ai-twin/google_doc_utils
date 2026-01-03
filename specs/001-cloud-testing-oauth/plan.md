# Implementation Plan: Cloud Testing Infrastructure with OAuth

**Branch**: `001-cloud-testing-oauth` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cloud-testing-oauth/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature establishes a comprehensive testing infrastructure for the extended-google-doc-utils Python library, enabling secure OAuth-based testing across local development, cloud agents, and GitHub Actions CI/CD. The implementation uses a two-tier testing strategy: Tier A tests run without credentials using fixtures and mocks for broad accessibility, while Tier B tests require valid OAuth credentials to validate real Google Docs/Drive API integration. The infrastructure supports desktop OAuth with local callback servers for developers, environment-based credentials for automated testing, and GitHub Environment-based approval gates to protect credentials from untrusted code.

## Technical Context

**Language/Version**: Python 3.11+ (minimum version for modern type hints and async capabilities)
**Primary Dependencies**:
- `uv` (modern Python package manager for fast dependency management)
- `pytest` (testing framework with fixture support and plugin ecosystem)
- `google-auth-oauthlib` (Google OAuth 2.0 authentication flow)
- `google-auth-httplib2` (Google API client authentication)
- `google-api-python-client` (Google Docs and Drive API client)
- `pytest-mock` (mocking fixtures for Tier A tests)

**Storage**: Local file system for OAuth refresh tokens (`.credentials/` directory, gitignored)
**Testing**: pytest with custom markers (`@pytest.mark.tier_a`, `@pytest.mark.tier_b`)
**Target Platform**: Cross-platform (macOS, Linux, Windows) for local development; Linux containers for CI/CD and cloud agents
**Project Type**: Single Python library with testing infrastructure
**Performance Goals**:
- Pre-flight credential check: <2 seconds
- Local OAuth flow completion: <5 minutes (including user authentication)
- Test suite execution: <10 minutes in GitHub Actions
- Individual test execution: <5 seconds for proof-of-concept integration test

**Constraints**:
- No credentials in version control (enforced via .gitignore and pre-commit hooks)
- OAuth scopes limited to minimum required (docs, drive.file)
- Single-user authentication only (no multi-tenancy)
- GitHub Environment protection required for Tier B tests in CI
- Manual maintainer approval required for credential access

**Scale/Scope**:
- Single library for Google Docs markdown extension utilities
- ~5-10 integration tests (Tier B) initially
- ~20-30 unit tests (Tier A) using fixtures
- 1 proof-of-concept test validating end-to-end flow
- Support for parallel test execution across multiple environments

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with Extended Google Doc Utils Constitution v1.0.0:

- [x] **I. LLM-Friendly Format Design**: N/A - This feature implements testing infrastructure, not markdown syntax extensions
- [x] **II. Round-Trip Safety**: N/A - This feature implements testing infrastructure, not document processing
- [x] **III. Minimal Verbosity**: N/A - This feature implements testing infrastructure, not markup
- [x] **IV. Backward Compatibility**: PASS - This is the initial testing infrastructure; establishes foundation for future compatibility
- [x] **V. Specification-Driven Development**: PASS - Full specification in spec.md completed before implementation planning

**Testing Standards**:
- [x] Contract tests planned - Tier A tests will validate OAuth credential handling without real API calls
- [x] Round-trip tests planned - N/A for testing infrastructure; applicable to future document processing features
- [x] LLM integration tests planned - N/A for testing infrastructure; cloud agent testing validates LLM-driven development workflows
- [x] Edge case coverage identified - Comprehensive edge cases documented in spec.md (OAuth failures, network errors, credential expiry, etc.)

**Rationale**: This feature establishes testing infrastructure to enable future development of markdown extension features. The constitution principles (I-III) primarily govern markdown syntax design and will be evaluated in subsequent features that implement document processing capabilities. This infrastructure feature complies with principles IV (backward compatibility) and V (specification-driven development).

**Re-evaluation Status (Post-Phase 1)**: ✓ PASS - Constitution compliance verified after design phase. No violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
extended-google-doc-utils/
├── pyproject.toml              # Project metadata, dependencies, uv configuration
├── .python-version             # Python version specification for uv
├── uv.lock                     # Dependency lock file (uv-managed)
├── .gitignore                  # Excludes .credentials/, __pycache__, etc.
├── README.md                   # Project overview and setup instructions
│
├── src/
│   └── extended_google_doc_utils/
│       ├── __init__.py
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── oauth_flow.py        # Desktop OAuth flow with local callback
│       │   ├── credential_manager.py # Load/save/refresh credentials
│       │   └── preflight_check.py   # Pre-test credential validation
│       ├── google_api/
│       │   ├── __init__.py
│       │   ├── docs_client.py       # Google Docs API wrapper
│       │   └── drive_client.py      # Google Drive API wrapper
│       └── utils/
│           ├── __init__.py
│           └── config.py            # Environment detection, config loading
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration, custom markers, shared fixtures
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── google_docs_responses.json    # Mock API responses for Tier A tests
│   │   └── google_drive_responses.json
│   ├── tier_a/                  # Credential-free tests (fixtures/mocks)
│   │   ├── __init__.py
│   │   ├── test_auth_logic.py           # Test auth without real API calls
│   │   ├── test_docs_parsing.py         # Test document parsing with fixtures
│   │   └── test_config_loading.py       # Test configuration logic
│   └── tier_b/                  # Credential-required integration tests
│       ├── __init__.py
│       ├── test_oauth_flow.py           # Test real OAuth authentication
│       ├── test_proof_of_concept.py     # Read "Gondwana" doc test
│       └── test_resource_isolation.py   # Test dynamic resource creation
│
├── scripts/
│   ├── bootstrap_oauth.py       # Interactive OAuth setup script
│   └── cleanup_test_resources.py # Manual cleanup for orphaned resources
│
├── .credentials/                # Local OAuth tokens (gitignored)
│   └── token.json              # Refresh token storage (local dev only)
│
├── .github/
│   ├── workflows/
│   │   ├── tier-a-tests.yml    # Auto-run on all PRs
│   │   └── tier-b-tests.yml    # Requires manual approval via Environment
│   └── environments/
│       └── README.md           # Instructions for setting up protected environment
│
└── .specify/                    # Speckit workflow artifacts
    ├── memory/
    │   └── constitution.md
    └── templates/
        └── [speckit templates]
```

**Structure Decision**: Using **Option 1: Single Project** structure. This is a Python library with testing infrastructure, not a web application or mobile app. The project follows standard Python packaging conventions with `src/` layout (PEP 517/518) for clean imports and test isolation. The two-tier testing strategy is implemented via directory structure (`tests/tier_a/`, `tests/tier_b/`) with pytest markers for additional filtering.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. Constitution Check passed for all applicable principles.
