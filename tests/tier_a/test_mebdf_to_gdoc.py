"""Unit tests for MEBDF to Google Docs import.

Tests cover:
- Text insertion request building
- Formatting request building
- Embedded object validation
- Paragraph style building
"""

import pytest

from extended_google_doc_utils.converter.exceptions import (
    EmbeddedObjectNotFoundError,
    FontValidationError,
)
from extended_google_doc_utils.converter.mebdf_parser import (
    BoldNode,
    CodeSpanNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    LinkNode,
    ListItemNode,
    ListNode,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.mebdf_to_gdoc import (
    build_import_requests,
    hex_to_rgb_color,
    serialize_ast_to_requests,
    serialize_node,
)


class TestSerializeNode:
    """Tests for individual node serialization."""

    def test_text_node(self):
        """Serialize text node."""
        node = TextNode("Hello")
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == "Hello"
        assert styles == []
        assert preserved == []

    def test_paragraph_node(self):
        """Serialize paragraph node."""
        node = ParagraphNode(content=[TextNode("Content")])
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == "Content\n"

    def test_bold_node(self):
        """Serialize bold node with style request."""
        node = BoldNode(content=[TextNode("Bold")])
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == "Bold"
        assert len(styles) == 1
        assert styles[0]["updateTextStyle"]["textStyle"]["bold"] is True

    def test_italic_node(self):
        """Serialize italic node with style request."""
        node = ItalicNode(content=[TextNode("Italic")])
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == "Italic"
        assert len(styles) == 1
        assert styles[0]["updateTextStyle"]["textStyle"]["italic"] is True

    def test_heading_node(self):
        """Serialize heading node with paragraph style."""
        node = HeadingNode(level=2, anchor_id=None, content=[TextNode("Title")])
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == "Title\n"
        assert len(styles) == 1
        assert (
            styles[0]["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"]
            == "HEADING_2"
        )

    def test_formatting_node_underline(self):
        """Serialize formatting node with underline."""
        node = FormattingNode(
            properties={"underline": True}, content=[TextNode("Underlined")]
        )
        warnings = []
        result = serialize_node(node, 1, {}, warnings)

        assert result is not None
        text, styles, preserved = result
        assert text == "Underlined"
        assert len(styles) == 1
        assert styles[0]["updateTextStyle"]["textStyle"]["underline"] is True

    def test_embedded_object_valid(self):
        """Serialize embedded object with valid ID."""
        node = EmbeddedObjectNode(object_id="img_001", object_type="image")
        available = {
            "img_001": {"inlineObjectProperties": {"embeddedObject": {"imageProperties": {}}}}
        }
        result = serialize_node(node, 1, available, [])

        assert result is not None
        text, styles, preserved = result
        assert text == ""  # Embedded objects don't produce text
        assert "img_001" in preserved

    def test_embedded_object_missing(self):
        """Raise error for missing embedded object."""
        node = EmbeddedObjectNode(object_id="missing", object_type="image")

        with pytest.raises(EmbeddedObjectNotFoundError) as exc_info:
            serialize_node(node, 1, {}, [])

        assert exc_info.value.object_id == "missing"
        assert exc_info.value.object_type == "image"

    def test_embedded_equation_no_id(self):
        """Equation without ID doesn't raise error."""
        node = EmbeddedObjectNode(object_id=None, object_type="equation")
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == ""
        assert preserved == []

    def test_list_node(self):
        """Serialize list node."""
        node = ListNode(
            ordered=False,
            items=[
                ListItemNode(content=[TextNode("One")], indent_level=0),
                ListItemNode(content=[TextNode("Two")], indent_level=0),
            ],
        )
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert "- One" in text
        assert "- Two" in text

    def test_nested_formatting(self):
        """Serialize nested formatting nodes."""
        node = BoldNode(content=[ItalicNode(content=[TextNode("Both")])])
        result = serialize_node(node, 1, {}, [])

        assert result is not None
        text, styles, preserved = result
        assert text == "Both"
        # Should have both bold and italic styles
        assert len(styles) == 2


class TestSerializeAstToRequests:
    """Tests for full AST serialization."""

    def test_simple_document(self):
        """Serialize simple document."""
        ast = DocumentNode(
            children=[
                HeadingNode(level=1, anchor_id=None, content=[TextNode("Title")]),
                ParagraphNode(content=[TextNode("Content")]),
            ]
        )

        text, styles, preserved, warnings = serialize_ast_to_requests(ast, 1, {})

        assert "Title" in text
        assert "Content" in text
        assert len(styles) > 0  # At least heading style

    def test_document_with_formatting(self):
        """Serialize document with various formatting."""
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        TextNode("Normal "),
                        BoldNode(content=[TextNode("bold")]),
                        TextNode(" text"),
                    ]
                )
            ]
        )

        text, styles, preserved, warnings = serialize_ast_to_requests(ast, 1, {})

        assert "Normal bold text" in text
        # Should have bold style request
        assert any("bold" in str(s) for s in styles)

    def test_document_with_embedded_objects(self):
        """Serialize document with embedded objects."""
        ast = DocumentNode(
            children=[
                ParagraphNode(content=[TextNode("Before")]),
                EmbeddedObjectNode(object_id="img_001", object_type="image"),
                ParagraphNode(content=[TextNode("After")]),
            ]
        )
        available = {
            "img_001": {"inlineObjectProperties": {"embeddedObject": {"imageProperties": {}}}}
        }

        text, styles, preserved, warnings = serialize_ast_to_requests(ast, 1, available)

        assert "img_001" in preserved


class TestBuildImportRequests:
    """Tests for building complete import requests."""

    def test_replace_all_deletes_content(self):
        """Replace all mode includes delete request."""
        document = {}
        body = {
            "content": [
                {"startIndex": 1, "endIndex": 25},
                {"startIndex": 25, "endIndex": 50},
            ]
        }
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New content")])]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have delete request
        delete_requests = [r for r in requests if "deleteContentRange" in r]
        assert len(delete_requests) == 1

    def test_insert_text_request(self):
        """Import generates insert text request."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New content")])]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have insert request
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) == 1

    def test_style_requests_included(self):
        """Import generates style requests for formatting."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                HeadingNode(level=1, anchor_id=None, content=[TextNode("Title")])
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have paragraph style request for heading
        style_requests = [r for r in requests if "updateParagraphStyle" in r]
        assert len(style_requests) >= 1

    def test_embedded_object_validation(self):
        """Import validates embedded object existence."""
        document = {"inlineObjects": {}}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[EmbeddedObjectNode(object_id="missing", object_type="image")]
        )

        with pytest.raises(EmbeddedObjectNotFoundError):
            build_import_requests(document, body, "", ast, replace_all=True)

    def test_highlight_color_applied(self):
        """Import applies highlight/background color formatting."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"highlight": "yellow"},
                            content=[TextNode("Highlighted")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a text style request with backgroundColor
        style_requests = [r for r in requests if "updateTextStyle" in r]
        assert len(style_requests) >= 1
        # Find the highlight style request
        bg_requests = [r for r in style_requests
                       if "backgroundColor" in r["updateTextStyle"]["textStyle"]]
        assert len(bg_requests) == 1
        assert "backgroundColor" in bg_requests[0]["updateTextStyle"]["fields"]

    def test_text_color_applied(self):
        """Import applies text color formatting."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"color": "#FF0000"},
                            content=[TextNode("Red text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a text style request with foregroundColor
        style_requests = [r for r in requests if "updateTextStyle" in r]
        fg_requests = [r for r in style_requests
                       if "foregroundColor" in r["updateTextStyle"]["textStyle"]]
        assert len(fg_requests) == 1
        fg_color = fg_requests[0]["updateTextStyle"]["textStyle"]["foregroundColor"]
        assert fg_color["color"]["rgbColor"]["red"] == 1.0
        assert fg_color["color"]["rgbColor"]["green"] == 0.0
        assert fg_color["color"]["rgbColor"]["blue"] == 0.0

    def test_monospace_applied(self):
        """Import applies monospace font formatting."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"mono": True},
                            content=[TextNode("Monospace text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a text style request with weightedFontFamily
        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        assert len(font_requests) == 1
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Courier New"

    def test_link_applied(self):
        """Import applies hyperlink formatting."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        LinkNode(text="Click here", url="https://example.com")
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a text style request with link
        style_requests = [r for r in requests if "updateTextStyle" in r]
        link_requests = [r for r in style_requests
                         if "link" in r["updateTextStyle"]["textStyle"]]
        assert len(link_requests) == 1
        link = link_requests[0]["updateTextStyle"]["textStyle"]["link"]
        assert link["url"] == "https://example.com"

    def test_code_span_applied(self):
        """Import applies monospace font to inline code spans."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        CodeSpanNode(content="code")
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a text style request with weightedFontFamily
        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        assert len(font_requests) == 1
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Courier New"

    def test_named_color_applied(self):
        """Import applies named colors (red, blue, etc.)."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"color": "blue"},
                            content=[TextNode("Blue text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a text style request with foregroundColor
        style_requests = [r for r in requests if "updateTextStyle" in r]
        fg_requests = [r for r in style_requests
                       if "foregroundColor" in r["updateTextStyle"]["textStyle"]]
        assert len(fg_requests) == 1
        fg_color = fg_requests[0]["updateTextStyle"]["textStyle"]["foregroundColor"]
        assert fg_color["color"]["rgbColor"]["red"] == 0.0
        assert fg_color["color"]["rgbColor"]["green"] == 0.0
        assert fg_color["color"]["rgbColor"]["blue"] == 1.0

    def test_invalid_color_warning(self):
        """Import warns about invalid color values."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"color": "invalidcolor"},
                            content=[TextNode("Text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should have a warning about invalid color
        assert any("invalid" in w.lower() and "color" in w.lower() for w in warnings)


class TestHexToRgbColor:
    """Tests for color conversion utility."""

    def test_hex_color_red(self):
        """Convert #FF0000 to RGB."""
        result = hex_to_rgb_color("#FF0000")
        assert result is not None
        rgb = result["color"]["rgbColor"]
        assert rgb["red"] == 1.0
        assert rgb["green"] == 0.0
        assert rgb["blue"] == 0.0

    def test_hex_color_short_form(self):
        """Convert #F00 (short form) to RGB."""
        result = hex_to_rgb_color("#F00")
        assert result is not None
        rgb = result["color"]["rgbColor"]
        assert rgb["red"] == 1.0
        assert rgb["green"] == 0.0
        assert rgb["blue"] == 0.0

    def test_hex_color_lowercase(self):
        """Convert lowercase hex."""
        result = hex_to_rgb_color("#00ff00")
        assert result is not None
        rgb = result["color"]["rgbColor"]
        assert rgb["red"] == 0.0
        assert rgb["green"] == 1.0
        assert rgb["blue"] == 0.0

    def test_named_color_red(self):
        """Convert named color 'red'."""
        result = hex_to_rgb_color("red")
        assert result is not None
        rgb = result["color"]["rgbColor"]
        assert rgb["red"] == 1.0
        assert rgb["green"] == 0.0
        assert rgb["blue"] == 0.0

    def test_named_color_case_insensitive(self):
        """Named colors are case-insensitive."""
        result = hex_to_rgb_color("YELLOW")
        assert result is not None
        rgb = result["color"]["rgbColor"]
        assert rgb["red"] == 1.0
        assert rgb["green"] == 1.0
        assert rgb["blue"] == 0.0

    def test_invalid_hex(self):
        """Invalid hex returns None."""
        assert hex_to_rgb_color("#GGG") is None
        assert hex_to_rgb_color("#12345") is None  # Wrong length
        assert hex_to_rgb_color("notacolor") is None

    def test_no_hash_prefix(self):
        """Hex without # prefix returns None (unless named color)."""
        assert hex_to_rgb_color("FF0000") is None


class TestFontFormatting:
    """Tests for font, weight, and size formatting."""

    def test_custom_font_applied(self):
        """Import applies custom font family."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"font": "Georgia"},
                            content=[TextNode("Custom font")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        assert len(font_requests) == 1
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Georgia"

    def test_font_weight_named(self):
        """Import applies named font weight (bold, light, etc.)."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"font": "Arial", "weight": "bold"},
                            content=[TextNode("Bold text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        assert len(font_requests) == 1
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Arial"
        assert font["weight"] == 700

    def test_font_weight_numeric(self):
        """Import applies numeric font weight."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            # Use Roboto which supports weight 300 (Arial only has 400/700)
                            properties={"font": "Roboto", "weight": "300"},
                            content=[TextNode("Light text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Roboto"
        assert font["weight"] == 300

    def test_font_size_with_pt(self):
        """Import applies font size with pt suffix."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"size": "14pt"},
                            content=[TextNode("Larger text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        style_requests = [r for r in requests if "updateTextStyle" in r]
        size_requests = [r for r in style_requests
                         if "fontSize" in r["updateTextStyle"]["textStyle"]]
        assert len(size_requests) == 1
        size = size_requests[0]["updateTextStyle"]["textStyle"]["fontSize"]
        assert size["magnitude"] == 14.0
        assert size["unit"] == "PT"

    def test_font_size_without_pt(self):
        """Import applies font size without suffix."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"size": "18"},
                            content=[TextNode("Larger text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        style_requests = [r for r in requests if "updateTextStyle" in r]
        size_requests = [r for r in style_requests
                         if "fontSize" in r["updateTextStyle"]["textStyle"]]
        size = size_requests[0]["updateTextStyle"]["textStyle"]["fontSize"]
        assert size["magnitude"] == 18.0


class TestParagraphFormatting:
    """Tests for paragraph-level formatting (alignment, spacing, indentation)."""

    def test_alignment_center(self):
        """Import applies center alignment."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"align": "center"},
                            content=[TextNode("Centered")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        assert len(para_requests) == 1
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        assert style["alignment"] == "CENTER"

    def test_alignment_justify(self):
        """Import applies justified alignment."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"align": "justify"},
                            content=[TextNode("Justified text")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        assert style["alignment"] == "JUSTIFIED"

    def test_line_spacing_double(self):
        """Import applies double line spacing."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"line-spacing": "double"},
                            content=[TextNode("Double spaced")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        assert style["lineSpacing"] == 200.0  # 2.0 * 100

    def test_line_spacing_numeric(self):
        """Import applies numeric line spacing."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"line-spacing": "1.5"},
                            content=[TextNode("1.5 spaced")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        assert style["lineSpacing"] == 150.0

    def test_paragraph_spacing(self):
        """Import applies space before and after."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"space-before": "12pt", "space-after": "6pt"},
                            content=[TextNode("Spaced paragraph")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        assert style["spaceAbove"]["magnitude"] == 12.0
        assert style["spaceBelow"]["magnitude"] == 6.0

    def test_indentation(self):
        """Import applies left indentation."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"indent-left": "0.5in"},
                            content=[TextNode("Indented")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        # 0.5in = 36pt
        assert style["indentStart"]["magnitude"] == 36.0

    def test_first_line_indent(self):
        """Import applies first line indentation."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"first-line-indent": "18pt"},
                            content=[TextNode("First line indented")],
                        )
                    ]
                )
            ]
        )

        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        para_requests = [r for r in requests if "updateParagraphStyle" in r]
        style = para_requests[0]["updateParagraphStyle"]["paragraphStyle"]
        assert style["indentFirstLine"]["magnitude"] == 18.0


class TestFontValidationErrors:
    """Tests for font validation error handling in imports."""

    def test_invalid_font_error_in_import(self):
        """Import raises FontValidationError for invalid font family."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"font": "FakeFont"},
                            content=[TextNode("Bad font")],
                        )
                    ]
                )
            ]
        )

        with pytest.raises(FontValidationError) as exc_info:
            build_import_requests(document, body, "", ast, replace_all=True)

        assert exc_info.value.error_code == "INVALID_FONT_FAMILY"
        assert "FakeFont" in str(exc_info.value)
        assert len(exc_info.value.suggestions) > 0

    def test_invalid_weight_error_in_import(self):
        """Import raises FontValidationError for invalid weight."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            # Arial only supports 400 and 700
                            properties={"font": "Arial", "weight": "300"},
                            content=[TextNode("Bad weight")],
                        )
                    ]
                )
            ]
        )

        with pytest.raises(FontValidationError) as exc_info:
            build_import_requests(document, body, "", ast, replace_all=True)

        assert exc_info.value.error_code == "INVALID_FONT_WEIGHT"
        assert "Arial" in str(exc_info.value)

    def test_variant_name_error_in_import(self):
        """Import raises FontValidationError for variant name as family."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"font": "Roboto Light"},
                            content=[TextNode("Variant name")],
                        )
                    ]
                )
            ]
        )

        with pytest.raises(FontValidationError) as exc_info:
            build_import_requests(document, body, "", ast, replace_all=True)

        assert exc_info.value.error_code == "INVALID_FONT_VARIANT"
        assert "Roboto" in exc_info.value.suggestions

    def test_valid_font_no_error(self):
        """Import succeeds for valid font and weight."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"font": "Roboto", "weight": "300"},
                            content=[TextNode("Valid font")],
                        )
                    ]
                )
            ]
        )

        # Should not raise
        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Verify font was applied
        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        assert len(font_requests) > 0
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Roboto"
        assert font["weight"] == 300

    def test_case_insensitive_font_accepted(self):
        """Import accepts font names case-insensitively."""
        document = {}
        body = {"content": [{"startIndex": 1, "endIndex": 2}]}
        ast = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"font": "roboto"},  # lowercase
                            content=[TextNode("Lowercase font")],
                        )
                    ]
                )
            ]
        )

        # Should not raise
        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Verify font was normalized to canonical casing
        style_requests = [r for r in requests if "updateTextStyle" in r]
        font_requests = [r for r in style_requests
                         if "weightedFontFamily" in r["updateTextStyle"]["textStyle"]]
        font = font_requests[0]["updateTextStyle"]["textStyle"]["weightedFontFamily"]
        assert font["fontFamily"] == "Roboto"  # Canonical casing
