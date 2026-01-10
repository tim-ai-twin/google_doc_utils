"""Test fixtures for MCP server tests.

This module provides fixtures for testing MCP tools using the SDK's
in-memory transport, enabling fast and reliable automated testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from extended_google_doc_utils.converter.converter import GoogleDocsConverter


@pytest.fixture
def mock_credentials():
    """Create mock OAuth credentials for testing."""
    from datetime import UTC, datetime, timedelta

    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials

    return OAuthCredentials(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
        client_id="mock_client_id",
        client_secret="mock_client_secret",
        scopes=["https://www.googleapis.com/auth/documents"],
        token_uri="https://oauth2.googleapis.com/token",
    )


@pytest.fixture
def mock_converter(mock_credentials) -> MagicMock:
    """Create a mock GoogleDocsConverter for testing."""
    converter = MagicMock(spec=["get_hierarchy", "export_tab", "export_section", "import_section", "import_tab", "list_documents", "get_metadata"])

    # Default mock responses
    from extended_google_doc_utils.converter.types import (
        ExportResult,
        HeadingAnchor,
        HierarchyResult,
        ImportResult,
    )

    converter.get_hierarchy.return_value = HierarchyResult(
        headings=[
            HeadingAnchor(anchor_id="h.abc123", level=1, text="Introduction", start_index=0),
            HeadingAnchor(anchor_id="h.def456", level=2, text="Background", start_index=100),
        ],
        markdown="# {^ h.abc123}Introduction\n## {^ h.def456}Background\n",
    )

    converter.export_tab.return_value = ExportResult(
        content="# Introduction\n\nSome content here.\n\n## Background\n\nMore content.",
        anchors=[],
        embedded_objects=[],
        warnings=[],
    )

    converter.export_section.return_value = ExportResult(
        content="## {^ h.def456}Background\n\nMore content.",
        anchors=[],
        embedded_objects=[],
        warnings=[],
    )

    converter.import_section.return_value = ImportResult(
        success=True,
        requests=[],
        preserved_objects=[],
        warnings=[],
    )

    converter.import_tab.return_value = ImportResult(
        success=True,
        requests=[],
        preserved_objects=[],
        warnings=[],
    )

    # Discovery method mocks
    converter.list_documents.return_value = [
        {
            "document_id": "doc123",
            "title": "Test Document",
            "last_modified": "2026-01-10T12:00:00.000Z",
            "owner": "test@example.com",
        },
        {
            "document_id": "doc456",
            "title": "Another Document",
            "last_modified": "2026-01-09T12:00:00.000Z",
            "owner": "other@example.com",
        },
    ]

    converter.get_metadata.return_value = {
        "document_id": "doc123",
        "title": "Test Document",
        "tabs": [
            {"tab_id": "t.0", "title": "Overview", "index": 0},
            {"tab_id": "t.1", "title": "Details", "index": 1},
        ],
        "can_edit": True,
        "can_comment": True,
    }

    return converter


@pytest.fixture
def mcp_server_with_mock_converter(mock_credentials, mock_converter):
    """Create an MCP server with mocked converter for testing.

    This fixture:
    1. Patches credential loading to return mock credentials
    2. Patches converter creation to return mock converter
    3. Initializes the server
    4. Registers all tools

    Yields:
        The configured MCP server instance.
    """
    from extended_google_doc_utils.mcp import server

    # Patch credential loading and converter creation
    with patch.object(
        server, "_credentials", mock_credentials
    ), patch.object(
        server, "_converter", mock_converter
    ):
        # Import tools to register them
        server.register_tools()

        yield server.mcp


@pytest.fixture
def initialized_mcp_server(mock_credentials, mock_converter):
    """Initialize MCP server with mocked dependencies.

    This fixture properly initializes the server module's global state
    with mocked credentials and converter.
    """
    from extended_google_doc_utils.mcp import server

    # Store originals
    original_converter = server._converter
    original_credentials = server._credentials

    # Set mocked values
    server._converter = mock_converter
    server._credentials = mock_credentials

    # Register tools
    server.register_tools()

    yield server

    # Restore originals
    server._converter = original_converter
    server._credentials = original_credentials


@pytest.fixture
def mock_drive_client():
    """Create a mock Drive client for testing list_documents."""
    client = MagicMock()

    # Mock list files response
    client.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "doc123",
                "name": "Test Document",
                "modifiedTime": "2026-01-10T12:00:00.000Z",
                "owners": [{"emailAddress": "test@example.com"}],
            },
            {
                "id": "doc456",
                "name": "Another Doc",
                "modifiedTime": "2026-01-09T12:00:00.000Z",
                "owners": [{"emailAddress": "other@example.com"}],
            },
        ]
    }

    return client


@pytest.fixture
def mock_docs_client():
    """Create a mock Docs client for testing get_metadata."""
    client = MagicMock()

    # Mock get document response
    client.documents.return_value.get.return_value.execute.return_value = {
        "documentId": "doc123",
        "title": "Test Document",
        "tabs": [
            {"tabProperties": {"tabId": "t.0", "title": "Tab 1", "index": 0}},
            {"tabProperties": {"tabId": "t.1", "title": "Tab 2", "index": 1}},
        ],
    }

    return client
