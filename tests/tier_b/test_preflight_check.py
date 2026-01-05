"""Tier B tests for pre-flight credential check.

These tests validate the pre-flight check with real Google Cloud credentials
and actual Drive API calls.
"""

import pytest

from extended_google_doc_utils.auth.preflight_check import PreflightCheck


@pytest.mark.tier_b
def test_preflight_with_real_credentials(google_credentials):
    """Test pre-flight check with real credentials and Drive API.

    This validates end-to-end pre-flight check functionality:
    1. Uses real OAuth credentials (from fixture)
    2. Makes actual Drive API call to about.get()
    3. Validates pre-flight succeeds
    4. Checks timing is acceptable (<2s target)

    Prerequisites:
        - Valid Google OAuth credentials available
        - Credentials have Drive API access

    Args:
        google_credentials: OAuth credentials fixture from conftest.py
    """
    # Create pre-flight checker with real credentials
    checker = PreflightCheck(google_credentials)

    # Execute pre-flight check with real API call
    result = checker.run()

    # Verify pre-flight succeeded
    assert result.success is True, (
        f"Pre-flight check failed: {result.error_message}"
    )

    # Verify no error message on success
    assert result.error_message is None, (
        "Error message should be None on successful pre-flight"
    )

    # Verify user email was extracted
    assert result.user_email is not None, (
        "User email should be populated on successful pre-flight"
    )
    assert "@" in result.user_email, (
        f"User email should be valid email address, got: {result.user_email}"
    )

    # Verify timing is measured
    assert result.elapsed_time > 0, (
        "Elapsed time should be positive"
    )

    # Verify timing meets performance target (<2s)
    assert result.elapsed_time < 2.0, (
        f"Pre-flight check took {result.elapsed_time:.2f}s, "
        f"target is <2s. Check network connectivity."
    )

    # Print results for manual verification
    print(f"\n✓ Pre-flight check successful:")
    print(f"  User: {result.user_email}")
    print(f"  Time: {result.elapsed_time:.2f}s")
