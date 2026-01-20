"""Unit tests for style reader module.

Feature: 130-document-style-transfer
Tests: T009-T013
"""

import pytest

from extended_google_doc_utils.converter.style_reader import (
    extract_document_properties,
    extract_effective_style_from_paragraph,
    extract_named_style_definitions,
    extract_rgb_color,
    find_paragraphs_by_style_type,
)
from extended_google_doc_utils.converter.types import (
    NamedStyleType,
    RGBColor,
)


# =============================================================================
# T009: Unit test for RGB color extraction
# =============================================================================


class TestExtractRgbColor:
    """Tests for extract_rgb_color helper function."""

    def test_none_input(self):
        """Returns None for None input."""
        assert extract_rgb_color(None) is None

    def test_empty_dict(self):
        """Returns None for empty dict."""
        assert extract_rgb_color({}) is None

    def test_simple_rgb_color(self):
        """Extracts RGB from simple rgbColor structure."""
        color_obj = {"rgbColor": {"red": 0.5, "green": 0.25, "blue": 0.75}}
        result = extract_rgb_color(color_obj)
        assert result == RGBColor(red=0.5, green=0.25, blue=0.75)

    def test_nested_color_structure(self):
        """Extracts RGB from nested color structure."""
        color_obj = {
            "color": {"color": {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}}
        }
        result = extract_rgb_color(color_obj)
        assert result == RGBColor(red=1.0, green=0.0, blue=0.0)

    def test_missing_rgb_values_default_to_zero(self):
        """Missing RGB values default to 0.0."""
        color_obj = {"rgbColor": {"red": 0.5}}
        result = extract_rgb_color(color_obj)
        assert result == RGBColor(red=0.5, green=0.0, blue=0.0)

    def test_no_rgb_color_key(self):
        """Returns None if no rgbColor key present."""
        color_obj = {"color": {"themeColor": "DARK1"}}
        assert extract_rgb_color(color_obj) is None


class TestRGBColorDataclass:
    """Tests for RGBColor dataclass methods."""

    def test_to_hex(self):
        """Converts to hex string correctly."""
        color = RGBColor(red=1.0, green=0.0, blue=0.5)
        # 0.5 * 255 = 127.5 → int() truncates to 127 = 0x7f
        assert color.to_hex() == "#ff007f"

    def test_to_hex_black(self):
        """Black converts to #000000."""
        color = RGBColor(red=0.0, green=0.0, blue=0.0)
        assert color.to_hex() == "#000000"

    def test_to_hex_white(self):
        """White converts to #ffffff."""
        color = RGBColor(red=1.0, green=1.0, blue=1.0)
        assert color.to_hex() == "#ffffff"

    def test_from_hex(self):
        """Parses hex string correctly."""
        color = RGBColor.from_hex("#ff8000")
        assert color.red == pytest.approx(1.0, abs=0.01)
        assert color.green == pytest.approx(0.5, abs=0.01)
        assert color.blue == pytest.approx(0.0, abs=0.01)

    def test_from_hex_without_hash(self):
        """Parses hex string without # prefix."""
        color = RGBColor.from_hex("00ff00")
        assert color.green == pytest.approx(1.0, abs=0.01)

    def test_validation_rejects_out_of_range(self):
        """Raises ValueError for out-of-range values."""
        with pytest.raises(ValueError, match="red must be between"):
            RGBColor(red=1.5, green=0.0, blue=0.0)


# =============================================================================
# T010: Unit test for document properties extraction
# =============================================================================


class TestExtractDocumentProperties:
    """Tests for extract_document_properties helper function."""

    def test_none_input(self):
        """Returns empty DocumentProperties for None input."""
        result = extract_document_properties(None)
        assert result.background_color is None
        assert result.margin_top_pt is None

    def test_empty_dict(self):
        """Returns empty DocumentProperties for empty dict."""
        result = extract_document_properties({})
        assert result.background_color is None

    def test_extracts_background_color(self):
        """Extracts background color from documentStyle."""
        doc_style = {
            "background": {
                "color": {"color": {"rgbColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}}
            }
        }
        result = extract_document_properties(doc_style)
        assert result.background_color is not None
        assert result.background_color.red == pytest.approx(0.95, abs=0.01)

    def test_extracts_margins(self):
        """Extracts all four margins."""
        doc_style = {
            "marginTop": {"magnitude": 72, "unit": "PT"},
            "marginBottom": {"magnitude": 72, "unit": "PT"},
            "marginLeft": {"magnitude": 90, "unit": "PT"},
            "marginRight": {"magnitude": 90, "unit": "PT"},
        }
        result = extract_document_properties(doc_style)
        assert result.margin_top_pt == 72.0
        assert result.margin_bottom_pt == 72.0
        assert result.margin_left_pt == 90.0
        assert result.margin_right_pt == 90.0

    def test_extracts_page_size(self):
        """Extracts page width and height."""
        doc_style = {
            "pageSize": {
                "width": {"magnitude": 612, "unit": "PT"},
                "height": {"magnitude": 792, "unit": "PT"},
            }
        }
        result = extract_document_properties(doc_style)
        assert result.page_width_pt == 612.0
        assert result.page_height_pt == 792.0

    def test_partial_properties(self):
        """Handles partial properties (some set, others missing)."""
        doc_style = {"marginTop": {"magnitude": 72, "unit": "PT"}}
        result = extract_document_properties(doc_style)
        assert result.margin_top_pt == 72.0
        assert result.margin_bottom_pt is None


# =============================================================================
# T011: Unit test for named style definition extraction
# =============================================================================


class TestExtractNamedStyleDefinitions:
    """Tests for extract_named_style_definitions helper function."""

    def test_none_input(self):
        """Returns empty dict for None input."""
        result = extract_named_style_definitions(None)
        assert result == {}

    def test_empty_dict(self):
        """Returns empty dict for empty input."""
        result = extract_named_style_definitions({})
        assert result == {}

    def test_extracts_heading_1_style(self):
        """Extracts HEADING_1 style definition."""
        named_styles = {
            "styles": [
                {
                    "namedStyleType": "HEADING_1",
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Arial", "weight": 700},
                        "fontSize": {"magnitude": 24, "unit": "PT"},
                        "bold": True,
                    },
                    "paragraphStyle": {
                        "alignment": "START",
                        "lineSpacing": 115,
                        "spaceAbove": {"magnitude": 20, "unit": "PT"},
                    },
                }
            ]
        }
        result = extract_named_style_definitions(named_styles)

        assert NamedStyleType.HEADING_1 in result
        text_style, para_style = result[NamedStyleType.HEADING_1]

        assert text_style.font_family == "Arial"
        assert text_style.font_weight == 700
        assert text_style.font_size_pt == 24.0
        assert text_style.bold is True

        assert para_style.alignment == "START"
        assert para_style.line_spacing == pytest.approx(1.15, abs=0.01)
        assert para_style.space_before_pt == 20.0

    def test_extracts_all_9_style_types(self):
        """Extracts all 9 named style types when present."""
        styles = [
            {"namedStyleType": style_type.value, "textStyle": {}, "paragraphStyle": {}}
            for style_type in NamedStyleType
        ]
        named_styles = {"styles": styles}
        result = extract_named_style_definitions(named_styles)

        for style_type in NamedStyleType:
            assert style_type in result

    def test_skips_unknown_style_types(self):
        """Skips style types that aren't in the enum."""
        named_styles = {
            "styles": [
                {"namedStyleType": "UNKNOWN_STYLE", "textStyle": {}, "paragraphStyle": {}}
            ]
        }
        result = extract_named_style_definitions(named_styles)
        assert len(result) == 0


# =============================================================================
# T012: Unit test for effective style extraction from paragraph with overrides
# =============================================================================


class TestExtractEffectiveStyleFromParagraph:
    """Tests for extract_effective_style_from_paragraph helper function."""

    def test_extracts_paragraph_style(self):
        """Extracts paragraph style properties."""
        paragraph = {
            "paragraphStyle": {
                "alignment": "CENTER",
                "lineSpacing": 150,
                "spaceAbove": {"magnitude": 12, "unit": "PT"},
                "spaceBelow": {"magnitude": 6, "unit": "PT"},
            },
            "elements": [],
        }
        text_style, para_style = extract_effective_style_from_paragraph(paragraph)

        assert para_style.alignment == "CENTER"
        assert para_style.line_spacing == pytest.approx(1.5, abs=0.01)
        assert para_style.space_before_pt == 12.0
        assert para_style.space_after_pt == 6.0

    def test_extracts_text_style_from_first_run(self):
        """Extracts text style from first text run."""
        paragraph = {
            "paragraphStyle": {},
            "elements": [
                {
                    "textRun": {
                        "content": "Hello",
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Roboto", "weight": 400},
                            "fontSize": {"magnitude": 14, "unit": "PT"},
                            "foregroundColor": {
                                "color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 1.0}}
                            },
                        },
                    }
                }
            ],
        }
        text_style, para_style = extract_effective_style_from_paragraph(paragraph)

        assert text_style.font_family == "Roboto"
        assert text_style.font_size_pt == 14.0
        assert text_style.text_color is not None
        assert text_style.text_color.blue == 1.0

    def test_handles_paragraph_with_overrides(self):
        """Captures inline overrides that differ from style definition."""
        # Simulates a paragraph with inline formatting applied
        paragraph = {
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "elements": [
                {
                    "textRun": {
                        "content": "Custom Heading",
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Georgia", "weight": 400},
                            "fontSize": {"magnitude": 18, "unit": "PT"},
                            "foregroundColor": {
                                "color": {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}
                            },
                            "italic": True,
                        },
                    }
                }
            ],
        }
        text_style, para_style = extract_effective_style_from_paragraph(paragraph)

        # Should capture the overrides
        assert text_style.font_family == "Georgia"
        assert text_style.font_size_pt == 18.0
        assert text_style.text_color is not None
        assert text_style.text_color.red == 1.0
        assert text_style.italic is True

    def test_handles_empty_elements(self):
        """Returns empty text style for paragraph with no elements."""
        paragraph = {"paragraphStyle": {"alignment": "START"}, "elements": []}
        text_style, para_style = extract_effective_style_from_paragraph(paragraph)

        assert text_style.font_family is None
        assert para_style.alignment == "START"


# =============================================================================
# T013: Unit test for fallback to style definition when no paragraphs exist
# =============================================================================


class TestFindParagraphsByStyleType:
    """Tests for find_paragraphs_by_style_type helper function."""

    def test_empty_body(self):
        """Returns empty lists for all types when body is empty."""
        body = {"content": []}
        result = find_paragraphs_by_style_type(body)

        for style_type in NamedStyleType:
            assert result[style_type] == []

    def test_finds_heading_paragraphs(self):
        """Finds paragraphs by their named style type."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "elements": [{"textRun": {"content": "Heading 1"}}],
                    }
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Body text"}}],
                    }
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "elements": [{"textRun": {"content": "Another Heading 1"}}],
                    }
                },
            ]
        }
        result = find_paragraphs_by_style_type(body)

        assert len(result[NamedStyleType.HEADING_1]) == 2
        assert len(result[NamedStyleType.NORMAL_TEXT]) == 1
        assert len(result[NamedStyleType.HEADING_2]) == 0

    def test_skips_non_paragraph_elements(self):
        """Skips elements that are not paragraphs."""
        body = {
            "content": [
                {"table": {}},
                {"sectionBreak": {}},
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [],
                    }
                },
            ]
        }
        result = find_paragraphs_by_style_type(body)

        assert len(result[NamedStyleType.NORMAL_TEXT]) == 1

    def test_handles_paragraphs_without_style_type(self):
        """Skips paragraphs without namedStyleType."""
        body = {
            "content": [
                {"paragraph": {"paragraphStyle": {}, "elements": []}},
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [],
                    }
                },
            ]
        }
        result = find_paragraphs_by_style_type(body)

        assert len(result[NamedStyleType.NORMAL_TEXT]) == 1
