"""Tier A tests for pre-flight check logic.

These tests validate the pre-flight credential check functionality
without making real API calls. All external dependencies are mocked.
"""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from extended_google_doc_utils.auth.credential_manager import OAuthCredentials
from extended_google_doc_utils.auth.preflight_check import (
    PreflightCheck,
)


@pytest.fixture
def sample_oauth_credentials():
    """Sample OAuthCredentials instance for testing."""
    return OAuthCredentials(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
        client_id="test_client_id.apps.googleusercontent.com",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
        token_uri="https://oauth2.googleapis.com/token",
    )


@pytest.mark.tier_a
@patch("extended_google_doc_utils.auth.preflight_check.build")
@patch("extended_google_doc_utils.auth.preflight_check.Credentials")
def test_preflight_success_mock(
    mock_credentials_class,
    mock_build,
    sample_oauth_credentials,
):
    """Test pre-flight check with mocked successful API call.

    This validates the success path:
    1. Converts OAuthCredentials to google.oauth2.credentials.Credentials
    2. Builds Drive API service
    3. Makes Drive about.get() call
    4. Extracts user email from response
    5. Returns successful PreflightCheckResult
    """
    # Set up mock google credentials
    mock_google_creds = Mock()
    mock_credentials_class.return_value = mock_google_creds

    # Set up mock Drive API service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Set up mock API response
    mock_about = Mock()
    mock_about.get.return_value.execute.return_value = {
        "user": {"emailAddress": "test@example.com"}
    }
    mock_service.about.return_value = mock_about

    # Run pre-flight check
    checker = PreflightCheck(sample_oauth_credentials)
    result = checker.run()

    # Verify Credentials was instantiated correctly
    mock_credentials_class.assert_called_once_with(
        token="test_access_token",
        refresh_token="test_refresh_token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client_id.apps.googleusercontent.com",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    # Verify Drive API service was built
    mock_build.assert_called_once_with("drive", "v3", credentials=mock_google_creds)

    # Verify about.get() was called with correct fields
    mock_about.get.assert_called_once_with(fields="user")

    # Verify result is successful
    assert result.success is True
    assert result.error_message is None
    assert result.user_email == "test@example.com"
    assert result.elapsed_time > 0
    assert result.elapsed_time < 1.0  # Should be very fast with mocks


@pytest.mark.tier_a
@patch("extended_google_doc_utils.auth.preflight_check.build")
@patch("extended_google_doc_utils.auth.preflight_check.Credentials")
def test_preflight_failure_mock(
    mock_credentials_class,
    mock_build,
    sample_oauth_credentials,
):
    """Test pre-flight check with mocked failed API call.

    This validates the error handling path:
    1. Mocks an API exception
    2. Ensures exception is caught and converted to failed result
    3. Returns PreflightCheckResult with error details
    """
    # Set up mock google credentials
    mock_google_creds = Mock()
    mock_credentials_class.return_value = mock_google_creds

    # Set up mock to raise an exception
    mock_build.side_effect = Exception("Invalid credentials: Token has been expired or revoked")

    # Run pre-flight check
    checker = PreflightCheck(sample_oauth_credentials)
    result = checker.run()

    # Verify result indicates failure
    assert result.success is False
    assert result.error_message == "Invalid credentials: Token has been expired or revoked"
    assert result.user_email is None
    assert result.elapsed_time > 0


@pytest.mark.tier_a
@patch("extended_google_doc_utils.auth.preflight_check.build")
@patch("extended_google_doc_utils.auth.preflight_check.Credentials")
def test_preflight_timing(
    mock_credentials_class,
    mock_build,
    sample_oauth_credentials,
):
    """Test that pre-flight check accurately measures timing.

    This validates:
    1. Elapsed time is measured correctly
    2. Fast operations (mocked) complete in < 1s
    3. Simulated slow operations are detected and measured
    """
    # Set up mock google credentials
    mock_google_creds = Mock()
    mock_credentials_class.return_value = mock_google_creds

    # Set up mock Drive API service with artificial delay
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Add a small delay to simulate API call
    def delayed_execute():
        time.sleep(0.1)  # 100ms delay
        return {"user": {"emailAddress": "test@example.com"}}

    mock_about = Mock()
    mock_about.get.return_value.execute = delayed_execute
    mock_service.about.return_value = mock_about

    # Run pre-flight check
    checker = PreflightCheck(sample_oauth_credentials)
    result = checker.run()

    # Verify timing measurement
    assert result.success is True
    assert result.elapsed_time >= 0.1  # At least the delay we added
    assert result.elapsed_time < 0.5   # But not excessively long
