#!/usr/bin/env python3
"""Bootstrap OAuth credentials for local development.

This script guides developers through the OAuth 2.0 authorization flow
to obtain and save credentials for local development and testing.
"""

import argparse
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from googleapiclient.discovery import build

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    CredentialSource,
)
from extended_google_doc_utils.auth.oauth_flow import OAuthFlow


def print_welcome():
    """Print welcome message and setup instructions."""
    print("\n" + "=" * 70)
    print("  Google OAuth 2.0 Credential Bootstrap")
    print("=" * 70)
    print("\nThis script will guide you through obtaining OAuth credentials")
    print("for local development and testing with Google Docs/Drive APIs.")
    print("\n" + "-" * 70)
    print("SETUP REQUIREMENTS:")
    print("-" * 70)
    print("\n1. Go to the Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print("\n2. Create or select a project")
    print("\n3. Enable the required APIs:")
    print("   - Google Docs API")
    print("   - Google Drive API")
    print("\n4. Create OAuth 2.0 credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Choose 'Desktop app' as the application type")
    print("   - Download the client ID and client secret")
    print("\n5. Configure OAuth consent screen if prompted")
    print("\n" + "-" * 70 + "\n")


def prompt_for_credentials():
    """Prompt user for OAuth credentials if not provided via command line."""
    print("Please enter your OAuth credentials:\n")

    client_id = input("Client ID: ").strip()
    if not client_id:
        print("Error: Client ID cannot be empty")
        sys.exit(1)

    client_secret = input("Client Secret: ").strip()
    if not client_secret:
        print("Error: Client Secret cannot be empty")
        sys.exit(1)

    return client_id, client_secret


def validate_credentials(credentials):
    """Validate credentials by making a test API call.

    Args:
        credentials: The OAuth credentials to validate

    Returns:
        str: User email if successful, None otherwise
    """
    try:
        # Build Drive service
        service = build("drive", "v3", credentials=credentials)

        # Make test API call to get user info
        about = service.about().get(fields="user").execute()

        # Extract user email
        user_email = about.get("user", {}).get("emailAddress", "Unknown")

        return user_email
    except Exception as e:
        print(f"\n⚠️  Warning: Failed to validate credentials: {e}")
        return None


def format_env_vars(client_id: str, client_secret: str, credentials) -> str:
    """Format credentials as environment variables for easy export.

    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        credentials: Google OAuth credentials object

    Returns:
        str: Formatted export statements
    """
    refresh_token = credentials.refresh_token if credentials.refresh_token else ""

    return f"""
export GOOGLE_OAUTH_CLIENT_ID="{client_id}"
export GOOGLE_OAUTH_CLIENT_SECRET="{client_secret}"
export GOOGLE_OAUTH_REFRESH_TOKEN="{refresh_token}"
""".strip()


def main():
    """Run the OAuth bootstrap process."""
    parser = argparse.ArgumentParser(
        description="Bootstrap OAuth credentials for local development"
    )
    parser.add_argument(
        "--client-id",
        help="Google OAuth client ID",
    )
    parser.add_argument(
        "--client-secret",
        help="Google OAuth client secret",
    )
    parser.add_argument(
        "--scopes",
        nargs="+",
        default=[
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
        help="OAuth scopes to request (space-separated)",
    )

    args = parser.parse_args()

    # Print welcome message and instructions
    print_welcome()

    # Get credentials from args or prompt
    if args.client_id and args.client_secret:
        client_id = args.client_id
        client_secret = args.client_secret
    else:
        client_id, client_secret = prompt_for_credentials()

    # Initialize OAuth flow
    oauth_flow = OAuthFlow(
        client_id=client_id,
        client_secret=client_secret,
        scopes=args.scopes,
    )

    # Notify user before launching browser
    print("\n" + "=" * 70)
    print("STARTING OAUTH FLOW")
    print("=" * 70)
    print("\nYour browser will now open to complete the authorization.")
    print("Please:")
    print("  1. Sign in with your Google account")
    print("  2. Review the requested permissions")
    print("  3. Click 'Allow' to grant access")
    print("\nWaiting for authorization...")
    print("-" * 70 + "\n")

    # Run interactive OAuth flow
    credentials = oauth_flow.run_interactive_flow()

    # Save credentials to local file
    credential_manager = CredentialManager(source=CredentialSource.LOCAL_FILE)
    credential_manager.save_credentials(credentials)

    # Validate credentials with test API call
    print("\n" + "=" * 70)
    print("VALIDATING CREDENTIALS")
    print("=" * 70)
    print("\nMaking test API call to verify credentials...")

    user_email = validate_credentials(credentials)

    if user_email:
        print("\n✓ Success! Credentials are valid and working.")
        print(f"✓ Authenticated as: {user_email}")
        print("\n" + "=" * 70)
        print("SETUP COMPLETE")
        print("=" * 70)
        print("\nYour OAuth credentials have been saved and validated.")
        print("You can now run tests and use the library with these credentials.")

        # Output credentials in environment variable format
        print("\n" + "=" * 70)
        print("ENVIRONMENT VARIABLES")
        print("=" * 70)
        print("\nCopy these to your CI/CD environment or .env file:\n")
        print(format_env_vars(client_id, client_secret, credentials))
        print()
    else:
        print("\n⚠️  Credentials were saved but validation failed.")
        print("You may need to check your API permissions or scopes.")


if __name__ == "__main__":
    main()
