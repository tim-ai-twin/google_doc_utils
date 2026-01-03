# Data Model: Cloud Testing Infrastructure with OAuth

**Feature**: 001-cloud-testing-oauth
**Date**: 2026-01-02
**Status**: Phase 1 Design

## Overview

This document defines the core entities, their relationships, validation rules, and state transitions for the OAuth-based testing infrastructure. The data model focuses on credential management, test configuration, and resource tracking.

---

## Core Entities

### 1. OAuthCredentials

**Purpose**: Represents OAuth 2.0 credentials for Google API authentication

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `access_token` | `str` | Yes | Short-lived token for API requests | Non-empty string |
| `refresh_token` | `str` | Yes | Long-lived token for obtaining new access tokens | Non-empty string |
| `token_expiry` | `datetime` | Yes | Expiration timestamp for access token | Future datetime |
| `client_id` | `str` | Yes | OAuth client application identifier | Non-empty string |
| `client_secret` | `str` | Yes | OAuth client application secret | Non-empty string |
| `scopes` | `list[str]` | Yes | Requested OAuth scopes | Non-empty list, valid scope URLs |
| `token_uri` | `str` | Yes | Google's token endpoint URL | Valid HTTPS URL |

**Relationships**:
- Used by `TestExecutionContext` for API authentication
- Loaded by `CredentialManager` from file or environment

**State Transitions**:
```
[Created] → [Valid] → [Expired] → [Refreshed] → [Valid]
                ↓
           [Revoked] (terminal state)
```

**Validation Rules**:
- `access_token` must be non-empty when credentials are valid
- `refresh_token` must persist across token refreshes
- `token_expiry` must be checked before API calls
- `scopes` must include at minimum: `https://www.googleapis.com/auth/documents`

**Python Type Definition**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class OAuthCredentials:
    access_token: str
    refresh_token: str
    token_expiry: datetime
    client_id: str
    client_secret: str
    scopes: List[str]
    token_uri: str = "https://oauth2.googleapis.com/token"

    def is_expired(self) -> bool:
        """Check if access token is expired"""
        return datetime.utcnow() >= self.token_expiry

    def is_valid(self) -> bool:
        """Check if credentials have required fields"""
        return bool(
            self.access_token
            and self.refresh_token
            and self.client_id
            and self.client_secret
            and self.scopes
        )
```

---

### 2. CredentialSource

**Purpose**: Enum representing where credentials are loaded from

**Values**:
| Value | Description | Use Case |
|-------|-------------|----------|
| `LOCAL_FILE` | Loaded from `.credentials/token.json` | Local development |
| `ENVIRONMENT` | Loaded from environment variables | CI/CD, cloud agents |
| `NONE` | No credentials available | Tier A tests only |

**Validation Rules**:
- `LOCAL_FILE` requires `.credentials/token.json` to exist
- `ENVIRONMENT` requires `GOOGLE_OAUTH_REFRESH_TOKEN` env var at minimum

**Python Type Definition**:
```python
from enum import Enum

class CredentialSource(Enum):
    LOCAL_FILE = "local_file"
    ENVIRONMENT = "environment"
    NONE = "none"
```

---

### 3. TestExecutionContext

**Purpose**: Tracks runtime state during test execution

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `credentials` | `OAuthCredentials \| None` | No | Current OAuth credentials | Valid credentials or None |
| `credential_source` | `CredentialSource` | Yes | Where credentials were loaded from | Valid enum value |
| `environment_type` | `EnvironmentType` | Yes | Execution environment | Valid enum value |
| `tier_a_enabled` | `bool` | Yes | Whether Tier A tests can run | Always true |
| `tier_b_enabled` | `bool` | Yes | Whether Tier B tests can run | True only if credentials valid |
| `preflight_passed` | `bool` | Yes | Whether pre-flight check succeeded | Set before Tier B tests |

**Relationships**:
- Contains `OAuthCredentials` instance when available
- Used by pytest fixtures to configure test behavior

**State Transitions**:
```
[Initialized]
    ↓
[Credentials Loaded] (if available)
    ↓
[Pre-flight Check] (if Tier B tests requested)
    ↓
[Ready for Tests]
```

**Validation Rules**:
- `tier_b_enabled` must be `False` if `credentials` is `None`
- `preflight_passed` must be checked before running Tier B tests
- `credential_source` must be `NONE` if `credentials` is `None`

**Python Type Definition**:
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TestExecutionContext:
    credential_source: CredentialSource
    environment_type: 'EnvironmentType'
    tier_a_enabled: bool = True
    tier_b_enabled: bool = False
    preflight_passed: bool = False
    credentials: Optional[OAuthCredentials] = None

    def can_run_tier_b(self) -> bool:
        """Check if Tier B tests can execute"""
        return (
            self.tier_b_enabled
            and self.credentials is not None
            and self.credentials.is_valid()
            and self.preflight_passed
        )
```

---

### 4. EnvironmentType

**Purpose**: Enum representing test execution environment

**Values**:
| Value | Description | Credential Source | OAuth Flow |
|-------|-------------|-------------------|------------|
| `LOCAL` | Developer machine | `LOCAL_FILE` | Interactive desktop flow |
| `GITHUB_ACTIONS` | GitHub Actions CI | `ENVIRONMENT` | No interaction |
| `CLOUD_AGENT` | Cloud-based AI agent | `ENVIRONMENT` | No interaction |

**Detection Logic**:
- `GITHUB_ACTIONS`: Detected via `GITHUB_ACTIONS=true` environment variable
- `CLOUD_AGENT`: Detected via custom `CLOUD_AGENT=true` environment variable
- `LOCAL`: Default when neither above is set

**Python Type Definition**:
```python
import os
from enum import Enum

class EnvironmentType(Enum):
    LOCAL = "local"
    GITHUB_ACTIONS = "github_actions"
    CLOUD_AGENT = "cloud_agent"

    @classmethod
    def detect(cls) -> 'EnvironmentType':
        """Auto-detect current environment"""
        if os.getenv('GITHUB_ACTIONS') == 'true':
            return cls.GITHUB_ACTIONS
        elif os.getenv('CLOUD_AGENT') == 'true':
            return cls.CLOUD_AGENT
        else:
            return cls.LOCAL
```

---

### 5. TestResourceMetadata

**Purpose**: Tracks Google Docs/Drive resources created during tests

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `resource_id` | `str` | Yes | Google Docs/Drive file ID | Non-empty string |
| `resource_type` | `ResourceType` | Yes | Type of resource | Valid enum value |
| `title` | `str` | Yes | Resource title/name | Must include unique suffix |
| `created_at` | `datetime` | Yes | Creation timestamp | UTC datetime |
| `test_name` | `str` | Yes | Name of test that created it | Non-empty string |
| `cleanup_attempted` | `bool` | Yes | Whether cleanup was attempted | Boolean |
| `cleanup_succeeded` | `bool` | Yes | Whether cleanup succeeded | Boolean |

**Relationships**:
- Created during Tier B test execution
- Tracked for cleanup and debugging

**Validation Rules**:
- `title` must follow pattern: `test-{prefix}-{timestamp}-{random}`
- `resource_id` must be valid Google resource ID format
- `cleanup_attempted` must be `True` if `cleanup_succeeded` is `True`

**Python Type Definition**:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResourceMetadata:
    resource_id: str
    resource_type: 'ResourceType'
    title: str
    created_at: datetime
    test_name: str
    cleanup_attempted: bool = False
    cleanup_succeeded: bool = False

    def is_orphaned(self) -> bool:
        """Check if resource cleanup failed"""
        return self.cleanup_attempted and not self.cleanup_succeeded
```

---

### 6. ResourceType

**Purpose**: Enum representing Google resource types

**Values**:
| Value | Description | API |
|-------|-------------|-----|
| `DOCUMENT` | Google Docs document | Google Docs API |
| `FOLDER` | Google Drive folder | Google Drive API |
| `SPREADSHEET` | Google Sheets spreadsheet | Google Sheets API (future) |

**Python Type Definition**:
```python
from enum import Enum

class ResourceType(Enum):
    DOCUMENT = "document"
    FOLDER = "folder"
    SPREADSHEET = "spreadsheet"  # Future use
```

---

### 7. PreflightCheckResult

**Purpose**: Result of pre-flight credential validation

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `success` | `bool` | Yes | Whether check passed | Boolean |
| `error_message` | `str \| None` | No | Error message if failed | Non-empty if success=False |
| `check_duration_ms` | `int` | Yes | How long check took | Positive integer |
| `timestamp` | `datetime` | Yes | When check was performed | UTC datetime |

**Validation Rules**:
- `success` must be `False` if `error_message` is present
- `check_duration_ms` must be positive
- `check_duration_ms` should be < 2000 (2 seconds target)

**Python Type Definition**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PreflightCheckResult:
    success: bool
    check_duration_ms: int
    timestamp: datetime
    error_message: Optional[str] = None

    def is_within_target(self) -> bool:
        """Check if duration meets performance target"""
        return self.check_duration_ms < 2000
```

---

## Entity Relationships Diagram

```
TestExecutionContext
├── credentials: OAuthCredentials?
├── credential_source: CredentialSource
└── environment_type: EnvironmentType

OAuthCredentials
└── (loaded from CredentialManager)

TestResourceMetadata
├── resource_type: ResourceType
└── (created during Tier B tests)

PreflightCheckResult
└── (validates OAuthCredentials before Tier B tests)
```

---

## State Transition Diagrams

### Credential Lifecycle

```
[No Credentials]
    ↓ (bootstrap_oauth.py)
[Valid Credentials]
    ↓ (time passes)
[Expired Access Token]
    ↓ (auto-refresh)
[Valid Credentials]
    ↓ (revoked by user/Google)
[Invalid Credentials]
    ↓ (bootstrap_oauth.py)
[Valid Credentials]
```

### Test Execution Flow

```
[Test Suite Start]
    ↓
[Detect Environment] (LOCAL, GITHUB_ACTIONS, CLOUD_AGENT)
    ↓
[Load Credentials] (if available)
    ↓
[Pre-flight Check] (if Tier B requested)
    ↓
├─ [Success] → [Run Tier B Tests]
└─ [Failure] → [Skip Tier B Tests]
    ↓
[Cleanup Resources] (best effort)
    ↓
[Test Suite End]
```

### Test Resource Lifecycle

```
[Test Starts]
    ↓
[Create Resource] (with unique ID)
    ↓
[Use in Test]
    ↓
[Test Completes]
    ↓
[Attempt Cleanup]
    ├─ [Success] → [Resource Deleted]
    └─ [Failure] → [Orphaned Resource]
```

---

## Validation Rules Summary

### Cross-Entity Rules

1. **Tier B Execution Prerequisite**:
   - `TestExecutionContext.credentials` must be non-null
   - `OAuthCredentials.is_valid()` must return `True`
   - `TestExecutionContext.preflight_passed` must be `True`

2. **Credential Source Consistency**:
   - `EnvironmentType.LOCAL` → `CredentialSource.LOCAL_FILE` or `NONE`
   - `EnvironmentType.GITHUB_ACTIONS` → `CredentialSource.ENVIRONMENT`
   - `EnvironmentType.CLOUD_AGENT` → `CredentialSource.ENVIRONMENT` or `NONE`

3. **Test Resource Naming**:
   - All `TestResourceMetadata.title` must include timestamp from `created_at`
   - All titles must include random suffix for uniqueness

4. **Pre-flight Check Timing**:
   - `PreflightCheckResult` must exist before setting `TestExecutionContext.preflight_passed = True`
   - Pre-flight check should complete in <2 seconds

---

## File Storage Formats

### Local Credentials File (`.credentials/token.json`)

**Format**: JSON (compatible with `google-auth` library)

**Schema**:
```json
{
  "access_token": "ya29.a0AfB...",
  "refresh_token": "1//0gZ...",
  "token_expiry": "2026-01-02T18:30:00Z",
  "client_id": "123456789.apps.googleusercontent.com",
  "client_secret": "GOCSPX-...",
  "scopes": [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file"
  ],
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

**Security**:
- File permissions: `0600` (owner read/write only)
- Directory `.credentials/` must be in `.gitignore`
- Never commit to version control

---

### Environment Variables (CI/CD)

**Required Variables**:
```bash
GOOGLE_OAUTH_REFRESH_TOKEN="1//0gZ..."
GOOGLE_OAUTH_CLIENT_ID="123456789.apps.googleusercontent.com"
GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-..."
```

**Optional Variables**:
```bash
GOOGLE_OAUTH_SCOPES="https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive.file"
GITHUB_ACTIONS="true"  # Auto-set by GitHub Actions
CLOUD_AGENT="true"     # Set manually in cloud agent environments
```

---

## Usage Examples

### Loading Credentials in Local Environment

```python
from src.extended_google_doc_utils.auth.credential_manager import CredentialManager
from src.extended_google_doc_utils.utils.config import EnvironmentType

env_type = EnvironmentType.detect()
cred_manager = CredentialManager(env_type)

try:
    credentials = cred_manager.load_credentials()
    print(f"Loaded credentials from {cred_manager.source}")
except FileNotFoundError:
    print("No credentials found. Run: uv run scripts/bootstrap_oauth.py")
```

### Creating Test Resource with Unique ID

```python
from src.extended_google_doc_utils.google_api.docs_client import DocsClient
from datetime import datetime
import secrets

def create_test_document(client: DocsClient, test_name: str) -> str:
    """Create a test document with unique identifier"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(4)
    title = f"test-doc-{timestamp}-{random_suffix}"

    doc = client.create_document(title)
    resource_id = doc['documentId']

    # Track for cleanup
    metadata = TestResourceMetadata(
        resource_id=resource_id,
        resource_type=ResourceType.DOCUMENT,
        title=title,
        created_at=datetime.utcnow(),
        test_name=test_name
    )

    return resource_id
```

### Pre-flight Check in pytest

```python
import pytest
from src.extended_google_doc_utils.auth.preflight_check import run_preflight_check

@pytest.fixture(scope="session", autouse=True)
def tier_b_preflight(request, test_context: TestExecutionContext):
    """Run pre-flight check before Tier B tests"""
    if not test_context.tier_b_enabled:
        return  # Skip if not running Tier B

    result = run_preflight_check(test_context.credentials)

    if not result.success:
        pytest.skip(f"Pre-flight check failed: {result.error_message}")

    test_context.preflight_passed = True
    print(f"✓ Pre-flight check passed ({result.check_duration_ms}ms)")
```

---

## Design Rationale

### Why Separate Credential Source and Environment Type?

- **Decoupling**: Environment (where code runs) vs credential location (where secrets stored)
- **Flexibility**: Local environment could use environment variables for testing
- **Clarity**: Explicit about credential provenance for debugging

### Why Track Test Resources?

- **Debugging**: When tests fail, know what resources were created
- **Cleanup**: Enable bulk cleanup of orphaned resources
- **Auditing**: Understand resource creation patterns and costs

### Why Pre-flight Check?

- **Fast failure**: Detect auth issues in 2s instead of waiting for first test to fail
- **Clear errors**: Single error message vs many test failures
- **User experience**: Immediate actionable feedback

---

**Data Model Status**: ✓ Complete
**Next Steps**: Generate API contracts and quickstart guide
