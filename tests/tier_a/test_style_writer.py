"""Unit tests for style writer module.

Feature: 130-document-style-transfer
Tests: T018-T019, T025-T028
"""

import pytest

from extended_google_doc_utils.converter.types import (
    DocumentProperties,
    NamedStyleType,
    ParagraphStyleProperties,
    RGBColor,
    TextStyleProperties,
)


# =============================================================================
# T018: Unit test for building UpdateDocumentStyle request
# =============================================================================


class TestBuildUpdateDocumentStyleRequest:
    """Tests for building UpdateDocumentStyle request (T018)."""

    def test_builds_request_with_background_color(self):
        """Builds request with background color."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_document_style_request,
        )

        props = DocumentProperties(
            background_color=RGBColor(red=0.95, green=0.95, blue=0.95)
        )
        request = build_update_document_style_request(props)

        assert request is not None
        assert "updateDocumentStyle" in request
        doc_style = request["updateDocumentStyle"]["documentStyle"]
        assert "background" in doc_style
        assert "fields" in request["updateDocumentStyle"]
        assert "background" in request["updateDocumentStyle"]["fields"]

    def test_builds_request_with_margins(self):
        """Builds request with all four margins."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_document_style_request,
        )

        props = DocumentProperties(
            margin_top_pt=72.0,
            margin_bottom_pt=72.0,
            margin_left_pt=90.0,
            margin_right_pt=90.0,
        )
        request = build_update_document_style_request(props)

        assert request is not None
        doc_style = request["updateDocumentStyle"]["documentStyle"]
        assert doc_style["marginTop"]["magnitude"] == 72.0
        assert doc_style["marginBottom"]["magnitude"] == 72.0
        assert doc_style["marginLeft"]["magnitude"] == 90.0
        assert doc_style["marginRight"]["magnitude"] == 90.0

        fields = request["updateDocumentStyle"]["fields"]
        assert "marginTop" in fields
        assert "marginBottom" in fields
        assert "marginLeft" in fields
        assert "marginRight" in fields

    def test_builds_request_with_page_size(self):
        """Builds request with page size."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_document_style_request,
        )

        props = DocumentProperties(page_width_pt=612.0, page_height_pt=792.0)
        request = build_update_document_style_request(props)

        assert request is not None
        doc_style = request["updateDocumentStyle"]["documentStyle"]
        assert "pageSize" in doc_style
        assert doc_style["pageSize"]["width"]["magnitude"] == 612.0
        assert doc_style["pageSize"]["height"]["magnitude"] == 792.0

    def test_returns_none_for_empty_properties(self):
        """Returns None when no properties are set."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_document_style_request,
        )

        props = DocumentProperties()
        request = build_update_document_style_request(props)
        assert request is None


# =============================================================================
# T019: Unit test for partial property application
# =============================================================================


class TestPartialPropertyApplication:
    """Tests for partial property application (T019)."""

    def test_only_set_properties_included(self):
        """Only explicitly set properties are included in request."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_document_style_request,
        )

        # Only set top margin
        props = DocumentProperties(margin_top_pt=100.0)
        request = build_update_document_style_request(props)

        assert request is not None
        doc_style = request["updateDocumentStyle"]["documentStyle"]
        fields = request["updateDocumentStyle"]["fields"]

        # Top margin should be included
        assert "marginTop" in doc_style
        assert "marginTop" in fields

        # Other margins should NOT be included
        assert "marginBottom" not in doc_style
        assert "marginLeft" not in doc_style
        assert "marginRight" not in doc_style

    def test_mixed_properties(self):
        """Handles mix of set and unset properties."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_document_style_request,
        )

        props = DocumentProperties(
            background_color=RGBColor(red=1.0, green=1.0, blue=0.9),
            margin_top_pt=72.0,
            # Other margins and page size not set
        )
        request = build_update_document_style_request(props)

        fields = request["updateDocumentStyle"]["fields"]
        assert "background" in fields
        assert "marginTop" in fields
        assert "pageSize" not in fields


# =============================================================================
# T025: Unit test for building updateParagraphStyle request
# =============================================================================


class TestBuildUpdateParagraphStyleRequest:
    """Tests for building updateParagraphStyle request (T025)."""

    def test_builds_request_with_alignment(self):
        """Builds request with alignment."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_paragraph_style_request,
        )

        para_style = ParagraphStyleProperties(alignment="CENTER")
        request = build_update_paragraph_style_request(
            start_index=1, end_index=10, para_style=para_style
        )

        assert request is not None
        assert "updateParagraphStyle" in request
        assert request["updateParagraphStyle"]["range"]["startIndex"] == 1
        assert request["updateParagraphStyle"]["range"]["endIndex"] == 10
        assert (
            request["updateParagraphStyle"]["paragraphStyle"]["alignment"] == "CENTER"
        )

    def test_builds_request_with_spacing(self):
        """Builds request with line spacing and paragraph spacing."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_paragraph_style_request,
        )

        para_style = ParagraphStyleProperties(
            line_spacing=1.5, space_before_pt=12.0, space_after_pt=6.0
        )
        request = build_update_paragraph_style_request(
            start_index=0, end_index=50, para_style=para_style
        )

        para = request["updateParagraphStyle"]["paragraphStyle"]
        # Line spacing is stored as percentage
        assert para["lineSpacing"] == 150
        assert para["spaceAbove"]["magnitude"] == 12.0
        assert para["spaceBelow"]["magnitude"] == 6.0

    def test_builds_request_with_indentation(self):
        """Builds request with indentation properties."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_paragraph_style_request,
        )

        para_style = ParagraphStyleProperties(
            indent_start_pt=36.0, indent_end_pt=0.0, first_line_indent_pt=18.0
        )
        request = build_update_paragraph_style_request(
            start_index=0, end_index=100, para_style=para_style
        )

        para = request["updateParagraphStyle"]["paragraphStyle"]
        assert para["indentStart"]["magnitude"] == 36.0
        assert para["indentFirstLine"]["magnitude"] == 18.0

    def test_returns_none_for_empty_style(self):
        """Returns None when no properties are set."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_paragraph_style_request,
        )

        para_style = ParagraphStyleProperties()
        request = build_update_paragraph_style_request(
            start_index=0, end_index=10, para_style=para_style
        )
        assert request is None


# =============================================================================
# T026: Unit test for building updateTextStyle request
# =============================================================================


class TestBuildUpdateTextStyleRequest:
    """Tests for building updateTextStyle request (T026)."""

    def test_builds_request_with_font_family(self):
        """Builds request with font family and weight."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_text_style_request,
        )

        text_style = TextStyleProperties(font_family="Roboto", font_weight=700)
        request = build_update_text_style_request(
            start_index=0, end_index=20, text_style=text_style
        )

        assert request is not None
        assert "updateTextStyle" in request
        ts = request["updateTextStyle"]["textStyle"]
        assert ts["weightedFontFamily"]["fontFamily"] == "Roboto"
        assert ts["weightedFontFamily"]["weight"] == 700

    def test_builds_request_with_font_size(self):
        """Builds request with font size."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_text_style_request,
        )

        text_style = TextStyleProperties(font_size_pt=14.0)
        request = build_update_text_style_request(
            start_index=0, end_index=20, text_style=text_style
        )

        ts = request["updateTextStyle"]["textStyle"]
        assert ts["fontSize"]["magnitude"] == 14.0
        assert ts["fontSize"]["unit"] == "PT"

    def test_builds_request_with_colors(self):
        """Builds request with text and highlight colors."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_text_style_request,
        )

        text_style = TextStyleProperties(
            text_color=RGBColor(red=0.0, green=0.0, blue=1.0),
            highlight_color=RGBColor(red=1.0, green=1.0, blue=0.0),
        )
        request = build_update_text_style_request(
            start_index=0, end_index=20, text_style=text_style
        )

        ts = request["updateTextStyle"]["textStyle"]
        assert "foregroundColor" in ts
        assert ts["foregroundColor"]["color"]["rgbColor"]["blue"] == 1.0
        assert "backgroundColor" in ts
        assert ts["backgroundColor"]["color"]["rgbColor"]["red"] == 1.0

    def test_builds_request_with_boolean_properties(self):
        """Builds request with bold, italic, underline."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_text_style_request,
        )

        text_style = TextStyleProperties(bold=True, italic=True, underline=False)
        request = build_update_text_style_request(
            start_index=0, end_index=20, text_style=text_style
        )

        ts = request["updateTextStyle"]["textStyle"]
        assert ts["bold"] is True
        assert ts["italic"] is True
        assert ts["underline"] is False

    def test_returns_none_for_empty_style(self):
        """Returns None when no properties are set."""
        from extended_google_doc_utils.converter.style_writer import (
            build_update_text_style_request,
        )

        text_style = TextStyleProperties()
        request = build_update_text_style_request(
            start_index=0, end_index=20, text_style=text_style
        )
        assert request is None


# =============================================================================
# T027: Unit test for generating batch requests for all paragraphs
# =============================================================================


class TestGenerateBatchRequestsForStyleType:
    """Tests for generating batch requests for all paragraphs of a type (T027)."""

    def test_generates_requests_for_multiple_paragraphs(self):
        """Generates requests for each paragraph of a style type."""
        from extended_google_doc_utils.converter.style_writer import (
            generate_style_application_requests,
        )
        from extended_google_doc_utils.converter.types import EffectiveStyle, StyleSource

        # Mock paragraph ranges
        paragraph_ranges = [
            {"startIndex": 1, "endIndex": 20},
            {"startIndex": 25, "endIndex": 50},
            {"startIndex": 55, "endIndex": 80},
        ]

        effective_style = EffectiveStyle(
            style_type=NamedStyleType.HEADING_1,
            text_style=TextStyleProperties(font_family="Arial", font_size_pt=24.0),
            paragraph_style=ParagraphStyleProperties(alignment="START"),
            source=StyleSource.PARAGRAPH_SAMPLE,
        )

        requests = generate_style_application_requests(paragraph_ranges, effective_style)

        # Should have requests for each paragraph (text + paragraph style)
        assert len(requests) > 0
        # Each paragraph gets paragraph style and text style requests
        # If both have content, that's 2 requests per paragraph = 6 total
        assert len(requests) == 6

    def test_handles_empty_paragraph_ranges(self):
        """Returns empty list for no paragraphs."""
        from extended_google_doc_utils.converter.style_writer import (
            generate_style_application_requests,
        )
        from extended_google_doc_utils.converter.types import EffectiveStyle, StyleSource

        effective_style = EffectiveStyle(
            style_type=NamedStyleType.NORMAL_TEXT,
            text_style=TextStyleProperties(font_family="Arial"),
            paragraph_style=ParagraphStyleProperties(alignment="START"),
            source=StyleSource.STYLE_DEFINITION,
        )

        requests = generate_style_application_requests([], effective_style)
        assert requests == []


# =============================================================================
# T028: Unit test for preserving character-level overrides
# =============================================================================


class TestPreserveCharacterLevelOverrides:
    """Tests for preserving character-level overrides (T028)."""

    def test_requests_use_paragraph_range_not_character_range(self):
        """Text style requests use full paragraph range to preserve inline overrides."""
        from extended_google_doc_utils.converter.style_writer import (
            generate_style_application_requests,
        )
        from extended_google_doc_utils.converter.types import EffectiveStyle, StyleSource

        # Single paragraph range
        paragraph_ranges = [{"startIndex": 10, "endIndex": 50}]

        effective_style = EffectiveStyle(
            style_type=NamedStyleType.NORMAL_TEXT,
            text_style=TextStyleProperties(font_family="Arial", font_size_pt=11.0),
            paragraph_style=ParagraphStyleProperties(line_spacing=1.15),
            source=StyleSource.PARAGRAPH_SAMPLE,
        )

        requests = generate_style_application_requests(paragraph_ranges, effective_style)

        # Find the updateTextStyle request
        text_requests = [r for r in requests if "updateTextStyle" in r]
        assert len(text_requests) == 1

        # The range should match the paragraph range
        text_range = text_requests[0]["updateTextStyle"]["range"]
        assert text_range["startIndex"] == 10
        assert text_range["endIndex"] == 50

        # Key: by applying to the whole paragraph range, we set the default
        # text style but preserve any explicit character-level formatting


# =============================================================================
# T049: Unit test for same document edge case
# =============================================================================


class TestSameDocumentEdgeCase:
    """Tests for handling same source/target document (T049)."""

    def test_apply_document_styles_raises_for_same_document(self):
        """apply_document_styles raises ValueError for same source and target."""
        import pytest
        from extended_google_doc_utils.converter.style_writer import (
            apply_document_styles,
        )
        from extended_google_doc_utils.converter.types import StyleTransferOptions

        options = StyleTransferOptions()

        with pytest.raises(ValueError) as exc_info:
            apply_document_styles(
                source_document_id="same_doc_123",
                target_document_id="same_doc_123",
                options=options,
                credentials=None,  # Will fail before API call
            )

        assert "same" in str(exc_info.value).lower()
