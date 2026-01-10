"""Tests for MCP tab tools.

Tests for:
- export_tab tool
- import_tab tool
"""

from __future__ import annotations

import pytest

from extended_google_doc_utils.converter.types import (
    ExportResult,
    ImportResult,
)


class TestExportTab:
    """Contract tests for export_tab tool."""

    @pytest.mark.tier_b
    def test_export_tab_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that export_tab returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.tabs import export_tab

        result = export_tab(document_id="test_doc_123", tab_id="")

        assert result["success"] is True
        assert "content" in result
        assert "tab_id" in result
        assert "warnings" in result

    @pytest.mark.tier_b
    def test_export_tab_returns_mebdf_content(self, initialized_mcp_server, mock_converter):
        """Test that export_tab returns MEBDF markdown content."""
        from extended_google_doc_utils.mcp.tools.tabs import export_tab

        result = export_tab(document_id="test_doc_123", tab_id="")

        assert isinstance(result["content"], str)
        assert result["content"]  # Non-empty

    @pytest.mark.tier_b
    def test_export_tab_handles_multiple_tabs_error(self, initialized_mcp_server, mock_converter):
        """Test that export_tab returns structured error when tab_id required."""
        from extended_google_doc_utils.converter.exceptions import MultipleTabsError
        from extended_google_doc_utils.mcp.tools.tabs import export_tab

        # Configure mock to raise exception
        mock_converter.export_tab.side_effect = MultipleTabsError(3)

        result = export_tab(document_id="doc123", tab_id="")

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "MultipleTabsError"


class TestImportTab:
    """Contract tests for import_tab tool."""

    @pytest.mark.tier_b
    def test_import_tab_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that import_tab returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.tabs import import_tab

        result = import_tab(
            document_id="test_doc_123",
            content="# Full Document\n\nContent here.",
            tab_id=""
        )

        assert result["success"] is True
        assert "tab_id" in result
        assert "preserved_objects" in result
        assert "warnings" in result

    @pytest.mark.tier_b
    def test_import_tab_handles_mebdf_parse_error(self, initialized_mcp_server, mock_converter):
        """Test that import_tab returns structured error for invalid MEBDF."""
        from extended_google_doc_utils.converter.exceptions import MebdfParseError
        from extended_google_doc_utils.mcp.tools.tabs import import_tab

        # Configure mock to raise exception
        mock_converter.import_tab.side_effect = MebdfParseError("Invalid syntax")

        result = import_tab(
            document_id="test_doc_123",
            content="Invalid {!broken content",
            tab_id=""
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "MebdfParseError"

    @pytest.mark.tier_b
    def test_import_tab_preserves_embedded_objects(self, initialized_mcp_server, mock_converter):
        """Test that import_tab reports preserved embedded objects."""
        from extended_google_doc_utils.converter.types import ImportResult
        from extended_google_doc_utils.mcp.tools.tabs import import_tab

        # Configure mock to return preserved objects
        mock_converter.import_tab.return_value = ImportResult(
            success=True,
            requests=[],
            preserved_objects=["img123", "chart456"],
            warnings=[],
        )

        result = import_tab(
            document_id="test_doc_123",
            content="# Doc\n\n{^= img123 image}\n{^= chart456 chart}",
            tab_id=""
        )

        assert result["success"] is True
        assert "img123" in result["preserved_objects"]
        assert "chart456" in result["preserved_objects"]
