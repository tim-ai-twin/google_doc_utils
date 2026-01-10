"""Unit tests for MEBDF serializer.

Tests cover:
- Serialization of all node types
- Round-trip AST preservation (parse -> serialize -> parse)
- Property serialization
"""

import pytest

from extended_google_doc_utils.converter.mebdf_parser import (
    AnchorNode,
    BlockFormattingNode,
    BoldNode,
    CodeBlockNode,
    CodeSpanNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    LinkNode,
    ListItemNode,
    ListNode,
    MebdfParser,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.mebdf_serializer import MebdfSerializer


class TestSerializeNodes:
    """Test serialization of individual node types."""

    def test_serialize_text_node(self):
        """Serialize plain text."""
        serializer = MebdfSerializer()
        doc = DocumentNode(children=[ParagraphNode(content=[TextNode("Hello world")])])

        result = serializer.serialize(doc)
        assert result == "Hello world"

    def test_serialize_bold(self):
        """Serialize bold text."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[BoldNode(content=[TextNode("bold")])])]
        )

        result = serializer.serialize(doc)
        assert result == "**bold**"

    def test_serialize_italic(self):
        """Serialize italic text."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[ItalicNode(content=[TextNode("italic")])])]
        )

        result = serializer.serialize(doc)
        assert result == "*italic*"

    def test_serialize_code_span(self):
        """Serialize inline code."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[CodeSpanNode(content="code")])]
        )

        result = serializer.serialize(doc)
        assert result == "`code`"

    def test_serialize_code_block(self):
        """Serialize code block."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[CodeBlockNode(content="print('hello')", language="python")]
        )

        result = serializer.serialize(doc)
        assert "```python" in result
        assert "print('hello')" in result
        assert result.endswith("```")

    def test_serialize_link(self):
        """Serialize link."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[LinkNode(text="click", url="https://example.com")]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "[click](https://example.com)"

    def test_serialize_anchor(self):
        """Serialize anchor."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[AnchorNode(anchor_id="h.abc123")])]
        )

        result = serializer.serialize(doc)
        assert result == "{^ h.abc123}"

    def test_serialize_proposed_anchor(self):
        """Serialize proposed anchor (no ID)."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[AnchorNode(anchor_id=None)])]
        )

        result = serializer.serialize(doc)
        assert result == "{^}"

    def test_serialize_embedded_object(self):
        """Serialize embedded object."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[EmbeddedObjectNode(object_id="img_001", object_type="image")]
        )

        result = serializer.serialize(doc)
        assert result == "{^= img_001 image}"

    def test_serialize_embedded_object_no_id(self):
        """Serialize embedded object without ID (equation)."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[EmbeddedObjectNode(object_id=None, object_type="equation")]
        )

        result = serializer.serialize(doc)
        assert result == "{^= equation}"

    def test_serialize_inline_formatting(self):
        """Serialize inline formatting."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"highlight": "yellow"},
                            content=[TextNode("highlighted")],
                        )
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert "{!highlight:yellow}" in result
        assert "highlighted" in result
        assert "{/!}" in result

    def test_serialize_inline_formatting_multiple_props(self):
        """Serialize inline formatting with multiple properties."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"highlight": "yellow", "underline": True},
                            content=[TextNode("text")],
                        )
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert "highlight:yellow" in result
        assert "underline" in result

    def test_serialize_block_formatting(self):
        """Serialize block formatting."""
        serializer = MebdfSerializer()
        doc = DocumentNode(children=[BlockFormattingNode(properties={"mono": True})])

        result = serializer.serialize(doc)
        assert result == "{!mono}"

    def test_serialize_block_formatting_false(self):
        """Serialize block formatting with false value."""
        serializer = MebdfSerializer()
        doc = DocumentNode(children=[BlockFormattingNode(properties={"mono": False})])

        result = serializer.serialize(doc)
        assert result == "{!mono:false}"

    def test_serialize_heading(self):
        """Serialize heading."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[HeadingNode(level=2, anchor_id=None, content=[TextNode("Title")])]
        )

        result = serializer.serialize(doc)
        assert result == "## Title"

    def test_serialize_heading_with_anchor(self):
        """Serialize heading with anchor."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                HeadingNode(level=1, anchor_id="h.abc123", content=[TextNode("Title")])
            ]
        )

        result = serializer.serialize(doc)
        assert result == "# {^ h.abc123}Title"

    def test_serialize_unordered_list(self):
        """Serialize unordered list."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ListNode(
                    ordered=False,
                    items=[
                        ListItemNode(content=[TextNode("One")], indent_level=0),
                        ListItemNode(content=[TextNode("Two")], indent_level=0),
                    ],
                )
            ]
        )

        result = serializer.serialize(doc)
        assert "- One" in result
        assert "- Two" in result

    def test_serialize_ordered_list(self):
        """Serialize ordered list."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ListNode(
                    ordered=True,
                    items=[
                        ListItemNode(content=[TextNode("First")], indent_level=0),
                        ListItemNode(content=[TextNode("Second")], indent_level=0),
                    ],
                )
            ]
        )

        result = serializer.serialize(doc)
        assert "1. First" in result
        assert "2. Second" in result

    def test_serialize_nested_list(self):
        """Serialize nested list."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ListNode(
                    ordered=False,
                    items=[
                        ListItemNode(content=[TextNode("Parent")], indent_level=0),
                        ListItemNode(content=[TextNode("Child")], indent_level=1),
                    ],
                )
            ]
        )

        result = serializer.serialize(doc)
        assert "- Parent" in result
        assert "  - Child" in result


class TestRoundTrip:
    """Test that parse -> serialize -> parse produces equivalent AST."""

    def setup_method(self):
        """Set up parser and serializer."""
        self.parser = MebdfParser()
        self.serializer = MebdfSerializer()

    def test_roundtrip_plain_text(self):
        """Round-trip plain text."""
        original = "Hello world"
        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        assert len(doc1.children) == len(doc2.children)

    def test_roundtrip_heading(self):
        """Round-trip heading."""
        original = "# My Heading"
        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        assert isinstance(doc2.children[0], HeadingNode)
        assert doc2.children[0].level == 1

    def test_roundtrip_heading_with_anchor(self):
        """Round-trip heading with anchor."""
        original = "# {^ h.abc123}My Heading"
        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        heading = doc2.children[0]
        assert isinstance(heading, HeadingNode)
        assert heading.anchor_id == "h.abc123"

    def test_roundtrip_formatting(self):
        """Round-trip inline formatting."""
        original = "{!highlight:yellow}text{/!}"
        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        # Find the formatting node
        para = doc2.children[0]
        assert isinstance(para, ParagraphNode)
        assert any(isinstance(n, FormattingNode) for n in para.content)

    def test_roundtrip_embedded_object(self):
        """Round-trip embedded object."""
        original = "{^= img_001 image}"
        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        assert isinstance(doc2.children[0], EmbeddedObjectNode)
        assert doc2.children[0].object_id == "img_001"
        assert doc2.children[0].object_type == "image"

    def test_roundtrip_list(self):
        """Round-trip list."""
        original = """- One
- Two
- Three"""
        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        assert isinstance(doc2.children[0], ListNode)
        assert len(doc2.children[0].items) == 3

    def test_roundtrip_complex_document(self):
        """Round-trip complex document."""
        original = """# {^ h.intro}Introduction

This is **bold** and *italic* text.

{^= img_001 image}

## {^ h.details}Details

{!highlight:yellow}Highlighted section.{/!}

- Item one
- Item two"""

        doc1 = self.parser.parse(original)
        serialized = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(serialized)

        # Count headings
        headings1 = [c for c in doc1.children if isinstance(c, HeadingNode)]
        headings2 = [c for c in doc2.children if isinstance(c, HeadingNode)]
        assert len(headings1) == len(headings2)

        # Count embedded objects
        embeds1 = [c for c in doc1.children if isinstance(c, EmbeddedObjectNode)]
        embeds2 = [c for c in doc2.children if isinstance(c, EmbeddedObjectNode)]
        assert len(embeds1) == len(embeds2)


class TestEdgeCases:
    """Edge cases for serialization."""

    def test_serialize_empty_document(self):
        """Serialize empty document."""
        serializer = MebdfSerializer()
        doc = DocumentNode(children=[])

        result = serializer.serialize(doc)
        assert result == ""

    def test_serialize_mixed_content(self):
        """Serialize paragraph with mixed content."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        TextNode("Normal "),
                        BoldNode(content=[TextNode("bold")]),
                        TextNode(" and "),
                        ItalicNode(content=[TextNode("italic")]),
                        TextNode(" text"),
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "Normal **bold** and *italic* text"

    def test_serialize_heading_levels(self):
        """Serialize all heading levels."""
        serializer = MebdfSerializer()

        for level in range(1, 7):
            doc = DocumentNode(
                children=[
                    HeadingNode(level=level, anchor_id=None, content=[TextNode("H")])
                ]
            )
            result = serializer.serialize(doc)
            expected_prefix = "#" * level
            assert result.startswith(expected_prefix + " ")

    def test_serialize_special_characters(self):
        """Serialize text with special characters."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[TextNode("Text with < > & chars")])]
        )

        result = serializer.serialize(doc)
        assert "<" in result
        assert ">" in result
        assert "&" in result

    def test_serialize_unicode(self):
        """Serialize unicode content."""
        serializer = MebdfSerializer()
        doc = DocumentNode(
            children=[ParagraphNode(content=[TextNode("\u00e9\u00e8\u00ea \u4e2d\u6587 \U0001f600")])]
        )

        result = serializer.serialize(doc)
        assert "\u00e9" in result
        assert "\u4e2d\u6587" in result
