"""Credential management for Google API authentication."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from ..utils.config import EnvironmentType


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
            raise NotImplementedError("ENVIRONMENT source not yet implemented")
        elif self._source == CredentialSource.NONE:
            return None
        else:
            return None

    def _load_from_local_file(self) -> OAuthCredentials | None:
        """Load credentials from .credentials/token.json.

        Returns:
            OAuthCredentials if file exists and is valid, None otherwise
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
        except (KeyError, ValueError, json.JSONDecodeError):
            # Return None if file is malformed or missing required fields
            return None

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
            RefreshError: If refresh token is invalid or revoked
            ValueError: If credentials missing required fields
            IOError: If network request fails
        """
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
            RefreshError: If refresh fails
            FileNotFoundError: If credentials not found in LOCAL environment
        """
        creds = self.load_credentials()
        if creds is None:
            return None

        if creds.is_expired():
            creds = self.refresh_access_token(creds)
            if self.source == CredentialSource.LOCAL_FILE:
                self.save_credentials(creds)

        return creds
