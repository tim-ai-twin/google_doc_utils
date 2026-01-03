"""Credential management for Google API authentication."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

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
        now = datetime.now(timezone.utc)
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

    def load_credentials(self) -> Optional[OAuthCredentials]:
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

    def _load_from_local_file(self) -> Optional[OAuthCredentials]:
        """Load credentials from .credentials/token.json.

        Returns:
            OAuthCredentials if file exists and is valid, None otherwise
        """
        credentials_path = Path(".credentials/token.json")

        if not credentials_path.exists():
            return None

        try:
            with open(credentials_path, "r") as f:
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
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            # Return None if file is malformed or missing required fields
            return None

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
        raise NotImplementedError("Subclasses must implement save_credentials()")

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
        raise NotImplementedError("Subclasses must implement refresh_access_token()")

    def get_credentials_for_testing(self) -> Optional[OAuthCredentials]:
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
