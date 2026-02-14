"""Unit tests for mock MCP tool responses."""

import pytest

from extended_google_doc_utils.discoverability.mock import (
    ALL_TOOL_NAMES,
    UnknownToolError,
    get_mock_response,
)


class TestGetMockResponse:
    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_each_tool_returns_response(self, tool_name):
        """Every known tool returns a well-formed response."""
        response = get_mock_response(tool_name, {})
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True

    def test_unknown_tool_raises(self):
        with pytest.raises(UnknownToolError, match="Unknown MCP tool"):
            get_mock_response("nonexistent_tool", {})

    def test_all_12_tools_covered(self):
        """Verify we have mock responses for all 12 MCP tools."""
        expected_tools = {
            "list_documents",
            "get_metadata",
            "get_hierarchy",
            "export_section",
            "import_section",
            "export_tab",
            "import_tab",
            "normalize_formatting",
            "extract_styles",
            "apply_styles",
            "get_document_styles",
            "apply_document_styles",
        }
        assert set(ALL_TOOL_NAMES) == expected_tools

    def test_get_hierarchy_has_headings(self):
        response = get_mock_response("get_hierarchy", {"document_id": "doc123"})
        assert "headings" in response
        assert len(response["headings"]) > 0
        assert "anchor_id" in response["headings"][0]

    def test_list_documents_has_documents(self):
        response = get_mock_response("list_documents", {})
        assert "documents" in response
        assert len(response["documents"]) > 0
        assert "document_id" in response["documents"][0]
        assert "title" in response["documents"][0]

    def test_export_section_has_content(self):
        response = get_mock_response("export_section", {"anchor_id": "h.abc123"})
        assert "content" in response
        assert len(response["content"]) > 0
        assert response["anchor_id"] == "h.abc123"

    def test_parameter_customization(self):
        """Mock responses use provided parameters where relevant."""
        response = get_mock_response("get_metadata", {"document_id": "custom_id"})
        assert response["document_id"] == "custom_id"

    def test_response_is_copy(self):
        """Responses should be copies, not mutable references."""
        r1 = get_mock_response("list_documents", {})
        r2 = get_mock_response("list_documents", {})
        r1["extra_key"] = "modified"
        assert "extra_key" not in r2
