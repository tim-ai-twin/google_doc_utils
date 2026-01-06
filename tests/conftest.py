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
    # Initialize pre-flight result storage
    config.preflight_result = None


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
    """Auto-skip Tier B tests if credentials are unavailable or pre-flight check failed."""
    tier_b_marker = item.get_closest_marker("tier_b")
    if tier_b_marker:
        # First check if credentials are available
        if not _credentials_available():
            pytest.skip("Tier B tests require credentials")

        # Then check if pre-flight check failed
        preflight_result = item.config.preflight_result
        if preflight_result is not None and not preflight_result.success:
            pytest.skip("Skipping Tier B: pre-flight check failed")


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


@pytest.fixture(scope="session", autouse=True)
def preflight_check(request, google_credentials):
    """Run pre-flight check before any tests to validate credentials.

    This fixture automatically validates credentials once per test session using
    a lightweight Drive API call. If pre-flight fails, Tier B tests will be skipped.

    Args:
        request: Pytest request object for accessing config
        google_credentials: Loaded OAuth credentials from google_credentials fixture

    Returns:
        PreflightCheckResult | None: Result of pre-flight check, or None if no credentials
    """
    from extended_google_doc_utils.auth.preflight_check import PreflightCheck

    # If no credentials available, skip pre-flight check
    if google_credentials is None:
        request.config.preflight_result = None
        return None

    # Run pre-flight check
    checker = PreflightCheck(google_credentials)
    result = checker.run()

    # Store result in config for pytest hooks to access
    request.config.preflight_result = result

    # Display result
    if result.success:
        print(f"\n✓ Pre-flight check passed for {result.user_email} ({result.elapsed_time:.1f}s)")
    else:
        print(f"\n✗ Pre-flight check failed: {result.error_message}")
        print("Tier B tests will be skipped")

    return result


@pytest.fixture(scope="session")
def resource_manager(google_credentials):
    """Provide a TestResourceManager for Tier B tests.

    Session-scoped fixture that creates a TestResourceManager instance
    and automatically cleans up all tracked resources at session end.

    Args:
        google_credentials: OAuth credentials from google_credentials fixture

    Yields:
        TestResourceManager: Manager for creating and tracking test resources
    """
    from extended_google_doc_utils.utils.test_resources import TestResourceManager

    manager = TestResourceManager(credentials=google_credentials)

    yield manager

    # Cleanup all tracked resources at session end
    succeeded, failed = manager.cleanup_all()
    if succeeded > 0 or failed > 0:
        print(f"\n🧹 Resource cleanup: {succeeded} succeeded, {failed} failed")
        orphaned = manager.list_orphaned_resources()
        if orphaned:
            print("⚠️  Orphaned resources (manual cleanup needed):")
            for r in orphaned:
                print(f"   - {r.resource_type.value}: {r.resource_id} ({r.title})")
