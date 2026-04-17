"""Unit tests for Plain Markdown Serializer.

Tests cover:
- Plain text passthrough
- Bold/italic preserved as standard markdown
- MEBDF formatting markers stripped
- Heading anchors stripped
- Embedded objects become [image] placeholder
- Links preserved
- Lists preserved
- Empty document produces empty string
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
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.plain_serializer import PlainMarkdownSerializer


@pytest.fixture
def serializer():
    return PlainMarkdownSerializer()


class TestPlainTextPassthrough:
    """Test that plain text is passed through unchanged."""

    def test_plain_text(self, serializer):
        """Plain text content is emitted unchanged."""
        doc = DocumentNode(children=[ParagraphNode(content=[TextNode("Hello world")])])

        result = serializer.serialize(doc)
        assert result == "Hello world"

    def test_multiple_paragraphs(self, serializer):
        """Multiple paragraphs joined with double newline."""
        doc = DocumentNode(
            children=[
                ParagraphNode(content=[TextNode("First paragraph")]),
                ParagraphNode(content=[TextNode("Second paragraph")]),
            ]
        )

        result = serializer.serialize(doc)
        assert result == "First paragraph\n\nSecond paragraph"


class TestBoldItalicPreserved:
    """Test that bold and italic use standard markdown syntax."""

    def test_bold(self, serializer):
        """Bold text uses **markers**."""
        doc = DocumentNode(
            children=[ParagraphNode(content=[BoldNode(content=[TextNode("bold")])])]
        )

        result = serializer.serialize(doc)
        assert result == "**bold**"

    def test_italic(self, serializer):
        """Italic text uses *markers*."""
        doc = DocumentNode(
            children=[ParagraphNode(content=[ItalicNode(content=[TextNode("italic")])])]
        )

        result = serializer.serialize(doc)
        assert result == "*italic*"

    def test_bold_italic_nested(self, serializer):
        """Bold wrapping italic produces ***text***."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        BoldNode(content=[ItalicNode(content=[TextNode("both")])])
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "***both***"


class TestMebdfMarkersStripped:
    """Test that MEBDF-specific markers are stripped."""

    def test_formatting_node_stripped(self, serializer):
        """Inline formatting {!color:red}text{/!} becomes just 'text'."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"color": "#ff0000"},
                            content=[TextNode("red text")],
                        )
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "red text"
        assert "{!" not in result
        assert "{/!}" not in result

    def test_formatting_with_nested_bold(self, serializer):
        """Formatting wrapping bold keeps bold but strips MEBDF wrapper."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"highlight": "yellow", "underline": True},
                            content=[BoldNode(content=[TextNode("important")])],
                        )
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "**important**"
        assert "{!" not in result

    def test_block_formatting_stripped(self, serializer):
        """Block formatting directives are removed entirely."""
        doc = DocumentNode(
            children=[
                BlockFormattingNode(properties={"mono": True}),
                ParagraphNode(content=[TextNode("Some text")]),
            ]
        )

        result = serializer.serialize(doc)
        assert result == "Some text"
        assert "{!" not in result

    def test_anchor_node_stripped(self, serializer):
        """Standalone anchor nodes are stripped."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        AnchorNode(anchor_id="h.abc123"),
                        TextNode("text after anchor"),
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "text after anchor"
        assert "{^" not in result


class TestHeadingAnchorsStripped:
    """Test that heading anchor markers are stripped."""

    def test_heading_without_anchor(self, serializer):
        """Heading without anchor renders normally."""
        doc = DocumentNode(
            children=[HeadingNode(level=2, anchor_id=None, content=[TextNode("Title")])]
        )

        result = serializer.serialize(doc)
        assert result == "## Title"

    def test_heading_with_anchor_stripped(self, serializer):
        """Heading with anchor ID omits the {^ id} marker."""
        doc = DocumentNode(
            children=[
                HeadingNode(
                    level=1, anchor_id="h.abc123", content=[TextNode("Introduction")]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "# Introduction"
        assert "{^" not in result
        assert "h.abc123" not in result

    def test_all_heading_levels(self, serializer):
        """All heading levels render correctly."""
        for level in range(1, 7):
            doc = DocumentNode(
                children=[
                    HeadingNode(level=level, anchor_id="h.test", content=[TextNode("H")])
                ]
            )
            result = serializer.serialize(doc)
            expected_prefix = "#" * level
            assert result == f"{expected_prefix} H"


class TestEmbeddedObjectPlaceholder:
    """Test that embedded objects become [image] placeholder."""

    def test_image_becomes_placeholder(self, serializer):
        """Image embedded object becomes [image]."""
        doc = DocumentNode(
            children=[EmbeddedObjectNode(object_id="img_001", object_type="image")]
        )

        result = serializer.serialize(doc)
        assert result == "[image]"
        assert "{^=" not in result

    def test_chart_becomes_placeholder(self, serializer):
        """Chart embedded object also becomes [image]."""
        doc = DocumentNode(
            children=[EmbeddedObjectNode(object_id="chart_001", object_type="chart")]
        )

        result = serializer.serialize(doc)
        assert result == "[image]"

    def test_equation_becomes_placeholder(self, serializer):
        """Equation (no ID) also becomes [image]."""
        doc = DocumentNode(
            children=[EmbeddedObjectNode(object_id=None, object_type="equation")]
        )

        result = serializer.serialize(doc)
        assert result == "[image]"


class TestLinksPreserved:
    """Test that markdown links are preserved."""

    def test_link_preserved(self, serializer):
        """Links use standard markdown [text](url) format."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[LinkNode(text="click here", url="https://example.com")]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "[click here](https://example.com)"

    def test_link_in_paragraph(self, serializer):
        """Links within paragraph text are preserved."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        TextNode("Visit "),
                        LinkNode(text="Google", url="https://google.com"),
                        TextNode(" for more."),
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "Visit [Google](https://google.com) for more."


class TestListsPreserved:
    """Test that lists are preserved in standard markdown."""

    def test_unordered_list(self, serializer):
        """Unordered list items use - prefix."""
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

    def test_ordered_list(self, serializer):
        """Ordered list items use numbered prefix."""
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

    def test_nested_list(self, serializer):
        """Nested list items are indented."""
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


class TestEmptyDocument:
    """Test that empty document produces empty string."""

    def test_empty_document(self, serializer):
        """Empty document produces empty string."""
        doc = DocumentNode(children=[])

        result = serializer.serialize(doc)
        assert result == ""


class TestCodePreserved:
    """Test that code spans and blocks are preserved."""

    def test_code_span(self, serializer):
        """Inline code is preserved."""
        doc = DocumentNode(
            children=[ParagraphNode(content=[CodeSpanNode(content="x = 1")])]
        )

        result = serializer.serialize(doc)
        assert result == "`x = 1`"

    def test_code_block(self, serializer):
        """Code blocks are preserved."""
        doc = DocumentNode(
            children=[CodeBlockNode(content="print('hello')", language="python")]
        )

        result = serializer.serialize(doc)
        assert "```python" in result
        assert "print('hello')" in result
        assert result.endswith("```")


class TestMixedContent:
    """Test complex documents with mixed content types."""

    def test_mixed_paragraph(self, serializer):
        """Paragraph with mixed formatting strips MEBDF but keeps markdown."""
        doc = DocumentNode(
            children=[
                ParagraphNode(
                    content=[
                        TextNode("Normal "),
                        BoldNode(content=[TextNode("bold")]),
                        TextNode(" and "),
                        FormattingNode(
                            properties={"color": "#ff0000"},
                            content=[TextNode("colored")],
                        ),
                        TextNode(" text"),
                    ]
                )
            ]
        )

        result = serializer.serialize(doc)
        assert result == "Normal **bold** and colored text"
        assert "{!" not in result

    def test_complex_document(self, serializer):
        """Full document with headings, formatting, lists, and embeds."""
        doc = DocumentNode(
            children=[
                HeadingNode(
                    level=1, anchor_id="h.intro", content=[TextNode("Introduction")]
                ),
                ParagraphNode(
                    content=[
                        TextNode("This is "),
                        BoldNode(content=[TextNode("important")]),
                        TextNode(" text."),
                    ]
                ),
                EmbeddedObjectNode(object_id="img_001", object_type="image"),
                HeadingNode(
                    level=2, anchor_id="h.details", content=[TextNode("Details")]
                ),
                ParagraphNode(
                    content=[
                        FormattingNode(
                            properties={"highlight": "yellow"},
                            content=[TextNode("Highlighted section.")],
                        )
                    ]
                ),
                ListNode(
                    ordered=False,
                    items=[
                        ListItemNode(content=[TextNode("Item one")], indent_level=0),
                        ListItemNode(content=[TextNode("Item two")], indent_level=0),
                    ],
                ),
            ]
        )

        result = serializer.serialize(doc)
        assert "# Introduction" in result
        assert "h.intro" not in result
        assert "**important**" in result
        assert "[image]" in result
        assert "## Details" in result
        assert "h.details" not in result
        assert "Highlighted section." in result
        assert "{!" not in result
        assert "- Item one" in result
        assert "- Item two" in result
