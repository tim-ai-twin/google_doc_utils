"""Unit tests for MEBDF to Google Docs import.

Tests cover:
- Text insertion request building
- Formatting request building
- Embedded object validation
- Paragraph style building
"""

import pytest

from extended_google_doc_utils.converter.exceptions import EmbeddedObjectNotFoundError
from extended_google_doc_utils.converter.mebdf_parser import (
    BoldNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    ListItemNode,
    ListNode,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.mebdf_to_gdoc import (
    build_import_requests,
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

    def test_warnings_collected(self):
        """Import collects warnings for unsupported features."""
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

        # Should have warning about highlight import
        assert any("highlight" in w.lower() for w in warnings)
