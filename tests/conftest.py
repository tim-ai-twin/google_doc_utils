"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path

import pytest


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "tier_a: Tier A tests - credential-free, use mocks"
    )
    config.addinivalue_line(
        "markers", "tier_b: Tier B tests - require Google Cloud credentials"
    )
    config.addinivalue_line(
        "markers", "manual: Manual/interactive tests requiring human interaction"
    )


def _credentials_available() -> bool:
    """Check if Google Cloud credentials are available.

    Returns:
        bool: True if credentials are available, False otherwise
    """
    # Check for local credentials file
    credentials_path = Path(".credentials/token.json")
    if credentials_path.exists():
        return True

    # Check for environment variables (common in CI/CD)
    env_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "GOOGLE_OAUTH_REFRESH_TOKEN",
    ]
    return any(os.getenv(var) for var in env_vars)


def pytest_runtest_setup(item):
    """Auto-skip Tier B tests if credentials are unavailable."""
    tier_b_marker = item.get_closest_marker("tier_b")
    if tier_b_marker and not _credentials_available():
        pytest.skip("Tier B tests require credentials")


@pytest.fixture(scope="session")
def google_credentials():
    """Load Google OAuth credentials for Tier B tests.

    This fixture uses CredentialManager to load credentials from the appropriate
    source (local file in development, environment variables in CI/CD).

    The fixture will automatically refresh expired tokens if needed.

    Returns:
        OAuthCredentials | None: Valid credentials if available, None otherwise

    Yields:
        OAuthCredentials | None: Credentials for use in tests
    """
    from extended_google_doc_utils.auth.credential_manager import (
        CredentialManager,
        CredentialSourceDetector,
    )

    # Auto-detect environment and credential source
    env_type = CredentialSourceDetector.detect_environment()
    credential_source = CredentialSourceDetector.get_credential_source(env_type)

    # Load credentials
    manager = CredentialManager(source=credential_source)
    credentials = manager.get_credentials_for_testing()

    yield credentials
