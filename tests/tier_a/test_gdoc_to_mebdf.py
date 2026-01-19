"""Unit tests for Google Docs to MEBDF export.

Tests cover:
- Text extraction with formatting
- Anchor extraction
- Embedded object detection
- Paragraph and list conversion
- Table conversion
"""


from extended_google_doc_utils.converter.gdoc_to_mebdf import (
    convert_elements,
    convert_paragraph_content,
    convert_text_with_style,
    detect_embedded_type,
    export_body,
    rgb_to_hex,
)
from extended_google_doc_utils.converter.mebdf_parser import (
    BoldNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    ListNode,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.types import AnchorType, EmbeddedObjectType


class TestConvertTextWithStyle:
    """Tests for text style conversion."""

    def test_plain_text(self):
        """Convert plain text without formatting."""
        warnings = []
        node = convert_text_with_style("Hello", {}, warnings)

        assert isinstance(node, TextNode)
        assert node.content == "Hello"
        assert len(warnings) == 0

    def test_bold_text(self):
        """Convert bold text."""
        warnings = []
        node = convert_text_with_style("Bold", {"bold": True}, warnings)

        assert isinstance(node, BoldNode)
        assert isinstance(node.content[0], TextNode)
        assert node.content[0].content == "Bold"

    def test_italic_text(self):
        """Convert italic text."""
        warnings = []
        node = convert_text_with_style("Italic", {"italic": True}, warnings)

        assert isinstance(node, ItalicNode)

    def test_bold_and_italic(self):
        """Convert bold+italic text."""
        warnings = []
        node = convert_text_with_style("Both", {"bold": True, "italic": True}, warnings)

        assert isinstance(node, BoldNode)
        assert isinstance(node.content[0], ItalicNode)

    def test_underline(self):
        """Convert underlined text to MEBDF formatting."""
        warnings = []
        node = convert_text_with_style("Underlined", {"underline": True}, warnings)

        assert isinstance(node, FormattingNode)
        assert node.properties.get("underline") is True

    def test_highlight_color(self):
        """Convert highlighted text."""
        warnings = []
        style = {
            "backgroundColor": {
                "color": {"rgbColor": {"red": 1.0, "green": 1.0, "blue": 0.0}}
            }
        }
        node = convert_text_with_style("Yellow", style, warnings)

        assert isinstance(node, FormattingNode)
        assert "highlight" in node.properties

    def test_text_color(self):
        """Convert colored text."""
        warnings = []
        style = {
            "foregroundColor": {
                "color": {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}
            }
        }
        node = convert_text_with_style("Red", style, warnings)

        assert isinstance(node, FormattingNode)
        assert node.properties.get("color") == "#ff0000"

    def test_monospace_font(self):
        """Convert monospace font to MEBDF mono."""
        warnings = []
        style = {"weightedFontFamily": {"fontFamily": "Roboto Mono"}}
        node = convert_text_with_style("Code", style, warnings)

        assert isinstance(node, FormattingNode)
        assert node.properties.get("mono") is True

    def test_custom_font_family(self):
        """Convert custom font family to MEBDF font property."""
        warnings = []
        style = {"weightedFontFamily": {"fontFamily": "Comic Sans MS"}}
        node = convert_text_with_style("Fun text", style, warnings)

        assert isinstance(node, FormattingNode)
        assert node.properties.get("font") == "Comic Sans MS"

    def test_font_with_weight(self):
        """Convert font with custom weight."""
        warnings = []
        style = {"weightedFontFamily": {"fontFamily": "Roboto", "weight": 300}}
        node = convert_text_with_style("Light text", style, warnings)

        assert isinstance(node, FormattingNode)
        assert node.properties.get("font") == "Roboto"
        assert node.properties.get("weight") == 300

    def test_arial_default_not_exported(self):
        """Arial with default weight is not exported (it's the default)."""
        warnings = []
        style = {"weightedFontFamily": {"fontFamily": "Arial", "weight": 400}}
        node = convert_text_with_style("Default text", style, warnings)

        assert isinstance(node, TextNode)
        assert node.content == "Default text"

    def test_arial_bold_weight_exported(self):
        """Arial with bold weight exports the weight."""
        warnings = []
        style = {"weightedFontFamily": {"fontFamily": "Arial", "weight": 700}}
        node = convert_text_with_style("Bold Arial", style, warnings)

        assert isinstance(node, FormattingNode)
        assert node.properties.get("weight") == 700
        # Font not exported because Arial is default
        assert "font" not in node.properties

    def test_strikethrough_warning(self):
        """Strikethrough generates a warning."""
        warnings = []
        convert_text_with_style("Struck", {"strikethrough": True}, warnings)

        assert len(warnings) == 1
        assert "Strikethrough not supported" in warnings[0]


class TestRgbToHex:
    """Tests for RGB to hex conversion."""

    def test_red(self):
        """Convert red."""
        assert rgb_to_hex({"red": 1.0, "green": 0.0, "blue": 0.0}) == "#ff0000"

    def test_green(self):
        """Convert green."""
        assert rgb_to_hex({"red": 0.0, "green": 1.0, "blue": 0.0}) == "#00ff00"

    def test_blue(self):
        """Convert blue."""
        assert rgb_to_hex({"red": 0.0, "green": 0.0, "blue": 1.0}) == "#0000ff"

    def test_white(self):
        """Convert white."""
        assert rgb_to_hex({"red": 1.0, "green": 1.0, "blue": 1.0}) == "#ffffff"

    def test_black(self):
        """Convert black."""
        assert rgb_to_hex({"red": 0.0, "green": 0.0, "blue": 0.0}) == "#000000"

    def test_empty(self):
        """Empty RGB returns None."""
        assert rgb_to_hex({}) is None


class TestDetectEmbeddedType:
    """Tests for embedded object type detection."""

    def test_image(self):
        """Detect image type."""
        obj_data = {
            "inlineObjectProperties": {
                "embeddedObject": {"imageProperties": {"contentUri": "..."}}
            }
        }
        assert detect_embedded_type(obj_data) == "image"

    def test_drawing(self):
        """Detect drawing type."""
        obj_data = {
            "inlineObjectProperties": {
                "embeddedObject": {"embeddedDrawingProperties": {}}
            }
        }
        assert detect_embedded_type(obj_data) == "drawing"

    def test_chart(self):
        """Detect chart type."""
        obj_data = {
            "inlineObjectProperties": {
                "embeddedObject": {
                    "linkedContentReference": {
                        "sheetsChartReference": {"spreadsheetId": "..."}
                    }
                }
            }
        }
        assert detect_embedded_type(obj_data) == "chart"

    def test_unknown(self):
        """Unknown type returns embed."""
        obj_data = {"inlineObjectProperties": {"embeddedObject": {}}}
        assert detect_embedded_type(obj_data) == "embed"


class TestConvertParagraphContent:
    """Tests for paragraph content conversion."""

    def test_simple_text_run(self):
        """Convert simple text run."""
        paragraph = {"elements": [{"textRun": {"content": "Hello world\n"}}]}

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, {}, {}
        )

        assert len(content) == 1
        assert isinstance(content[0], TextNode)
        assert content[0].content == "Hello world"

    def test_multiple_text_runs(self):
        """Convert multiple text runs."""
        paragraph = {
            "elements": [
                {"textRun": {"content": "Hello "}},
                {"textRun": {"content": "world\n"}},
            ]
        }

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, {}, {}
        )

        assert len(content) == 2

    def test_formatted_text_run(self):
        """Convert formatted text run."""
        paragraph = {
            "elements": [
                {"textRun": {"content": "Bold\n", "textStyle": {"bold": True}}}
            ]
        }

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, {}, {}
        )

        assert len(content) == 1
        assert isinstance(content[0], BoldNode)

    def test_inline_object(self):
        """Convert inline object reference."""
        paragraph = {
            "elements": [{"inlineObjectElement": {"inlineObjectId": "img_001"}}]
        }
        inline_objects = {
            "img_001": {
                "inlineObjectProperties": {
                    "embeddedObject": {"imageProperties": {"contentUri": "..."}}
                }
            }
        }

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, inline_objects, {}
        )

        assert len(content) == 1
        assert isinstance(content[0], EmbeddedObjectNode)
        assert content[0].object_id == "img_001"
        assert content[0].object_type == "image"

        assert len(embedded) == 1
        assert embedded[0].object_id == "img_001"
        assert embedded[0].object_type == EmbeddedObjectType.IMAGE

    def test_equation(self):
        """Convert equation element."""
        paragraph = {"elements": [{"equation": {}}]}

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, {}, {}
        )

        assert len(content) == 1
        assert isinstance(content[0], EmbeddedObjectNode)
        assert content[0].object_id is None
        assert content[0].object_type == "equation"

    def test_rich_link_youtube(self):
        """Convert YouTube rich link."""
        paragraph = {
            "elements": [
                {
                    "richLink": {
                        "richLinkId": "link_001",
                        "richLinkProperties": {
                            "uri": "https://www.youtube.com/watch?v=abc123"
                        },
                    }
                }
            ]
        }

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, {}, {}
        )

        assert len(content) == 1
        assert isinstance(content[0], EmbeddedObjectNode)
        assert content[0].object_type == "video"


class TestConvertElements:
    """Tests for full element conversion."""

    def test_heading(self):
        """Convert heading element."""
        elements = [
            {
                "paragraph": {
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "headingId": "h.abc123",
                    },
                    "elements": [{"textRun": {"content": "Title\n"}}],
                },
                "startIndex": 1,
            }
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], HeadingNode)
        assert doc.children[0].level == 1
        assert doc.children[0].anchor_id == "h.abc123"

        assert len(anchors) == 1
        assert anchors[0].anchor_id == "h.abc123"
        assert anchors[0].anchor_type == AnchorType.HEADING

    def test_regular_paragraph(self):
        """Convert regular paragraph."""
        elements = [
            {
                "paragraph": {
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "elements": [{"textRun": {"content": "Content\n"}}],
                },
                "startIndex": 1,
            }
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ParagraphNode)

    def test_list(self):
        """Convert list elements."""
        elements = [
            {
                "paragraph": {
                    "bullet": {"listId": "list1", "nestingLevel": 0},
                    "elements": [{"textRun": {"content": "Item 1\n"}}],
                },
                "startIndex": 1,
            },
            {
                "paragraph": {
                    "bullet": {"listId": "list1", "nestingLevel": 0},
                    "elements": [{"textRun": {"content": "Item 2\n"}}],
                },
                "startIndex": 10,
            },
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ListNode)
        assert len(doc.children[0].items) == 2


class TestHeadingFormatting:
    """Tests for heading text formatting extraction.

    Headings should preserve inline formatting (bold, italic, font, color, etc.)
    just like body paragraphs.
    """

    def test_heading_with_bold_text(self):
        """Export heading containing bold text."""
        elements = [
            {
                "paragraph": {
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "headingId": "h.test1",
                    },
                    "elements": [
                        {"textRun": {"content": "Bold "}},
                        {"textRun": {"content": "Heading", "textStyle": {"bold": True}}},
                        {"textRun": {"content": "\n"}},
                    ],
                },
                "startIndex": 1,
            }
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        assert len(doc.children) == 1
        heading = doc.children[0]
        assert isinstance(heading, HeadingNode)
        assert heading.level == 1
        # Should have mixed content: plain text + bold
        assert len(heading.content) >= 2
        # Find the bold node
        bold_nodes = [n for n in heading.content if isinstance(n, BoldNode)]
        assert len(bold_nodes) == 1

    def test_heading_with_custom_font(self):
        """Export heading with custom font formatting."""
        elements = [
            {
                "paragraph": {
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_2",
                        "headingId": "h.test2",
                    },
                    "elements": [
                        {
                            "textRun": {
                                "content": "Custom Font Heading\n",
                                "textStyle": {
                                    "weightedFontFamily": {
                                        "fontFamily": "Roboto",
                                        "weight": 300,
                                    }
                                },
                            }
                        }
                    ],
                },
                "startIndex": 1,
            }
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        heading = doc.children[0]
        assert isinstance(heading, HeadingNode)
        # Should have FormattingNode with font properties
        assert len(heading.content) == 1
        formatting_node = heading.content[0]
        assert isinstance(formatting_node, FormattingNode)
        assert formatting_node.properties.get("font") == "Roboto"
        assert formatting_node.properties.get("weight") == 300

    def test_heading_with_text_color(self):
        """Export heading with colored text."""
        elements = [
            {
                "paragraph": {
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "headingId": "h.color",
                    },
                    "elements": [
                        {
                            "textRun": {
                                "content": "Red Heading\n",
                                "textStyle": {
                                    "foregroundColor": {
                                        "color": {
                                            "rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}
                                        }
                                    }
                                },
                            }
                        }
                    ],
                },
                "startIndex": 1,
            }
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        heading = doc.children[0]
        assert isinstance(heading, HeadingNode)
        formatting_node = heading.content[0]
        assert isinstance(formatting_node, FormattingNode)
        assert formatting_node.properties.get("color") == "#ff0000"

    def test_heading_with_mixed_formatting(self):
        """Export heading with multiple formatting styles."""
        elements = [
            {
                "paragraph": {
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "headingId": "h.mixed",
                    },
                    "elements": [
                        {"textRun": {"content": "Normal "}},
                        {
                            "textRun": {
                                "content": "bold",
                                "textStyle": {"bold": True},
                            }
                        },
                        {"textRun": {"content": " and "}},
                        {
                            "textRun": {
                                "content": "italic",
                                "textStyle": {"italic": True},
                            }
                        },
                        {"textRun": {"content": " text\n"}},
                    ],
                },
                "startIndex": 1,
            }
        ]

        doc, anchors, embedded, warnings = convert_elements(elements, {}, {})

        heading = doc.children[0]
        assert isinstance(heading, HeadingNode)
        # Should have TextNode, BoldNode, TextNode, ItalicNode, TextNode
        bold_nodes = [n for n in heading.content if isinstance(n, BoldNode)]
        italic_nodes = [n for n in heading.content if isinstance(n, ItalicNode)]
        assert len(bold_nodes) == 1
        assert len(italic_nodes) == 1


class TestExportBody:
    """Tests for full body export."""

    def test_simple_document(self):
        """Export simple document."""
        document = {}
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.intro",
                        },
                        "elements": [{"textRun": {"content": "Introduction\n"}}],
                    },
                    "startIndex": 1,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Content here.\n"}}],
                    },
                    "startIndex": 15,
                },
            ]
        }

        result = export_body(document, body, "")

        assert "# {^ h.intro}Introduction" in result.content
        assert "Content here." in result.content
        assert len(result.anchors) == 1
        assert result.anchors[0].anchor_id == "h.intro"

    def test_document_with_formatting(self):
        """Export document with formatting."""
        document = {}
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [
                            {"textRun": {"content": "This is "}},
                            {
                                "textRun": {
                                    "content": "bold",
                                    "textStyle": {"bold": True},
                                }
                            },
                            {"textRun": {"content": " text.\n"}},
                        ],
                    },
                    "startIndex": 1,
                }
            ]
        }

        result = export_body(document, body, "")

        assert "**bold**" in result.content
