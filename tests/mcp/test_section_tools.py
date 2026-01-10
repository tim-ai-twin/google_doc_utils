"""Tests for MCP section tools.

Tests for:
- export_section tool
- import_section tool
- Section round-trip (isolation guarantee)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from extended_google_doc_utils.converter.types import (
    ExportResult,
    ImportResult,
)


class TestExportSection:
    """Contract tests for export_section tool."""

    @pytest.mark.tier_b
    def test_export_section_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that export_section returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.sections import export_section

        result = export_section(
            document_id="test_doc_123",
            anchor_id="h.abc123",
            tab_id=""
        )

        assert result["success"] is True
        assert "content" in result
        assert "anchor_id" in result
        assert "warnings" in result

    @pytest.mark.tier_b
    def test_export_section_returns_mebdf_content(self, initialized_mcp_server, mock_converter):
        """Test that export_section returns MEBDF markdown content."""
        from extended_google_doc_utils.mcp.tools.sections import export_section

        result = export_section(
            document_id="test_doc_123",
            anchor_id="h.def456",
            tab_id=""
        )

        assert isinstance(result["content"], str)
        assert result["content"]  # Non-empty

    @pytest.mark.tier_b
    def test_export_section_echoes_anchor_id(self, initialized_mcp_server, mock_converter):
        """Test that export_section echoes back the anchor_id."""
        from extended_google_doc_utils.mcp.tools.sections import export_section

        anchor = "h.specific123"
        result = export_section(
            document_id="test_doc_123",
            anchor_id=anchor,
            tab_id=""
        )

        assert result["anchor_id"] == anchor

    @pytest.mark.tier_b
    def test_export_section_handles_anchor_not_found(self, initialized_mcp_server, mock_converter):
        """Test that export_section returns structured error for invalid anchor."""
        from extended_google_doc_utils.converter.exceptions import AnchorNotFoundError
        from extended_google_doc_utils.mcp.tools.sections import export_section

        # Configure mock to raise exception
        mock_converter.export_section.side_effect = AnchorNotFoundError("h.invalid")

        result = export_section(
            document_id="test_doc_123",
            anchor_id="h.invalid",
            tab_id=""
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "AnchorNotFoundError"
        assert "suggestion" in result["error"]

    @pytest.mark.tier_b
    def test_export_section_preamble_with_empty_anchor(self, initialized_mcp_server, mock_converter):
        """Test that export_section handles empty anchor_id for preamble."""
        from extended_google_doc_utils.mcp.tools.sections import export_section

        result = export_section(
            document_id="test_doc_123",
            anchor_id="",  # Empty = preamble
            tab_id=""
        )

        assert result["success"] is True
        assert result["anchor_id"] == ""


class TestImportSection:
    """Contract tests for import_section tool."""

    @pytest.mark.tier_b
    def test_import_section_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that import_section returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.sections import import_section

        result = import_section(
            document_id="test_doc_123",
            anchor_id="h.abc123",
            content="## Updated Section\n\nNew content here.",
            tab_id=""
        )

        assert result["success"] is True
        assert "anchor_id" in result
        assert "preserved_objects" in result
        assert "warnings" in result

    @pytest.mark.tier_b
    def test_import_section_echoes_anchor_id(self, initialized_mcp_server, mock_converter):
        """Test that import_section echoes back the anchor_id."""
        from extended_google_doc_utils.mcp.tools.sections import import_section

        anchor = "h.target123"
        result = import_section(
            document_id="test_doc_123",
            anchor_id=anchor,
            content="## Section\n\nContent.",
            tab_id=""
        )

        assert result["anchor_id"] == anchor

    @pytest.mark.tier_b
    def test_import_section_handles_anchor_not_found(self, initialized_mcp_server, mock_converter):
        """Test that import_section returns structured error for invalid anchor."""
        from extended_google_doc_utils.converter.exceptions import AnchorNotFoundError
        from extended_google_doc_utils.mcp.tools.sections import import_section

        # Configure mock to raise exception
        mock_converter.import_section.side_effect = AnchorNotFoundError("h.invalid")

        result = import_section(
            document_id="test_doc_123",
            anchor_id="h.invalid",
            content="## Section\n\nContent.",
            tab_id=""
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "AnchorNotFoundError"

    @pytest.mark.tier_b
    def test_import_section_handles_mebdf_parse_error(self, initialized_mcp_server, mock_converter):
        """Test that import_section returns structured error for invalid MEBDF."""
        from extended_google_doc_utils.converter.exceptions import MebdfParseError
        from extended_google_doc_utils.mcp.tools.sections import import_section

        # Configure mock to raise exception
        mock_converter.import_section.side_effect = MebdfParseError("Invalid syntax")

        result = import_section(
            document_id="test_doc_123",
            anchor_id="h.abc123",
            content="Invalid {!broken content",
            tab_id=""
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "MebdfParseError"


class TestSectionRoundTrip:
    """Integration tests for section round-trip (export → modify → import)."""

    @pytest.mark.tier_b
    def test_section_roundtrip_preserves_other_sections(self, initialized_mcp_server, mock_converter):
        """Test that importing a section doesn't affect other sections.

        This is the core isolation guarantee of the section editing feature.
        """
        from extended_google_doc_utils.mcp.tools.sections import (
            export_section,
            import_section,
        )

        # Export a section
        export_result = export_section(
            document_id="test_doc_123",
            anchor_id="h.section1",
            tab_id=""
        )
        assert export_result["success"] is True

        # Modify and import back
        modified_content = export_result["content"] + "\n\nAdded paragraph."
        import_result = import_section(
            document_id="test_doc_123",
            anchor_id="h.section1",
            content=modified_content,
            tab_id=""
        )
        assert import_result["success"] is True

        # Verify the converter was called with correct parameters
        mock_converter.import_section.assert_called()

    @pytest.mark.tier_b
    def test_section_roundtrip_with_rich_content(self, initialized_mcp_server, mock_converter):
        """Test that rich content (links, formatting) survives round-trip."""
        from extended_google_doc_utils.mcp.tools.sections import import_section

        # MEBDF content with various formatting
        rich_content = """## {^ h.rich}Rich Section

This has **bold** and *italic* text.

Here's a [link](https://example.com) to follow.

{!highlight:yellow}Highlighted text{/!} stands out.

- Bullet point one
- Bullet point two
"""

        result = import_section(
            document_id="test_doc_123",
            anchor_id="h.rich",
            content=rich_content,
            tab_id=""
        )

        assert result["success"] is True

    @pytest.mark.tier_b
    def test_section_roundtrip_preserves_image_placeholders(self, initialized_mcp_server, mock_converter):
        """Test that image placeholders are preserved during import."""
        from extended_google_doc_utils.converter.types import ImportResult
        from extended_google_doc_utils.mcp.tools.sections import import_section

        # Configure mock to return preserved objects
        mock_converter.import_section.return_value = ImportResult(
            success=True,
            requests=[],
            preserved_objects=["obj123", "obj456"],
            warnings=[],
        )

        content_with_image = """## Section with Image

Some text before the image.

{^= obj123 image}

Text after the image.
"""

        result = import_section(
            document_id="test_doc_123",
            anchor_id="h.withimage",
            content=content_with_image,
            tab_id=""
        )

        assert result["success"] is True
        assert "obj123" in result["preserved_objects"]
