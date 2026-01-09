# Architecture Overview

This document describes the architecture of the Extended Google Doc Utils library.

## Module Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        extended_google_doc_utils                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐  │
│  │        auth/        │    │     google_api/     │    │     utils/      │  │
│  ├─────────────────────┤    ├─────────────────────┤    ├─────────────────┤  │
│  │ credential_manager  │───▶│    docs_client      │    │    config       │  │
│  │                     │    │                     │    │                 │  │
│  │ oauth_flow          │    │    drive_client     │    │   logging       │  │
│  │                     │    │                     │    │                 │  │
│  │ preflight_check     │───▶│                     │    │ test_resources  │  │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────┘  │
│           │                          │                          │           │
│           │                          │                          │           │
│           └──────────────────────────┼──────────────────────────┘           │
│                                      │                                       │
│                                      ▼                                       │
│                          ┌─────────────────────┐                            │
│                          │   Google APIs       │                            │
│                          │  (Docs, Drive)      │                            │
│                          └─────────────────────┘                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Module Descriptions

| Module | Purpose |
|--------|---------|
| `auth/credential_manager` | Load, save, refresh OAuth credentials |
| `auth/oauth_flow` | Desktop OAuth flow with local callback server |
| `auth/preflight_check` | Validate credentials before test execution |
| `google_api/docs_client` | Google Docs API wrapper (CRUD operations) |
| `google_api/drive_client` | Google Drive API wrapper (file management) |
| `utils/config` | Environment detection and configuration |
| `utils/logging` | Structured logging utilities |
| `utils/test_resources` | Test resource lifecycle management |

## OAuth Authentication Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Developer  │     │ OAuth Flow   │     │   Google     │     │  Callback    │
│   (Browser)  │     │   (Local)    │     │   OAuth      │     │   Server     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  1. Run bootstrap  │                    │                    │
       │ ──────────────────▶│                    │                    │
       │                    │                    │                    │
       │                    │  2. Start server   │                    │
       │                    │ ──────────────────────────────────────▶│
       │                    │                    │                    │
       │  3. Open auth URL  │                    │                    │
       │ ◀──────────────────│                    │                    │
       │                    │                    │                    │
       │  4. Login & consent│                    │                    │
       │ ──────────────────────────────────────▶│                    │
       │                    │                    │                    │
       │                    │                    │  5. Redirect +     │
       │                    │                    │     auth code      │
       │ ◀──────────────────────────────────────────────────────────│
       │                    │                    │                    │
       │                    │  6. Receive code   │                    │
       │                    │ ◀──────────────────────────────────────│
       │                    │                    │                    │
       │                    │  7. Exchange for   │                    │
       │                    │     tokens         │                    │
       │                    │ ──────────────────▶│                    │
       │                    │                    │                    │
       │                    │  8. Access +       │                    │
       │                    │     Refresh tokens │                    │
       │                    │ ◀──────────────────│                    │
       │                    │                    │                    │
       │  9. Save to        │                    │                    │
       │     .credentials/  │                    │                    │
       │ ◀──────────────────│                    │                    │
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
```

### Credential Sources

```
┌─────────────────────────────────────────────────────────────────┐
│                    CredentialManager                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│   │   LOCAL_FILE    │  │   ENVIRONMENT   │  │  AUTO_DETECT    │ │
│   ├─────────────────┤  ├─────────────────┤  ├─────────────────┤ │
│   │                 │  │                 │  │                 │ │
│   │ .credentials/   │  │ GOOGLE_OAUTH_*  │  │ Check file      │ │
│   │   token.json    │  │ env variables   │  │ then env vars   │ │
│   │                 │  │                 │  │                 │ │
│   │ Local dev       │  │ CI/CD, Cloud    │  │ Flexible        │ │
│   │ (gitignored)    │  │ agents          │  │ deployment      │ │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Test Tier Separation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Test Suite                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────────────────────────┐   ┌───────────────────────────────┐    │
│   │         TIER A                │   │         TIER B                │    │
│   │   (Credential-Free)           │   │   (Credential-Required)       │    │
│   ├───────────────────────────────┤   ├───────────────────────────────┤    │
│   │                               │   │                               │    │
│   │  ┌─────────────────────────┐  │   │  ┌──────────────────────────┐ │    │
│   │  │ test_auth_logic.py     │  │   │  │ test_preflight_check.py  │ │    │
│   │  │ test_config_loading.py │  │   │  │ test_proof_of_concept.py │ │    │
│   │  │ test_docs_client.py    │  │   │  │ test_resource_isolation.py│ │    │
│   │  │ test_docs_parsing.py   │  │   │  └──────────────────────────┘ │    │
│   │  │ test_preflight_logic.py│  │   │                               │    │
│   │  └─────────────────────────┘  │   │  Real Google API calls       │    │
│   │                               │   │  Requires OAuth credentials  │    │
│   │  Uses mocks and fixtures      │   │  Manual approval in CI       │    │
│   │  No network required          │   │                               │    │
│   │  Runs on all PRs              │   │                               │    │
│   │                               │   │                               │    │
│   └───────────────────────────────┘   └───────────────────────────────┘    │
│                                                                              │
│   pytest -m tier_a                    pytest -m tier_b                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Test Execution Flow

```
                              ┌─────────────────┐
                              │  pytest starts  │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Load conftest   │
                              │ Register markers│
                              └────────┬────────┘
                                       │
                                       ▼
                    ┌──────────────────┴──────────────────┐
                    │                                      │
                    ▼                                      ▼
           ┌───────────────┐                     ┌───────────────┐
           │   Tier A?     │                     │   Tier B?     │
           └───────┬───────┘                     └───────┬───────┘
                   │                                     │
                   ▼                                     ▼
           ┌───────────────┐                     ┌───────────────┐
           │  Run with     │                     │  Check creds  │
           │  mocks        │                     │  available?   │
           └───────┬───────┘                     └───────┬───────┘
                   │                                     │
                   ▼                             ┌───────┴───────┐
           ┌───────────────┐                     │               │
           │    PASS       │                     ▼               ▼
           └───────────────┘              ┌──────────┐    ┌──────────┐
                                          │   Yes    │    │    No    │
                                          └────┬─────┘    └────┬─────┘
                                               │               │
                                               ▼               ▼
                                        ┌──────────┐    ┌──────────┐
                                        │ Preflight│    │   SKIP   │
                                        │  check   │    │ (message)│
                                        └────┬─────┘    └──────────┘
                                             │
                                     ┌───────┴───────┐
                                     │               │
                                     ▼               ▼
                              ┌──────────┐    ┌──────────┐
                              │  PASS    │    │  FAIL    │
                              └────┬─────┘    └────┬─────┘
                                   │               │
                                   ▼               ▼
                            ┌──────────┐    ┌──────────┐
                            │ Run test │    │   SKIP   │
                            │ with API │    │ all Tier │
                            └──────────┘    │    B     │
                                            └──────────┘
```

## Directory Structure

```
google_doc_utils/
├── src/
│   └── extended_google_doc_utils/
│       ├── __init__.py
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── credential_manager.py   # Credential lifecycle
│       │   ├── oauth_flow.py           # Desktop OAuth
│       │   └── preflight_check.py      # Credential validation
│       ├── google_api/
│       │   ├── __init__.py
│       │   ├── docs_client.py          # Docs API wrapper
│       │   └── drive_client.py         # Drive API wrapper
│       └── utils/
│           ├── __init__.py
│           ├── config.py               # Environment config
│           ├── logging.py              # Logging utilities
│           └── test_resources.py       # Test resource mgmt
│
├── tests/
│   ├── conftest.py                     # Shared fixtures, markers
│   ├── fixtures/                       # Mock API responses
│   ├── tier_a/                         # Credential-free tests
│   └── tier_b/                         # Integration tests
│
├── scripts/
│   ├── bootstrap_oauth.py              # Initial OAuth setup
│   └── cleanup_test_resources.py       # Orphan cleanup
│
├── .credentials/                       # Local tokens (gitignored)
│
└── .github/
    ├── workflows/
    │   ├── tier-a-tests.yml            # Auto-run on PRs
    │   └── tier-b-tests.yml            # Requires approval
    └── environments/
        └── README.md                   # Environment setup guide
```

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PR Created/Updated                                                         │
│         │                                                                    │
│         ├────────────────────────────┬───────────────────────────┐          │
│         │                            │                           │          │
│         ▼                            ▼                           ▼          │
│   ┌───────────┐              ┌───────────────┐          ┌──────────────┐   │
│   │ Tier A    │              │   Tier B      │          │   Tier B     │   │
│   │ Tests     │              │   (Waiting)   │          │   Approved   │   │
│   │           │              │               │          │              │   │
│   │ Automatic │              │ Requires      │   ───▶   │ Runs with    │   │
│   │ No creds  │              │ maintainer    │          │ credentials  │   │
│   │           │              │ approval      │          │              │   │
│   └─────┬─────┘              └───────────────┘          └──────┬───────┘   │
│         │                                                       │          │
│         ▼                                                       ▼          │
│   ┌───────────┐                                          ┌───────────┐    │
│   │  Results  │                                          │  Results  │    │
│   │  on PR    │                                          │  on PR    │    │
│   └───────────┘                                          └───────────┘    │
│                                                                              │
│   Environment: tier-b-testing                                               │
│   Secrets: GOOGLE_OAUTH_CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
