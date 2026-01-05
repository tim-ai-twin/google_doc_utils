"""Credential management for Google API authentication."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from ..utils.config import EnvironmentType


class CredentialError(Exception):
    """Base exception for credential-related errors."""

    pass


class TokenExpiredError(CredentialError):
    """Raised when the access token is expired and cannot be refreshed."""

    pass


class TokenRevokedError(CredentialError):
    """Raised when the refresh token has been revoked."""

    def __init__(self, message: str | None = None):
        """Initialize TokenRevokedError with helpful message.

        Args:
            message: Optional custom message
        """
        if message is None:
            message = (
                "Refresh token has been revoked. "
                "Please re-run bootstrap_oauth.py to obtain new credentials:\n"
                "  python scripts/bootstrap_oauth.py"
            )
        super().__init__(message)


class InvalidCredentialsError(CredentialError):
    """Raised when credentials are invalid or malformed."""

    def __init__(self, message: str | None = None, details: str | None = None):
        """Initialize InvalidCredentialsError with helpful troubleshooting.

        Args:
            message: Optional custom message
            details: Optional additional details about the error
        """
        if message is None:
            message = "Invalid credentials detected."

        full_message = message
        if details:
            full_message += f"\nDetails: {details}"

        full_message += (
            "\n\nTroubleshooting steps:\n"
            "1. Check that .credentials/token.json exists and is readable\n"
            "2. Verify the JSON structure contains all required fields\n"
            "3. If the file is corrupted, re-run: python scripts/bootstrap_oauth.py"
        )
        super().__init__(full_message)


class MissingEnvironmentVariableError(CredentialError):
    """Raised when required environment variables are missing or empty."""

    def __init__(self, missing_vars: list[str]):
        """Initialize MissingEnvironmentVariableError with helpful message.

        Args:
            missing_vars: List of missing environment variable names
        """
        if len(missing_vars) == 1:
            message = f"Missing required env var {missing_vars[0]}"
        else:
            var_list = ", ".join(missing_vars)
            message = f"Missing required env vars: {var_list}"

        message += (
            "\n\nFor CI/CD environments, ensure these secrets are configured:\n"
            "- GOOGLE_OAUTH_CLIENT_ID: OAuth 2.0 client ID\n"
            "- GOOGLE_OAUTH_CLIENT_SECRET: OAuth 2.0 client secret\n"
            "- GOOGLE_OAUTH_REFRESH_TOKEN: Long-lived refresh token\n"
            "\nSee the documentation for setting up GitHub Actions secrets."
        )
        super().__init__(message)
        self.missing_vars = missing_vars


class CredentialSource(Enum):
    """Source from which credentials are loaded."""

    LOCAL_FILE = "local_file"  # .credentials/token.json for developers
    ENVIRONMENT = "environment"  # Environment variables for CI/CD
    NONE = "none"  # No credentials, Tier A tests only


@dataclass
class OAuthCredentials:
    """Type-safe container for OAuth credentials."""

    access_token: str
    refresh_token: str
    token_expiry: datetime
    client_id: str
    client_secret: str
    scopes: list[str]
    token_uri: str

    def is_expired(self) -> bool:
        """Check if access token is expired.

        Returns:
            True if token is expired, False otherwise
        """
        if self.token_expiry is None:
            return True
        now = datetime.now(UTC)
        return now >= self.token_expiry

    def is_valid(self) -> bool:
        """Check if credentials have all required fields.

        Returns:
            True if credentials are valid, False otherwise
        """
        return all([
            self.access_token,
            self.refresh_token,
            self.client_id,
            self.client_secret,
            self.scopes,
            self.token_uri,
            self.token_expiry,
        ])


class CredentialSourceDetector:
    """Detects credential source based on environment."""

    @staticmethod
    def detect_environment() -> EnvironmentType:
        """Auto-detect execution environment from system environment variables.

        Detection logic:
        - GITHUB_ACTIONS=true → EnvironmentType.GITHUB_ACTIONS
        - CLOUD_AGENT=true → EnvironmentType.CLOUD_AGENT
        - Otherwise → EnvironmentType.LOCAL_DEVELOPMENT

        Returns:
            Detected environment type
        """
        return EnvironmentType.detect()

    @staticmethod
    def get_credential_source(env_type: EnvironmentType) -> CredentialSource:
        """Determine credential source based on environment type.

        Args:
            env_type: Detected or specified environment type

        Returns:
            Expected credential source for that environment
        """
        if env_type == EnvironmentType.LOCAL_DEVELOPMENT:
            return CredentialSource.LOCAL_FILE
        elif env_type in (EnvironmentType.GITHUB_ACTIONS, EnvironmentType.CLOUD_AGENT):
            return CredentialSource.ENVIRONMENT
        else:
            return CredentialSource.NONE


class CredentialManager:
    """Manages OAuth credentials loading, saving, and refreshing.

    Implementations handle loading credentials from different sources
    (local files, environment variables) and refreshing expired tokens.
    """

    def __init__(self, source: CredentialSource):
        """Initialize the credential manager.

        Args:
            source: Source from which to load credentials
        """
        self._source = source
        self._environment_type = CredentialSourceDetector.detect_environment()

    @property
    def source(self) -> CredentialSource:
        """The source from which credentials were loaded.

        Returns:
            CredentialSource enum value
        """
        return self._source

    @property
    def environment_type(self) -> EnvironmentType:
        """The detected execution environment.

        Returns:
            EnvironmentType enum value
        """
        return self._environment_type

    def load_credentials(self) -> OAuthCredentials | None:
        """Load credentials from appropriate source based on environment.

        Local environments load from `.credentials/token.json`.
        Automated environments load from environment variables.

        Returns:
            OAuthCredentials instance if found, None otherwise

        Raises:
            FileNotFoundError: If LOCAL_FILE source and file doesn't exist
            ValueError: If environment variables are malformed
        """
        if self._source == CredentialSource.LOCAL_FILE:
            return self._load_from_local_file()
        elif self._source == CredentialSource.ENVIRONMENT:
            return self._load_from_environment()
        elif self._source == CredentialSource.NONE:
            return None
        else:
            return None

    def _load_from_local_file(self) -> OAuthCredentials | None:
        """Load credentials from .credentials/token.json.

        Returns:
            OAuthCredentials if file exists and is valid, None otherwise

        Raises:
            InvalidCredentialsError: If file exists but is malformed
        """
        credentials_path = Path(".credentials/token.json")

        if not credentials_path.exists():
            return None

        try:
            with open(credentials_path) as f:
                data = json.load(f)

            # Parse token_expiry from ISO format string
            token_expiry = datetime.fromisoformat(data["token_expiry"])

            return OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                token_expiry=token_expiry,
                client_id=data["client_id"],
                client_secret=data["client_secret"],
                scopes=data["scopes"],
                token_uri=data["token_uri"],
            )
        except json.JSONDecodeError as e:
            raise InvalidCredentialsError(
                message="Failed to parse credentials file",
                details=f"JSON parsing error: {e}",
            ) from e
        except KeyError as e:
            raise InvalidCredentialsError(
                message="Credentials file is missing required fields",
                details=f"Missing field: {e}",
            ) from e
        except ValueError as e:
            raise InvalidCredentialsError(
                message="Credentials file contains invalid values",
                details=f"Value error: {e}",
            ) from e

    @staticmethod
    def validate_environment_variables() -> list[str]:
        """Validate that all required environment variables are present and non-empty.

        Checks for:
        - GOOGLE_OAUTH_CLIENT_ID (required)
        - GOOGLE_OAUTH_CLIENT_SECRET (required)
        - GOOGLE_OAUTH_REFRESH_TOKEN (required)

        Returns:
            List of missing environment variable names (empty if all present)
        """
        required_vars = [
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GOOGLE_OAUTH_REFRESH_TOKEN",
        ]

        missing = []
        for var_name in required_vars:
            value = os.getenv(var_name)
            if not value or not value.strip():
                missing.append(var_name)

        return missing

    def _load_from_environment(self) -> OAuthCredentials | None:
        """Load credentials from environment variables.

        Reads credentials from:
        - GOOGLE_OAUTH_CLIENT_ID (required)
        - GOOGLE_OAUTH_CLIENT_SECRET (required)
        - GOOGLE_OAUTH_REFRESH_TOKEN (required)
        - GOOGLE_OAUTH_SCOPES (optional, comma-separated)

        Returns:
            OAuthCredentials if all required variables present

        Raises:
            MissingEnvironmentVariableError: If any required env var is missing or empty
        """
        # Validate all required environment variables
        missing_vars = self.validate_environment_variables()
        if missing_vars:
            raise MissingEnvironmentVariableError(missing_vars)

        # Read required environment variables (validated above)
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        refresh_token = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN")

        # Read optional scopes (comma-separated)
        scopes_str = os.getenv("GOOGLE_OAUTH_SCOPES")
        if scopes_str:
            scopes = [s.strip() for s in scopes_str.split(",")]
        else:
            # Default scopes for Google Docs and Drive
            scopes = [
                "https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive.file",
            ]

        # Set token_expiry to past date to force immediate refresh
        # This ensures we get a fresh access token on first use
        token_expiry = datetime.fromtimestamp(0, tz=UTC)

        return OAuthCredentials(
            access_token="",  # Will be obtained via refresh
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            token_uri="https://oauth2.googleapis.com/token",
        )

    def _save_to_local_file(self, credentials: OAuthCredentials) -> None:
        """Save credentials to .credentials/token.json.

        Args:
            credentials: OAuth credentials to save

        Raises:
            IOError: If file write fails
            PermissionError: If credentials directory not writable
        """
        credentials_dir = Path(".credentials")
        credentials_path = credentials_dir / "token.json"

        # Create .credentials/ directory if it doesn't exist
        credentials_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Serialize credentials to JSON
        data = {
            "access_token": credentials.access_token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.token_expiry.isoformat(),
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "token_uri": credentials.token_uri,
        }

        # Write to file
        with open(credentials_path, "w") as f:
            json.dump(data, f, indent=2)

        # Set file permissions to 0600 (owner read/write only)
        os.chmod(credentials_path, 0o600)

    def save_credentials(self, credentials: OAuthCredentials) -> None:
        """Save credentials to appropriate storage.

        Local environments save to `.credentials/token.json`.
        Automated environments skip saving (credentials from env vars).

        Args:
            credentials: OAuth credentials to save

        Raises:
            IOError: If file write fails
            PermissionError: If credentials directory not writable
        """
        if self._source == CredentialSource.LOCAL_FILE:
            self._save_to_local_file(credentials)
        elif self._source == CredentialSource.ENVIRONMENT:
            # Skip saving - credentials are sourced from environment variables
            pass
        elif self._source == CredentialSource.NONE:
            # Skip saving - no credential source configured
            pass

    def refresh_access_token(
        self, credentials: OAuthCredentials
    ) -> OAuthCredentials:
        """Refresh an expired access token using the refresh token.

        Args:
            credentials: OAuth credentials with valid refresh token

        Returns:
            Updated credentials with new access token and expiry

        Raises:
            TokenRevokedError: If refresh token is invalid or revoked
            InvalidCredentialsError: If credentials missing required fields
            CredentialError: If network request fails or other errors occur
        """
        # Validate credentials have required fields
        if not credentials.is_valid():
            missing_fields = []
            if not credentials.access_token:
                missing_fields.append("access_token")
            if not credentials.refresh_token:
                missing_fields.append("refresh_token")
            if not credentials.client_id:
                missing_fields.append("client_id")
            if not credentials.client_secret:
                missing_fields.append("client_secret")
            if not credentials.scopes:
                missing_fields.append("scopes")
            if not credentials.token_uri:
                missing_fields.append("token_uri")

            raise InvalidCredentialsError(
                message="Credentials are missing required fields",
                details=f"Missing: {', '.join(missing_fields)}",
            )

        try:
            # Create a google.oauth2.credentials.Credentials object
            google_creds = Credentials(
                token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes,
            )

            # Refresh the credentials using google.auth
            request = Request()
            google_creds.refresh(request)

            # Update the token expiry to UTC timezone-aware datetime
            token_expiry = google_creds.expiry
            if token_expiry and token_expiry.tzinfo is None:
                token_expiry = token_expiry.replace(tzinfo=UTC)

            # Return updated OAuthCredentials
            return OAuthCredentials(
                access_token=google_creds.token,
                refresh_token=google_creds.refresh_token,
                token_expiry=token_expiry,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes,
                token_uri=credentials.token_uri,
            )

        except RefreshError as e:
            # Token has been revoked or is invalid
            raise TokenRevokedError() from e

        except OSError as e:
            # Network or connection error
            raise CredentialError(
                f"Network error while refreshing token: {e}\n"
                "Please check your internet connection and try again."
            ) from e

        except Exception as e:
            # Catch any other unexpected errors
            raise CredentialError(
                f"Unexpected error while refreshing token: {e}\n"
                "Please try re-running: python scripts/bootstrap_oauth.py"
            ) from e

    def get_credentials_for_testing(self) -> OAuthCredentials | None:
        """Load and refresh credentials if needed for testing.

        Convenience method that:
        1. Loads credentials from appropriate source
        2. Checks if access token is expired
        3. Refreshes token if needed
        4. Saves updated credentials (local only)

        Returns:
            Valid OAuth credentials ready for testing, or None if unavailable

        Raises:
            TokenRevokedError: If refresh token has been revoked - re-run bootstrap_oauth.py
            InvalidCredentialsError: If credentials are malformed or missing fields
            CredentialError: If network errors or other issues occur during refresh
        """
        creds = self.load_credentials()
        if creds is None:
            return None

        # Validate credentials before checking expiry
        if not creds.is_valid():
            raise InvalidCredentialsError(
                message="Loaded credentials are invalid",
                details="Credential file may be corrupted or incomplete",
            )

        # Refresh expired tokens
        if creds.is_expired():
            try:
                creds = self.refresh_access_token(creds)
                if self.source == CredentialSource.LOCAL_FILE:
                    self.save_credentials(creds)
            except TokenRevokedError:
                # Re-raise with no modification - error message is already clear
                raise
            except InvalidCredentialsError:
                # Re-raise with no modification - error message is already clear
                raise
            except CredentialError:
                # Re-raise with no modification - error message is already clear
                raise

        return creds
