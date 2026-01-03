"""
Credential Manager Protocol

Defines the interface for loading, saving, and refreshing OAuth credentials
from various sources (local files, environment variables).
"""

from datetime import datetime
from enum import Enum
from typing import Protocol


class CredentialSource(Enum):
    """Source from which credentials were loaded"""
    LOCAL_FILE = "local_file"
    ENVIRONMENT = "environment"
    NONE = "none"


class EnvironmentType(Enum):
    """Type of execution environment"""
    LOCAL = "local"
    GITHUB_ACTIONS = "github_actions"
    CLOUD_AGENT = "cloud_agent"


class OAuthCredentials(Protocol):
    """Protocol for OAuth 2.0 credentials"""

    access_token: str
    refresh_token: str
    token_expiry: datetime
    client_id: str
    client_secret: str
    scopes: list[str]
    token_uri: str

    def is_expired(self) -> bool:
        """
        Check if access token is expired.

        Returns:
            True if token is expired, False otherwise
        """
        ...

    def is_valid(self) -> bool:
        """
        Check if credentials have all required fields.

        Returns:
            True if credentials are valid, False otherwise
        """
        ...


class CredentialManager(Protocol):
    """
    Protocol for managing OAuth credentials.

    Implementations handle loading credentials from different sources
    (local files, environment variables) and refreshing expired tokens.
    """

    @property
    def source(self) -> CredentialSource:
        """
        The source from which credentials were loaded.

        Returns:
            CredentialSource enum value
        """
        ...

    @property
    def environment_type(self) -> EnvironmentType:
        """
        The detected execution environment.

        Returns:
            EnvironmentType enum value
        """
        ...

    def load_credentials(self) -> OAuthCredentials | None:
        """
        Load credentials from appropriate source based on environment.

        Local environments load from `.credentials/token.json`.
        Automated environments load from environment variables.

        Returns:
            OAuthCredentials instance if found, None otherwise

        Raises:
            FileNotFoundError: If LOCAL_FILE source and file doesn't exist
            ValueError: If environment variables are malformed
        """
        ...

    def save_credentials(self, credentials: OAuthCredentials) -> None:
        """
        Save credentials to appropriate storage.

        Local environments save to `.credentials/token.json`.
        Automated environments skip saving (credentials from env vars).

        Args:
            credentials: OAuth credentials to save

        Raises:
            IOError: If file write fails
            PermissionError: If credentials directory not writable
        """
        ...

    def refresh_access_token(
        self, credentials: OAuthCredentials
    ) -> OAuthCredentials:
        """
        Refresh an expired access token using the refresh token.

        Args:
            credentials: OAuth credentials with valid refresh token

        Returns:
            Updated credentials with new access token and expiry

        Raises:
            RefreshError: If refresh token is invalid or revoked
            ValueError: If credentials missing required fields
            IOError: If network request fails
        """
        ...

    def get_credentials_for_testing(self) -> OAuthCredentials | None:
        """
        Load and refresh credentials if needed for testing.

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
        ...


class CredentialSourceDetector(Protocol):
    """
    Protocol for detecting credential source based on environment.
    """

    @staticmethod
    def detect_environment() -> EnvironmentType:
        """
        Auto-detect execution environment from system environment variables.

        Detection logic:
        - GITHUB_ACTIONS=true → EnvironmentType.GITHUB_ACTIONS
        - CLOUD_AGENT=true → EnvironmentType.CLOUD_AGENT
        - Otherwise → EnvironmentType.LOCAL

        Returns:
            Detected environment type
        """
        ...

    @staticmethod
    def get_credential_source(env_type: EnvironmentType) -> CredentialSource:
        """
        Determine credential source based on environment type.

        Args:
            env_type: Detected or specified environment type

        Returns:
            Expected credential source for that environment
        """
        ...
