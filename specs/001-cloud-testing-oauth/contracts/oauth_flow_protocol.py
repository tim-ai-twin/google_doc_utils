"""
OAuth Flow Protocol

Defines the interface for OAuth 2.0 authentication flows,
specifically the desktop application flow with local callback server.
"""

from typing import Protocol
from credential_manager_protocol import OAuthCredentials


class OAuthFlow(Protocol):
    """
    Protocol for OAuth 2.0 desktop application flow.

    Implementations handle the full OAuth dance:
    1. Generate authorization URL
    2. Launch browser for user consent
    3. Start local callback server
    4. Exchange authorization code for tokens
    5. Return credentials
    """

    @property
    def client_id(self) -> str:
        """OAuth client ID"""
        ...

    @property
    def client_secret(self) -> str:
        """OAuth client secret"""
        ...

    @property
    def scopes(self) -> list[str]:
        """Requested OAuth scopes"""
        ...

    @property
    def redirect_uri(self) -> str:
        """Redirect URI for callback (e.g., http://localhost:8080)"""
        ...

    def run_interactive_flow(self) -> OAuthCredentials:
        """
        Execute interactive OAuth flow with browser and local callback server.

        This method:
        1. Generates authorization URL with PKCE (if supported)
        2. Opens user's default browser to authorization URL
        3. Starts temporary HTTP server on localhost
        4. Waits for authorization code callback
        5. Exchanges code for access + refresh tokens
        6. Returns credentials

        Returns:
            OAuth credentials with access and refresh tokens

        Raises:
            OAuthError: If user denies consent
            TimeoutError: If user doesn't complete flow within timeout (5 minutes)
            IOError: If callback server can't bind to port
            ValueError: If authorization code is invalid
        """
        ...

    def exchange_code_for_tokens(self, authorization_code: str) -> OAuthCredentials:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: Code received from OAuth callback

        Returns:
            OAuth credentials with tokens

        Raises:
            ValueError: If code is invalid or expired
            IOError: If token exchange request fails
        """
        ...


class OAuthCallbackServer(Protocol):
    """
    Protocol for temporary HTTP server to receive OAuth callback.
    """

    @property
    def port(self) -> int:
        """Port on which server is listening"""
        ...

    @property
    def authorization_code(self) -> str | None:
        """Authorization code received from callback, or None if not yet received"""
        ...

    def start(self) -> None:
        """
        Start the callback server in background thread.

        Raises:
            IOError: If port is already in use
        """
        ...

    def wait_for_code(self, timeout: int = 300) -> str:
        """
        Block until authorization code is received or timeout.

        Args:
            timeout: Maximum seconds to wait (default 300 = 5 minutes)

        Returns:
            Authorization code from callback

        Raises:
            TimeoutError: If code not received within timeout
        """
        ...

    def shutdown(self) -> None:
        """
        Stop the callback server and clean up resources.
        """
        ...


class OAuthClientConfig(Protocol):
    """
    Protocol for OAuth client configuration.

    This configuration is typically loaded from a client_secrets.json file
    or environment variables.
    """

    client_id: str
    client_secret: str
    auth_uri: str  # e.g., https://accounts.google.com/o/oauth2/auth
    token_uri: str  # e.g., https://oauth2.googleapis.com/token
    redirect_uris: list[str]  # e.g., ["http://localhost:8080"]

    @staticmethod
    def load_from_file(file_path: str) -> "OAuthClientConfig":
        """
        Load OAuth client configuration from JSON file.

        Args:
            file_path: Path to client_secrets.json

        Returns:
            OAuth client configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is malformed or missing required fields
        """
        ...

    @staticmethod
    def load_from_env() -> "OAuthClientConfig":
        """
        Load OAuth client configuration from environment variables.

        Expected variables:
        - GOOGLE_OAUTH_CLIENT_ID
        - GOOGLE_OAUTH_CLIENT_SECRET

        Returns:
            OAuth client configuration with defaults for URIs

        Raises:
            ValueError: If required environment variables are missing
        """
        ...
