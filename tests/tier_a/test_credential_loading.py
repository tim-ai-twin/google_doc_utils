"""Tier A tests for credential loading functionality."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    CredentialSource,
    OAuthCredentials,
)


@pytest.fixture
def temp_credentials_dir(tmp_path, monkeypatch):
    """Create a temporary .credentials directory for testing."""
    creds_dir = tmp_path / ".credentials"
    creds_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    return creds_dir


@pytest.fixture
def sample_credentials_data():
    """Sample credentials data for testing."""
    expiry = datetime.now(UTC) + timedelta(hours=1)
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_expiry": expiry.isoformat(),
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scopes": ["https://www.googleapis.com/auth/documents"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def test_load_credentials_file_not_found(temp_credentials_dir):
    """Test that load_credentials returns None when file doesn't exist."""
    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    result = manager.load_credentials()
    assert result is None


def test_load_credentials_success(temp_credentials_dir, sample_credentials_data):
    """Test successful loading of credentials from local file."""
    # Write sample credentials to file
    token_file = temp_credentials_dir / "token.json"
    with open(token_file, "w") as f:
        json.dump(sample_credentials_data, f)

    # Load credentials
    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    result = manager.load_credentials()

    # Verify credentials were loaded correctly
    assert result is not None
    assert isinstance(result, OAuthCredentials)
    assert result.access_token == "test_access_token"
    assert result.refresh_token == "test_refresh_token"
    assert result.client_id == "test_client_id"
    assert result.client_secret == "test_client_secret"
    assert result.scopes == ["https://www.googleapis.com/auth/documents"]
    assert result.token_uri == "https://oauth2.googleapis.com/token"
    assert isinstance(result.token_expiry, datetime)


def test_load_credentials_malformed_json(temp_credentials_dir):
    """Test that load_credentials returns None for malformed JSON."""
    token_file = temp_credentials_dir / "token.json"
    with open(token_file, "w") as f:
        f.write("not valid json{")

    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    result = manager.load_credentials()
    assert result is None


def test_load_credentials_missing_fields(temp_credentials_dir):
    """Test that load_credentials returns None when required fields are missing."""
    # Write incomplete credentials (missing client_id)
    token_file = temp_credentials_dir / "token.json"
    incomplete_data = {
        "access_token": "test_token",
        "refresh_token": "test_refresh",
    }
    with open(token_file, "w") as f:
        json.dump(incomplete_data, f)

    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    result = manager.load_credentials()
    assert result is None


def test_load_credentials_none_source():
    """Test that load_credentials returns None for NONE source."""
    manager = CredentialManager(CredentialSource.NONE)
    result = manager.load_credentials()
    assert result is None
