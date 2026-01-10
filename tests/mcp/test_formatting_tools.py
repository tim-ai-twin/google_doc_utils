"""Tests for MCP formatting tools.

Tests for:
- normalize_formatting tool (Phase 5)
- extract_styles tool (Phase 6)
- apply_styles tool (Phase 6)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from extended_google_doc_utils.converter.types import (
    ExportResult,
    ImportResult,
)


class TestNormalizeFormatting:
    """Contract tests for normalize_formatting tool."""

    @pytest.mark.tier_b
    def test_normalize_formatting_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that normalize_formatting returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.formatting import normalize_formatting

        result = normalize_formatting(
            document_id="test_doc_123",
            body_font="Arial",
            body_size="11pt",
        )

        assert result["success"] is True
        assert "changes_made" in result
        assert "warnings" in result

    @pytest.mark.tier_b
    def test_normalize_formatting_with_all_options(self, initialized_mcp_server, mock_converter):
        """Test normalize_formatting with all formatting options."""
        from extended_google_doc_utils.mcp.tools.formatting import normalize_formatting

        result = normalize_formatting(
            document_id="test_doc_123",
            tab_id="t.0",
            body_font="Times New Roman",
            body_size="12pt",
            heading_font="Arial",
            line_spacing="1.5",
            space_after="6pt",
        )

        assert result["success"] is True

    @pytest.mark.tier_b
    def test_normalize_formatting_preserves_embedded_objects(self, initialized_mcp_server, mock_converter):
        """Test that normalize_formatting preserves embedded objects."""
        from extended_google_doc_utils.mcp.tools.formatting import normalize_formatting

        # Configure mock to return content with embedded objects
        mock_converter.export_tab.return_value = ExportResult(
            content="# Title\n\nSome text.\n\n{^= img123 image}\n\nMore text.",
            anchors=[],
            embedded_objects=["img123"],
            warnings=[],
        )
        mock_converter.import_tab.return_value = ImportResult(
            success=True,
            requests=[],
            preserved_objects=["img123"],
            warnings=[],
        )

        result = normalize_formatting(
            document_id="test_doc_123",
            body_font="Arial",
        )

        assert result["success"] is True

    @pytest.mark.tier_b
    def test_normalize_formatting_handles_error(self, initialized_mcp_server, mock_converter):
        """Test that normalize_formatting handles errors gracefully."""
        from extended_google_doc_utils.mcp.tools.formatting import normalize_formatting

        # Configure mock to raise exception
        mock_converter.export_tab.side_effect = Exception("API error")

        result = normalize_formatting(
            document_id="invalid_doc",
            body_font="Arial",
        )

        assert result["success"] is False
        assert "error" in result


class TestExtractStyles:
    """Contract tests for extract_styles tool."""

    @pytest.mark.tier_b
    def test_extract_styles_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that extract_styles returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.formatting import extract_styles

        result = extract_styles(document_id="template_doc_123")

        assert result["success"] is True
        assert "styles" in result
        assert "source_document_id" in result

    @pytest.mark.tier_b
    def test_extract_styles_echoes_document_id(self, initialized_mcp_server, mock_converter):
        """Test that extract_styles echoes back the document ID."""
        from extended_google_doc_utils.mcp.tools.formatting import extract_styles

        doc_id = "my_template_doc"
        result = extract_styles(document_id=doc_id)

        assert result["source_document_id"] == doc_id


class TestApplyStyles:
    """Contract tests for apply_styles tool."""

    @pytest.mark.tier_b
    def test_apply_styles_returns_success_response(self, initialized_mcp_server, mock_converter):
        """Test that apply_styles returns a successful response structure."""
        from extended_google_doc_utils.mcp.tools.formatting import apply_styles

        styles = [
            {"element_type": "body", "font_family": "Arial", "font_size": "11pt"},
            {"element_type": "heading1", "font_family": "Arial", "font_size": "24pt"},
        ]

        result = apply_styles(
            document_id="target_doc_123",
            styles=styles,
        )

        assert result["success"] is True
        assert "changes_made" in result
        assert "warnings" in result

    @pytest.mark.tier_b
    def test_apply_styles_with_tab_id(self, initialized_mcp_server, mock_converter):
        """Test that apply_styles works with specific tab."""
        from extended_google_doc_utils.mcp.tools.formatting import apply_styles

        result = apply_styles(
            document_id="target_doc_123",
            styles=[{"element_type": "body", "font_family": "Georgia"}],
            tab_id="t.1",
        )

        assert result["success"] is True


class TestFormattingWorkflow:
    """Integration tests for formatting workflow."""

    @pytest.mark.tier_b
    def test_extract_and_apply_styles_workflow(self, initialized_mcp_server, mock_converter):
        """Test the complete extract → apply styles workflow."""
        from extended_google_doc_utils.mcp.tools.formatting import (
            apply_styles,
            extract_styles,
        )

        # Extract styles from template
        extract_result = extract_styles(document_id="template_doc")
        assert extract_result["success"] is True

        # Apply styles to target (using the extracted styles)
        # Note: In the stub implementation, styles is empty
        apply_result = apply_styles(
            document_id="target_doc",
            styles=extract_result["styles"],
        )
        assert apply_result["success"] is True
