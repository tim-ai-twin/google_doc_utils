"""FastMCP server for Google Docs operations.

This module provides the MCP server that exposes Google Docs tools to LLMs.
The server handles credential loading, converter initialization, and tool
registration.

Usage:
    python -m extended_google_doc_utils.mcp.server

Or configure in Claude Desktop:
    {
      "mcpServers": {
        "google-docs": {
          "command": "python",
          "args": ["-m", "extended_google_doc_utils.mcp.server"]
        }
      }
    }
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    CredentialSource,
    CredentialSourceDetector,
)
from extended_google_doc_utils.converter.converter import GoogleDocsConverter
from extended_google_doc_utils.mcp.errors import CredentialError

if TYPE_CHECKING:
    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials

logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP("Google Docs MCP Server")

# Global state for converter (initialized at startup)
_converter: GoogleDocsConverter | None = None
_credentials: OAuthCredentials | None = None


def get_converter() -> GoogleDocsConverter:
    """Get the initialized GoogleDocsConverter instance.

    Returns:
        The converter instance for document operations.

    Raises:
        CredentialError: If credentials are not initialized.
    """
    if _converter is None:
        raise CredentialError("MCP server not initialized. Credentials not loaded.")
    return _converter


def initialize_server(credentials_path: str | None = None) -> None:
    """Initialize the MCP server with credentials and converter.

    This function:
    1. Loads OAuth credentials from file or environment
    2. Refreshes credentials if needed
    3. Creates the GoogleDocsConverter instance

    Args:
        credentials_path: Optional path to credentials JSON file.
            If not provided, uses .credentials/token.json or environment variables.

    Raises:
        CredentialError: If credentials cannot be loaded.
    """
    global _converter, _credentials

    logger.info("Initializing Google Docs MCP server...")

    if credentials_path:
        # Load from specified file
        _credentials = _load_credentials_from_file(credentials_path)
    else:
        # Auto-detect credential source
        env_type = CredentialSourceDetector.detect_environment()
        source = CredentialSourceDetector.get_credential_source(env_type)

        if source == CredentialSource.NONE:
            raise CredentialError(
                "No credential source available. "
                "Run 'python scripts/bootstrap_oauth.py' to set up credentials."
            )

        # Load credentials
        manager = CredentialManager(source)
        _credentials = manager.get_credentials_for_testing()

    if _credentials is None:
        raise CredentialError(
            "Failed to load credentials. "
            "Run 'python scripts/bootstrap_oauth.py' to set up credentials."
        )

    # Create converter
    _converter = GoogleDocsConverter(_credentials)

    logger.info("Google Docs MCP server initialized successfully")


def _load_credentials_from_file(credentials_path: str) -> OAuthCredentials:
    """Load credentials from a specific file path.

    Args:
        credentials_path: Path to the credentials JSON file.

    Returns:
        Loaded OAuth credentials.

    Raises:
        CredentialError: If file cannot be read or parsed.
    """
    import json
    from datetime import datetime
    from pathlib import Path

    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials

    path = Path(credentials_path)
    if not path.exists():
        raise CredentialError(f"Credentials file not found: {credentials_path}")

    try:
        with open(path) as f:
            data = json.load(f)

        # Parse expiry if present
        token_expiry = None
        if "token_expiry" in data:
            token_expiry = datetime.fromisoformat(data["token_expiry"])

        return OAuthCredentials(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_expiry=token_expiry,
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            scopes=data.get("scopes", []),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        )
    except (json.JSONDecodeError, KeyError) as e:
        raise CredentialError(f"Invalid credentials file: {e}")


def create_server() -> FastMCP:
    """Create and return the configured MCP server.

    This is the main entry point for creating the server instance.
    Call initialize_server() before running the server.

    Returns:
        The configured FastMCP server instance.
    """
    return mcp


# =============================================================================
# Tool Registration
# =============================================================================
# Tools are registered by importing their modules.
# Each tool module uses the @mcp.tool() decorator to register tools.
# Import order determines tool listing order.


def register_tools() -> None:
    """Register all MCP tools with the server.

    This function imports all tool modules, which triggers registration
    via the @mcp.tool() decorator.
    """
    # Navigation tools: list_documents, get_metadata, get_hierarchy
    from extended_google_doc_utils.mcp.tools import navigation  # noqa: F401

    # Section tools: export_section, import_section
    from extended_google_doc_utils.mcp.tools import sections  # noqa: F401

    # Tab tools: export_tab, import_tab
    from extended_google_doc_utils.mcp.tools import tabs  # noqa: F401

    # Formatting tools: normalize_formatting, extract_styles, apply_styles
    from extended_google_doc_utils.mcp.tools import formatting  # noqa: F401

    # Style transfer tools: get_document_styles, apply_document_styles
    from extended_google_doc_utils.mcp.tools import styles  # noqa: F401

    logger.info("All MCP tools registered")


def run_server(credentials_path: str | None = None) -> None:
    """Run the MCP server (blocking).

    This is the main entry point for running the server.
    It initializes credentials, registers tools, and starts the server.

    Args:
        credentials_path: Optional path to credentials JSON file.
    """
    # Initialize server
    initialize_server(credentials_path)

    # Register all tools
    register_tools()

    # Run the server
    logger.info("Starting Google Docs MCP server...")
    mcp.run()
