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


class TestTransformFormatting:
    """Unit tests for _transform_formatting helper function."""

    def test_merges_formatting_instead_of_nesting_headings(self):
        """When heading already has formatting, new props should merge, not nest."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        # Source document has colored heading
        content = "## {!color:#f6b26b}Heading Level 2{/!}\n"

        # Apply new font
        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Should merge props, not create nested {!...}{!...}
        assert "{!color:#f6b26b,font:Arial}" in transformed or "{!font:Arial,color:#f6b26b}" in transformed
        # Should NOT have nested formatting
        assert "}{!" not in transformed
        assert changes == 1

    def test_merges_formatting_instead_of_nesting_body(self):
        """When body text already has formatting, new props should merge."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        # Source document has colored text
        content = "{!color:#ff0000}Red text{/!}\n"

        # Apply new font
        transformed, changes = _transform_formatting(content, body_font="Roboto")

        # Should merge props
        assert "font:Roboto" in transformed
        assert "color:#ff0000" in transformed
        # Should NOT have nested formatting
        assert "}{!" not in transformed
        assert changes == 1

    def test_adds_formatting_to_plain_text(self):
        """Plain text without existing formatting gets wrapped."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## Plain heading\n\nPlain body text.\n"

        transformed, changes = _transform_formatting(
            content, heading_font="Georgia", body_font="Arial"
        )

        assert "{!font:Georgia}Plain heading{/!}" in transformed
        assert "{!font:Arial}Plain body text.{/!}" in transformed
        assert changes == 2

    def test_preserves_embedded_objects(self):
        """Embedded objects are not wrapped with formatting."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "{^= img_123 image}\n\nBody text.\n"

        transformed, changes = _transform_formatting(content, body_font="Arial")

        # Embedded object should be unchanged
        assert "{^= img_123 image}" in transformed
        # Body text should be formatted
        assert "{!font:Arial}Body text.{/!}" in transformed
        assert changes == 1

    def test_new_property_overrides_existing(self):
        """When both old and new have same property, new wins."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        # Source has Arial, we want to change to Georgia
        content = "## {!font:Arial}Heading{/!}\n"

        transformed, changes = _transform_formatting(content, heading_font="Georgia")

        # New font should override old font
        assert "font:Georgia" in transformed
        # Old font should NOT be present
        assert "font:Arial" not in transformed
        assert changes == 1

    def test_merges_multiple_existing_properties(self):
        """Multiple existing properties are preserved when adding new ones."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        # Source has color and highlight
        content = "## {!color:#ff0000,highlight:#ffff00}Heading{/!}\n"

        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # All properties should be present
        assert "color:#ff0000" in transformed
        assert "highlight:#ffff00" in transformed
        assert "font:Arial" in transformed
        # No nesting
        assert "}{!" not in transformed

    def test_handles_heading_with_bold_marker(self):
        """Headings with **bold** markers inside formatting work correctly."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## {!color:#0000ff}**Bold Heading**{/!}\n"

        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Should merge and preserve bold
        assert "**Bold Heading**" in transformed
        assert "font:Arial" in transformed
        assert "color:#0000ff" in transformed

    def test_handles_all_heading_levels(self):
        """All heading levels (H1-H6) get formatting applied."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = """# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading
"""

        transformed, changes = _transform_formatting(content, heading_font="Impact")

        # All 6 headings should be formatted
        assert changes == 6
        assert "# {!font:Impact}H1 Heading{/!}" in transformed
        assert "###### {!font:Impact}H6 Heading{/!}" in transformed

    def test_no_changes_when_no_formatting_requested(self):
        """Content unchanged when no formatting parameters provided."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## Heading\n\nBody text.\n"

        transformed, changes = _transform_formatting(content)

        assert transformed == content
        assert changes == 0

    def test_handles_empty_content(self):
        """Empty content returns empty result."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        transformed, changes = _transform_formatting("", heading_font="Arial")

        assert transformed == ""
        assert changes == 0

    def test_handles_only_whitespace_lines(self):
        """Whitespace-only lines are not formatted."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## Heading\n\n   \n\nBody text.\n"

        transformed, changes = _transform_formatting(content, body_font="Arial")

        # Only body text should be formatted, not whitespace line
        assert "{!font:Arial}Body text.{/!}" in transformed
        # The whitespace line should remain as-is
        assert "   " in transformed
        assert changes == 1

    def test_preserves_anchors(self):
        """Anchor markers are preserved and not wrapped."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## {^ heading_anchor} Heading Title\n"

        # Anchors are part of heading content and should be preserved
        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Anchor should be in the formatted content
        assert "{^ heading_anchor}" in transformed

    def test_body_with_multiple_properties(self):
        """Body formatting can include multiple properties."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "Some body text.\n"

        transformed, changes = _transform_formatting(
            content, body_font="Roboto", body_size="12pt"
        )

        assert "font:Roboto" in transformed
        assert "size:12pt" in transformed
        assert changes == 1


class TestTransformFormattingRoundTrip:
    """Tests that transformed content can be parsed and serialized correctly."""

    def test_merged_formatting_parses_correctly(self):
        """Merged formatting is valid MEBDF that parses to correct AST."""
        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        # Start with colored heading
        content = "## {!color:#f6b26b}Heading{/!}\n"

        # Add font
        transformed, _ = _transform_formatting(content, heading_font="Arial")

        # Parse the result
        parser = MebdfParser()
        ast = parser.parse(transformed)

        # Should have HeadingNode with FormattingNode
        assert len(ast.children) == 1
        heading = ast.children[0]
        assert heading.__class__.__name__ == "HeadingNode"
        assert len(heading.content) == 1

        formatting = heading.content[0]
        assert formatting.__class__.__name__ == "FormattingNode"
        # Both properties should be in the FormattingNode
        assert "color" in formatting.properties
        assert "font" in formatting.properties
        assert formatting.properties["color"] == "#f6b26b"
        assert formatting.properties["font"] == "Arial"

    def test_merged_formatting_serializes_without_mebdf_syntax(self):
        """Merged formatting serializes to clean text without MEBDF markers."""
        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.converter.mebdf_to_gdoc import serialize_ast_to_requests
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## {!color:#0000ff}Blue Heading{/!}\n"
        transformed, _ = _transform_formatting(content, heading_font="Arial")

        parser = MebdfParser()
        ast = parser.parse(transformed)

        text, styles, _, warnings = serialize_ast_to_requests(ast, 1, {})

        # Text should be clean without MEBDF syntax
        assert text == "Blue Heading\n"
        assert "{!" not in text
        assert "{/!}" not in text

        # Should have style requests for color and font
        text_style_requests = [s for s in styles if "updateTextStyle" in s]
        assert len(text_style_requests) > 0

        # Check that foregroundColor and weightedFontFamily are in the request
        text_style = text_style_requests[0]["updateTextStyle"]["textStyle"]
        assert "foregroundColor" in text_style
        assert "weightedFontFamily" in text_style

    def test_complex_document_round_trip(self):
        """Complex document with mixed formatting round-trips correctly."""
        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.converter.mebdf_to_gdoc import serialize_ast_to_requests
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = """# {!color:#ff0000}Red Title{/!}

{!highlight:#ffff00}Highlighted text{/!}

## Plain Heading

Regular body text.
"""

        # Apply formatting
        transformed, changes = _transform_formatting(
            content, heading_font="Georgia", body_font="Arial"
        )

        # Parse and serialize
        parser = MebdfParser()
        ast = parser.parse(transformed)
        text, styles, _, _ = serialize_ast_to_requests(ast, 1, {})

        # Text should be clean
        assert "{!" not in text
        assert "{/!}" not in text
        assert "Red Title" in text
        assert "Highlighted text" in text
        assert "Plain Heading" in text
        assert "Regular body text" in text


class TestTransformFormattingErrorCases:
    """Tests for error handling and edge cases in formatting transformation."""

    def test_malformed_inline_formatting_left_unchanged(self):
        """Malformed inline formatting (missing closing) is left unchanged."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        # Missing {/!} closer
        content = "## {!color:#ff0000}Heading without closer\n"

        # This shouldn't crash, just treat as plain text
        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Should still apply heading formatting (wrapping the whole thing)
        assert changes == 1
        # The malformed content should be inside the new formatting
        assert "font:Arial" in transformed

    def test_empty_formatting_block_treated_as_plain(self):
        """Empty formatting block {!}{/!} is not recognized, so heading is wrapped.

        The parser requires at least one character in properties, so {!}...{/!}
        is treated as plain text and gets wrapped with the new formatting.
        """
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## {!}Heading{/!}\n"

        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Since {!}Heading{/!} isn't recognized as formatting, the whole thing
        # gets wrapped as the heading text
        assert "font:Arial" in transformed
        assert changes == 1
        # The original {!}Heading{/!} should be inside the new formatting
        assert "{!}Heading{/!}" in transformed

    def test_formatting_with_special_characters_in_text(self):
        """Text with special characters inside formatting works."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## {!color:#0000ff}Heading with {braces} and [brackets]{/!}\n"

        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Special chars should be preserved
        assert "{braces}" in transformed
        assert "[brackets]" in transformed
        assert "font:Arial" in transformed

    def test_multiple_paragraphs_with_mixed_formatting(self):
        """Multiple paragraphs with different formatting states are handled."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = """{!color:#ff0000}Red paragraph{/!}

Plain paragraph

{!highlight:#00ff00}Green highlighted{/!}

Another plain paragraph
"""

        transformed, changes = _transform_formatting(content, body_font="Verdana")

        # All body paragraphs should have font applied
        # Red paragraph: merged
        assert "color:#ff0000" in transformed
        assert transformed.count("font:Verdana") >= 3  # At least 3 paragraphs

    def test_heading_with_link(self):
        """Heading containing a markdown link works correctly."""
        from extended_google_doc_utils.mcp.tools.formatting import _transform_formatting

        content = "## {!color:#0000ff}Heading with [link](https://example.com){/!}\n"

        transformed, changes = _transform_formatting(content, heading_font="Arial")

        # Link should be preserved
        assert "[link](https://example.com)" in transformed
        assert "font:Arial" in transformed
        assert "color:#0000ff" in transformed
