"""OAuth 2.0 authorization code flow for desktop applications."""

import threading
import webbrowser
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from .credential_manager import OAuthCredentials


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    auth_code: str | None = None
    error: str | None = None

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        if "code" in params:
            _OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication successful!</h1>"
                b"<p>You can close this window now.</p></body></html>"
            )
        elif "error" in params:
            _OAuthCallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication failed!</h1>"
                b"<p>Error: " + _OAuthCallbackHandler.error.encode() + b"</p></body></html>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Invalid request</h1></body></html>"
            )

    def log_message(self, format, *args):
        """Suppress server log messages."""
        pass


class OAuthFlow:
    """Handles OAuth 2.0 authorization code flow for desktop applications.

    This class manages the interactive OAuth flow including:
    - Running a local callback server to receive authorization codes
    - Opening browser for user authorization
    - Exchanging authorization codes for access/refresh tokens
    """

    GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
    REDIRECT_URI_TEMPLATE = "http://localhost:{port}"
    PORT_RANGE = range(8080, 8090)  # 8080-8089

    def __init__(self, client_id: str, client_secret: str, scopes: list[str]):
        """Initialize the OAuth flow.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            scopes: List of OAuth scopes to request
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes

    def _find_available_port(self) -> tuple[HTTPServer, int]:
        """Find an available port and create server.

        Tries ports 8080-8089 in sequence.

        Returns:
            Tuple of (HTTPServer instance, port number)

        Raises:
            RuntimeError: If all ports in range are in use
        """
        for port in self.PORT_RANGE:
            try:
                server = HTTPServer(("localhost", port), _OAuthCallbackHandler)
                return server, port
            except OSError:
                continue

        raise RuntimeError(
            f"All ports in range {self.PORT_RANGE.start}-{self.PORT_RANGE.stop-1} are in use.\n"
            "Please close other applications using these ports and try again."
        )

    def run_interactive_flow(self) -> OAuthCredentials:
        """Run the interactive OAuth flow for desktop applications.

        This method:
        1. Starts a local HTTP server to receive the callback
        2. Opens the browser for user authorization
        3. Waits for the authorization code callback
        4. Exchanges the code for tokens

        Returns:
            OAuthCredentials with access token, refresh token, and metadata

        Raises:
            RuntimeError: If the authorization flow fails
            TimeoutError: If user doesn't complete authorization in time
        """
        # Reset class variables
        _OAuthCallbackHandler.auth_code = None
        _OAuthCallbackHandler.error = None

        # 1. Start local callback server with port fallback
        server, port = self._find_available_port()
        redirect_uri = self.REDIRECT_URI_TEMPLATE.format(port=port)
        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        # 2. Generate authorization URL
        auth_params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._scopes),
            "access_type": "offline",
            "prompt": "consent",
        }
        auth_url = f"{self.GOOGLE_AUTH_URI}?{urlencode(auth_params)}"

        # 3. Open browser to authorization URL
        print(f"Starting OAuth server on port {port}...")
        print("Opening browser for authentication...")
        print(f"If browser doesn't open, visit: {auth_url}")
        webbrowser.open(auth_url)

        # 4. Wait for callback with authorization code
        server_thread.join(timeout=300)  # 5 minute timeout

        if _OAuthCallbackHandler.error:
            raise RuntimeError(f"OAuth authorization failed: {_OAuthCallbackHandler.error}")

        if not _OAuthCallbackHandler.auth_code:
            raise TimeoutError(
                "OAuth authorization timed out - no response received within 5 minutes.\n"
                "Please restart the authorization flow and complete it in your browser."
            )

        # 5. Exchange code for tokens
        credentials = self.exchange_code_for_tokens(
            _OAuthCallbackHandler.auth_code, redirect_uri
        )

        # 6. Return OAuthCredentials
        return credentials

    def exchange_code_for_tokens(
        self, auth_code: str, redirect_uri: str = None
    ) -> OAuthCredentials:
        """Exchange authorization code for access and refresh tokens.

        Args:
            auth_code: Authorization code received from OAuth callback
            redirect_uri: OAuth redirect URI used in authorization request.
                         If None, defaults to http://localhost:8080

        Returns:
            OAuthCredentials with access token, refresh token, and metadata

        Raises:
            RuntimeError: If token exchange fails
            ValueError: If auth_code is invalid or empty
        """
        if not auth_code or not auth_code.strip():
            raise ValueError(
                "Authorization code cannot be empty. "
                "Ensure the OAuth callback received a valid code from Google."
            )

        # If redirect_uri not provided, use default (first port in range)
        if redirect_uri is None:
            redirect_uri = self.REDIRECT_URI_TEMPLATE.format(port=self.PORT_RANGE.start)

        # Prepare token exchange request
        token_data = {
            "code": auth_code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        # Exchange authorization code for tokens
        response = requests.post(self.GOOGLE_TOKEN_URI, data=token_data)

        if not response.ok:
            error_details = response.text
            raise RuntimeError(
                f"Token exchange failed (HTTP {response.status_code}): {error_details}\n"
                "This may indicate invalid client credentials or an expired authorization code."
            )

        token_response = response.json()

        # Calculate token expiry from expires_in (seconds from now)
        expires_in = token_response.get("expires_in", 3600)
        token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

        # Return OAuthCredentials with all required fields
        return OAuthCredentials(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_expiry=token_expiry,
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=self._scopes,
            token_uri=self.GOOGLE_TOKEN_URI,
        )
