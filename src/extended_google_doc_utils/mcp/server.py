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


def initialize_server() -> None:
    """Initialize the MCP server with credentials and converter.

    This function:
    1. Detects credential source (local file or environment)
    2. Loads and refreshes OAuth credentials
    3. Creates the GoogleDocsConverter instance

    Raises:
        CredentialError: If credentials cannot be loaded.
    """
    global _converter, _credentials

    logger.info("Initializing Google Docs MCP server...")

    # Detect credential source
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

    logger.info("All MCP tools registered")


def run_server() -> None:
    """Run the MCP server (blocking).

    This is the main entry point for running the server.
    It initializes credentials, registers tools, and starts the server.
    """
    # Initialize server
    initialize_server()

    # Register all tools
    register_tools()

    # Run the server
    logger.info("Starting Google Docs MCP server...")
    mcp.run()
