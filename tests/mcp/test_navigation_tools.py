"""Tests for MCP navigation tools.

Tests for:
- get_hierarchy tool
- list_documents tool (Phase 4)
- get_metadata tool (Phase 4)
"""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from extended_google_doc_utils.converter.types import (
    HeadingAnchor,
    HierarchyResult,
)


class TestGetHierarchy:
    """Contract tests for get_hierarchy tool."""

    @pytest.mark.tier_b
    def test_get_hierarchy_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that get_hierarchy returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id="test_doc_123", tab_id="")

        assert result["success"] is True
        assert "headings" in result
        assert "markdown" in result

    @pytest.mark.tier_b
    def test_get_hierarchy_returns_headings_list(self, initialized_mcp_server, mock_converter):
        """Test that get_hierarchy returns a list of headings with required fields."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id="test_doc_123", tab_id="")

        assert isinstance(result["headings"], list)
        if result["headings"]:
            heading = result["headings"][0]
            assert "anchor_id" in heading
            assert "level" in heading
            assert "text" in heading

    @pytest.mark.tier_b
    def test_get_hierarchy_returns_markdown_representation(self, initialized_mcp_server, mock_converter):
        """Test that get_hierarchy returns markdown hierarchy."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id="test_doc_123", tab_id="")

        assert isinstance(result["markdown"], str)

    @pytest.mark.tier_b
    def test_get_hierarchy_handles_google_api_error(self, initialized_mcp_server, mock_converter):
        """Test that get_hierarchy returns structured error for API errors."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        # Configure mock to raise a generic exception (simulating API error)
        mock_converter.get_hierarchy.side_effect = Exception("API error: document not found")

        result = get_hierarchy(document_id="invalid_doc", tab_id="")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.tier_b
    def test_get_hierarchy_handles_multiple_tabs_error(self, initialized_mcp_server, mock_converter):
        """Test that get_hierarchy returns structured error when tab_id required."""
        from extended_google_doc_utils.converter.exceptions import MultipleTabsError
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        # Configure mock to raise exception (MultipleTabsError takes only tab_count)
        mock_converter.get_hierarchy.side_effect = MultipleTabsError(3)

        result = get_hierarchy(document_id="doc123", tab_id="")

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "MultipleTabsError"
        assert "suggestion" in result["error"]

    @pytest.mark.tier_b
    def test_get_hierarchy_with_specific_tab(self, initialized_mcp_server, mock_converter):
        """Test that get_hierarchy works with specific tab_id."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id="test_doc_123", tab_id="t.specific")

        assert result["success"] is True
        # Verify the mock was called (converter should receive the tab_id)
        mock_converter.get_hierarchy.assert_called()
