"""Unit tests for MCP style transfer tools.

Feature: 130-document-style-transfer
Tests: T036-T038, T044
"""

import pytest
from unittest.mock import MagicMock, patch

from extended_google_doc_utils.converter.types import (
    DocumentProperties,
    DocumentStyles,
    EffectiveStyle,
    NamedStyleType,
    ParagraphStyleProperties,
    RGBColor,
    StyleApplicationResult,
    StyleSource,
    StyleTransferResult,
    TextStyleProperties,
)


# =============================================================================
# T036: Unit test for get_document_styles MCP tool response format
# =============================================================================


class TestGetDocumentStylesResponseFormat:
    """Tests for get_document_styles MCP tool response format (T036)."""

    def test_response_has_required_fields(self):
        """Response contains all required fields."""
        from extended_google_doc_utils.mcp.tools.styles import _document_styles_to_dict

        # Create mock DocumentStyles
        doc_styles = DocumentStyles(
            document_id="test_doc_id",
            document_properties=DocumentProperties(
                background_color=RGBColor(red=0.95, green=0.95, blue=0.95),
                margin_top_pt=72.0,
                margin_bottom_pt=72.0,
                margin_left_pt=72.0,
                margin_right_pt=72.0,
                page_width_pt=612.0,
                page_height_pt=792.0,
            ),
            effective_styles={
                NamedStyleType.NORMAL_TEXT: EffectiveStyle(
                    style_type=NamedStyleType.NORMAL_TEXT,
                    text_style=TextStyleProperties(font_family="Arial", font_size_pt=11.0),
                    paragraph_style=ParagraphStyleProperties(alignment="START"),
                    source=StyleSource.PARAGRAPH_SAMPLE,
                ),
                NamedStyleType.HEADING_1: EffectiveStyle(
                    style_type=NamedStyleType.HEADING_1,
                    text_style=TextStyleProperties(
                        font_family="Arial", font_size_pt=24.0, bold=True
                    ),
                    paragraph_style=ParagraphStyleProperties(
                        alignment="START", space_before_pt=20.0
                    ),
                    source=StyleSource.STYLE_DEFINITION,
                ),
            },
        )

        result = _document_styles_to_dict(doc_styles)

        # Check required fields
        assert "success" in result
        assert result["success"] is True
        assert "document_id" in result
        assert result["document_id"] == "test_doc_id"
        assert "document_properties" in result
        assert "effective_styles" in result

    def test_document_properties_format(self):
        """Document properties have correct format."""
        from extended_google_doc_utils.mcp.tools.styles import _document_styles_to_dict

        doc_styles = DocumentStyles(
            document_id="test_id",
            document_properties=DocumentProperties(
                background_color=RGBColor(red=1.0, green=0.0, blue=0.0),
                margin_top_pt=72.0,
            ),
            effective_styles={},
        )

        result = _document_styles_to_dict(doc_styles)
        props = result["document_properties"]

        assert props["background_color"] == "#ff0000"
        assert props["margin_top_pt"] == 72.0

    def test_effective_styles_format(self):
        """Effective styles have correct nested format."""
        from extended_google_doc_utils.mcp.tools.styles import _document_styles_to_dict

        doc_styles = DocumentStyles(
            document_id="test_id",
            document_properties=DocumentProperties(),
            effective_styles={
                NamedStyleType.HEADING_1: EffectiveStyle(
                    style_type=NamedStyleType.HEADING_1,
                    text_style=TextStyleProperties(
                        font_family="Roboto",
                        font_size_pt=24.0,
                        text_color=RGBColor(red=0.0, green=0.0, blue=1.0),
                        bold=True,
                    ),
                    paragraph_style=ParagraphStyleProperties(
                        alignment="CENTER", line_spacing=1.5, space_before_pt=20.0
                    ),
                    source=StyleSource.PARAGRAPH_SAMPLE,
                ),
            },
        )

        result = _document_styles_to_dict(doc_styles)
        h1 = result["effective_styles"]["HEADING_1"]

        # Check text properties
        assert h1["text"]["font_family"] == "Roboto"
        assert h1["text"]["font_size_pt"] == 24.0
        assert h1["text"]["text_color"] == "#0000ff"
        assert h1["text"]["bold"] is True

        # Check paragraph properties
        assert h1["paragraph"]["alignment"] == "CENTER"
        assert h1["paragraph"]["line_spacing"] == 1.5
        assert h1["paragraph"]["space_before_pt"] == 20.0

        # Check source
        assert h1["source"] == "paragraph_sample"


# =============================================================================
# T037: Unit test for apply_document_styles MCP tool response format
# =============================================================================


class TestApplyDocumentStylesResponseFormat:
    """Tests for apply_document_styles MCP tool response format (T037)."""

    def test_response_has_required_fields(self):
        """Response contains all required fields."""
        from extended_google_doc_utils.mcp.tools.styles import _transfer_result_to_dict

        result = StyleTransferResult(
            success=True,
            document_properties_applied=True,
            styles_applied={
                NamedStyleType.HEADING_1: StyleApplicationResult(
                    style_type=NamedStyleType.HEADING_1, paragraphs_updated=3
                ),
                NamedStyleType.NORMAL_TEXT: StyleApplicationResult(
                    style_type=NamedStyleType.NORMAL_TEXT, paragraphs_updated=42
                ),
            },
            total_paragraphs_updated=45,
            errors=[],
        )

        response = _transfer_result_to_dict(result)

        assert "success" in response
        assert response["success"] is True
        assert "document_properties_applied" in response
        assert response["document_properties_applied"] is True
        assert "styles_applied" in response
        assert "total_paragraphs_updated" in response
        assert response["total_paragraphs_updated"] == 45
        assert "errors" in response

    def test_styles_applied_format(self):
        """Styles applied have correct format with style type keys."""
        from extended_google_doc_utils.mcp.tools.styles import _transfer_result_to_dict

        result = StyleTransferResult(
            success=True,
            document_properties_applied=False,
            styles_applied={
                NamedStyleType.HEADING_1: StyleApplicationResult(
                    style_type=NamedStyleType.HEADING_1, paragraphs_updated=5
                ),
            },
            total_paragraphs_updated=5,
            errors=[],
        )

        response = _transfer_result_to_dict(result)

        # Keys should be string values from enum
        assert "HEADING_1" in response["styles_applied"]
        h1_result = response["styles_applied"]["HEADING_1"]
        assert h1_result["paragraphs_updated"] == 5
        assert h1_result["success"] is True
        assert h1_result["error"] is None

    def test_error_response_format(self):
        """Error responses include error details."""
        from extended_google_doc_utils.mcp.tools.styles import _transfer_result_to_dict

        result = StyleTransferResult(
            success=False,
            document_properties_applied=False,
            styles_applied={},
            total_paragraphs_updated=0,
            errors=["Document properties: permission denied"],
        )

        response = _transfer_result_to_dict(result)

        assert response["success"] is False
        assert len(response["errors"]) == 1
        assert "permission denied" in response["errors"][0]


# =============================================================================
# T038: Unit test for MCP error response format
# =============================================================================


class TestMcpErrorResponseFormat:
    """Tests for MCP error response format (T038)."""

    def test_exception_creates_error_response(self):
        """Exceptions are converted to error response format."""
        from extended_google_doc_utils.mcp.errors import create_error_response
        from dataclasses import asdict

        # Simulate an exception
        error = Exception("Test error message")
        response = asdict(create_error_response(error))

        assert "success" in response
        assert response["success"] is False
        assert "error" in response
        assert "Test error message" in str(response)

    def test_document_access_error_response(self):
        """DocumentAccessError creates appropriate error response."""
        from extended_google_doc_utils.mcp.errors import create_error_response
        from extended_google_doc_utils.converter.exceptions import DocumentAccessError
        from dataclasses import asdict

        error = DocumentAccessError("doc123", "permission denied")
        response = asdict(create_error_response(error))

        assert response["success"] is False
        assert "permission denied" in str(response)


# =============================================================================
# T044: Integration test placeholder (requires real documents)
# =============================================================================


@pytest.mark.tier_b
class TestMcpStyleToolsIntegration:
    """Integration tests for MCP style tools (T044)."""

    @pytest.mark.skip(reason="Requires real Google Docs credentials")
    def test_get_document_styles_integration(self):
        """Integration test for get_document_styles."""
        pass

    @pytest.mark.skip(reason="Requires real Google Docs credentials")
    def test_apply_document_styles_integration(self):
        """Integration test for apply_document_styles."""
        pass
