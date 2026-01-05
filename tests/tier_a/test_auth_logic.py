"""Tier A tests for authentication logic.

These tests focus on credential loading and refresh logic without
requiring real files or API calls. All external dependencies are mocked.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    CredentialSource,
    InvalidCredentialsError,
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
def sample_oauth_credentials():
    """Sample OAuthCredentials instance for testing."""
    return OAuthCredentials(
        access_token="old_access_token",
        refresh_token="test_refresh_token",
        token_expiry=datetime.now(UTC) - timedelta(hours=1),  # Expired
        client_id="test_client_id.apps.googleusercontent.com",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/documents"],
        token_uri="https://oauth2.googleapis.com/token",
    )


@pytest.mark.tier_a
def test_load_credentials_file_not_found(temp_credentials_dir):
    """Test that load_credentials returns None when file doesn't exist.

    This validates the behavior when no credentials file is present,
    which is expected for fresh installations or Tier A tests.
    """
    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    result = manager.load_credentials()
    assert result is None


@pytest.mark.tier_a
def test_load_credentials_invalid_json(temp_credentials_dir):
    """Test that load_credentials raises InvalidCredentialsError for invalid JSON.

    This validates error handling when the credentials file exists
    but contains malformed JSON data.
    """
    # Create a file with invalid JSON
    token_file = temp_credentials_dir / "token.json"
    with open(token_file, "w") as f:
        f.write("not valid json{[")

    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    with pytest.raises(InvalidCredentialsError) as exc_info:
        manager.load_credentials()

    # Verify error message is helpful
    assert "Failed to parse credentials file" in str(exc_info.value)
    assert "bootstrap_oauth.py" in str(exc_info.value)


@pytest.mark.tier_a
@patch("extended_google_doc_utils.auth.credential_manager.Request")
@patch("extended_google_doc_utils.auth.credential_manager.Credentials")
def test_refresh_token_logic(
    mock_credentials_class,
    mock_request_class,
    sample_oauth_credentials,
):
    """Test refresh_access_token with mocked google.auth dependencies.

    This validates the token refresh flow without making actual API calls:
    1. Creates google.oauth2.credentials.Credentials object
    2. Calls refresh() with a Request object
    3. Extracts updated token and expiry
    4. Returns new OAuthCredentials with refreshed values
    """
    # Set up the mock google credentials object
    mock_google_creds = MagicMock()
    mock_google_creds.token = "new_access_token"
    mock_google_creds.refresh_token = "test_refresh_token"
    new_expiry = datetime.now(UTC) + timedelta(hours=1)
    mock_google_creds.expiry = new_expiry
    mock_credentials_class.return_value = mock_google_creds

    # Set up the mock request object
    mock_request = Mock()
    mock_request_class.return_value = mock_request

    # Test the refresh logic
    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    refreshed = manager.refresh_access_token(sample_oauth_credentials)

    # Verify Credentials was instantiated with correct parameters
    mock_credentials_class.assert_called_once_with(
        token="old_access_token",
        refresh_token="test_refresh_token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client_id.apps.googleusercontent.com",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/documents"],
    )

    # Verify refresh was called with the request object
    mock_google_creds.refresh.assert_called_once_with(mock_request)

    # Verify the returned credentials have updated values
    assert refreshed.access_token == "new_access_token"
    assert refreshed.refresh_token == "test_refresh_token"
    assert refreshed.token_expiry == new_expiry

    # Verify other fields remain unchanged
    assert refreshed.client_id == sample_oauth_credentials.client_id
    assert refreshed.client_secret == sample_oauth_credentials.client_secret
    assert refreshed.scopes == sample_oauth_credentials.scopes
    assert refreshed.token_uri == sample_oauth_credentials.token_uri


@pytest.mark.tier_a
@patch("extended_google_doc_utils.auth.credential_manager.Request")
@patch("extended_google_doc_utils.auth.credential_manager.Credentials")
def test_refresh_token_logic_with_naive_datetime(
    mock_credentials_class,
    mock_request_class,
    sample_oauth_credentials,
):
    """Test refresh_access_token handles naive datetime from google.auth.

    Google's library may return timezone-naive datetimes. This test
    verifies that we correctly convert them to UTC timezone-aware.
    """
    # Set up mock with naive datetime (no timezone)
    mock_google_creds = MagicMock()
    mock_google_creds.token = "new_access_token"
    mock_google_creds.refresh_token = "test_refresh_token"
    naive_expiry = datetime.now()  # Naive datetime without timezone
    mock_google_creds.expiry = naive_expiry
    mock_credentials_class.return_value = mock_google_creds

    mock_request = Mock()
    mock_request_class.return_value = mock_request

    # Test the refresh logic
    manager = CredentialManager(CredentialSource.LOCAL_FILE)
    refreshed = manager.refresh_access_token(sample_oauth_credentials)

    # Verify the expiry has UTC timezone
    assert refreshed.token_expiry is not None
    assert refreshed.token_expiry.tzinfo == UTC


@pytest.mark.tier_a
@patch.dict(
    "os.environ",
    {
        "GOOGLE_OAUTH_CLIENT_ID": "test_client_id.apps.googleusercontent.com",
        "GOOGLE_OAUTH_CLIENT_SECRET": "test_client_secret",
        "GOOGLE_OAUTH_REFRESH_TOKEN": "test_refresh_token",
    },
)
def test_load_credentials_from_environment():
    """Test loading credentials from environment variables.

    This validates that credentials can be loaded from environment variables
    when ENVIRONMENT source is specified, without requiring a local file.
    """
    manager = CredentialManager(CredentialSource.ENVIRONMENT)
    result = manager.load_credentials()

    # Verify credentials were loaded
    assert result is not None
    assert isinstance(result, OAuthCredentials)

    # Verify required fields from environment variables
    assert result.client_id == "test_client_id.apps.googleusercontent.com"
    assert result.client_secret == "test_client_secret"
    assert result.refresh_token == "test_refresh_token"

    # Verify default values
    assert result.access_token == ""  # Will be obtained via refresh
    assert result.token_uri == "https://oauth2.googleapis.com/token"

    # Verify default scopes
    assert result.scopes == [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file",
    ]

    # Verify token_expiry is set to past date (forces refresh)
    assert result.token_expiry is not None
    assert result.token_expiry < datetime.now(UTC)


@pytest.mark.tier_a
@patch.dict(
    "os.environ",
    {
        "GOOGLE_OAUTH_CLIENT_ID": "test_client_id.apps.googleusercontent.com",
        "GOOGLE_OAUTH_CLIENT_SECRET": "test_client_secret",
        "GOOGLE_OAUTH_REFRESH_TOKEN": "test_refresh_token",
        "GOOGLE_OAUTH_SCOPES": "https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive",
    },
)
def test_load_credentials_from_environment_with_custom_scopes():
    """Test loading credentials with custom scopes from environment.

    This validates that the GOOGLE_OAUTH_SCOPES environment variable
    is correctly parsed as a comma-separated list of scopes.
    """
    manager = CredentialManager(CredentialSource.ENVIRONMENT)
    result = manager.load_credentials()

    # Verify custom scopes were parsed correctly
    assert result is not None
    assert result.scopes == [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ]


@pytest.mark.tier_a
@patch.dict("os.environ", {}, clear=True)
def test_load_credentials_from_environment_missing_vars():
    """Test that load_credentials returns None when env vars are missing.

    This validates the behavior when required environment variables
    are not set, which is expected for local development.
    """
    manager = CredentialManager(CredentialSource.ENVIRONMENT)
    result = manager.load_credentials()

    # Verify None is returned when environment variables are missing
    assert result is None


@pytest.mark.tier_a
@patch.dict(
    "os.environ",
    {
        "GOOGLE_OAUTH_CLIENT_ID": "test_client_id.apps.googleusercontent.com",
        # Missing CLIENT_SECRET and REFRESH_TOKEN
    },
)
def test_load_credentials_from_environment_partial_vars():
    """Test that load_credentials returns None when some env vars are missing.

    This validates that all required environment variables must be present,
    and missing any one of them results in None being returned.
    """
    manager = CredentialManager(CredentialSource.ENVIRONMENT)
    result = manager.load_credentials()

    # Verify None is returned when some required vars are missing
    assert result is None
