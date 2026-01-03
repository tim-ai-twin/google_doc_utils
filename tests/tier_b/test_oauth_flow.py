"""Tier B tests for OAuth flow.

These tests validate the full OAuth 2.0 authorization code flow
with real browser interaction and Google OAuth servers.

Run manual tests with: pytest -m manual
"""

import os
from datetime import UTC, datetime

import pytest

from extended_google_doc_utils.auth.oauth_flow import OAuthFlow


def _get_oauth_config():
    """Get OAuth configuration from environment variables.

    Returns:
        tuple: (client_id, client_secret, scopes) or None if not configured
    """
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    # Default scopes for testing
    scopes = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file",
    ]

    return client_id, client_secret, scopes


@pytest.mark.tier_b
@pytest.mark.manual
def test_oauth_flow_integration():
    """Test full OAuth flow with manual browser interaction.

    This is a manual/interactive test that:
    1. Starts a local callback server on localhost:8080-8089
    2. Opens browser for user to authorize
    3. Receives authorization code via callback
    4. Exchanges code for access and refresh tokens
    5. Validates the returned credentials

    **This test requires manual interaction** and will:
    - Open your default browser
    - Require you to log in to Google
    - Request OAuth consent for the specified scopes

    **Prerequisites:**
    - Set GOOGLE_OAUTH_CLIENT_ID environment variable
    - Set GOOGLE_OAUTH_CLIENT_SECRET environment variable
    - Have a valid Google account to authorize

    **How to run:**
    ```bash
    export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
    export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
    pytest -m manual tests/tier_b/test_oauth_flow.py
    ```

    **Expected behavior:**
    - Browser opens to Google consent screen
    - After authorization, browser shows "Authentication successful!"
    - Test validates that credentials are returned correctly

    **Note:** This test is automatically skipped in CI/non-interactive environments.
    """
    # Skip if not in interactive environment
    if not os.isatty(0):
        pytest.skip("OAuth flow test requires interactive terminal")

    # Get OAuth configuration from environment
    config = _get_oauth_config()
    if config is None:
        pytest.skip(
            "OAuth credentials not configured. "
            "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET"
        )

    client_id, client_secret, scopes = config

    # Create OAuthFlow instance
    oauth_flow = OAuthFlow(
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )

    # Print instructions for manual tester
    print("\n" + "=" * 70)
    print("MANUAL TEST: OAuth Flow Integration")
    print("=" * 70)
    print("\nThis test will:")
    print("1. Open your browser to Google's authorization page")
    print("2. Ask you to log in and authorize the application")
    print("3. Redirect back to localhost to complete the flow")
    print("\nPlease complete the authorization in the browser window.")
    print("You have 5 minutes to complete the flow.")
    print("=" * 70 + "\n")

    # Run the interactive OAuth flow
    credentials = oauth_flow.run_interactive_flow()

    # Validate returned credentials
    assert credentials is not None, "OAuth flow should return credentials"
    assert credentials.access_token, "Access token should not be empty"
    assert credentials.refresh_token, "Refresh token should not be empty"
    assert credentials.client_id == client_id, "Client ID should match"
    assert credentials.client_secret == client_secret, "Client secret should match"
    assert credentials.scopes == scopes, "Scopes should match"
    assert credentials.token_uri == oauth_flow.GOOGLE_TOKEN_URI, "Token URI should match"

    # Validate token expiry is in the future
    assert credentials.token_expiry is not None, "Token expiry should be set"
    assert credentials.token_expiry.tzinfo == UTC, "Token expiry should be UTC"
    assert credentials.token_expiry > datetime.now(UTC), "Token should not be expired"

    # Print success message
    print("\n" + "=" * 70)
    print("SUCCESS: OAuth flow completed successfully!")
    print("=" * 70)
    print(f"Access token: {credentials.access_token[:20]}...")
    print(f"Refresh token: {credentials.refresh_token[:20]}...")
    print(f"Token expiry: {credentials.token_expiry}")
    print("=" * 70 + "\n")
