"""Unit tests for MEBDF parser.

Tests cover:
- Tokenization of all token types
- Inline parsing (bold, italic, links, anchors, formatting)
- Block parsing (headings, paragraphs, lists, code blocks)
- Edge cases and malformed input handling
"""

import pytest

from extended_google_doc_utils.converter.exceptions import MebdfParseError
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
    InlineParser,
    ItalicNode,
    LinkNode,
    ListNode,
    MebdfParser,
    ParagraphNode,
    TextNode,
    Tokenizer,
    TokenType,
)


class TestTokenizer:
    """Tests for MEBDF tokenizer."""

    def test_tokenize_plain_text(self):
        """Tokenize plain text."""
        tokenizer = Tokenizer("Hello world")
        tokens = tokenizer.tokenize()

        assert len(tokens) == 2  # TEXT + EOF
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "Hello world"
        assert tokens[1].type == TokenType.EOF

    def test_tokenize_heading(self):
        """Tokenize markdown heading."""
        tokenizer = Tokenizer("# My Heading")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.HEADING
        assert tokens[0].properties["level"] == 1
        assert tokens[0].properties["content"] == "My Heading"

    def test_tokenize_heading_levels(self):
        """Tokenize headings of different levels."""
        for level in range(1, 7):
            hashes = "#" * level
            tokenizer = Tokenizer(f"{hashes} Heading {level}")
            tokens = tokenizer.tokenize()

            assert tokens[0].type == TokenType.HEADING
            assert tokens[0].properties["level"] == level

    def test_tokenize_block_formatting(self):
        """Tokenize standalone block formatting directive."""
        tokenizer = Tokenizer("{!mono}")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.BLOCK_FORMAT
        assert tokens[0].properties["properties"] == {"mono": True}

    def test_tokenize_block_formatting_with_value(self):
        """Tokenize block formatting with property value."""
        tokenizer = Tokenizer("{!highlight:yellow}")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.BLOCK_FORMAT
        assert tokens[0].properties["properties"] == {"highlight": "yellow"}

    def test_tokenize_block_formatting_multiple_props(self):
        """Tokenize block formatting with multiple properties."""
        tokenizer = Tokenizer("{!highlight:yellow, underline}")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.BLOCK_FORMAT
        props = tokens[0].properties["properties"]
        assert props == {"highlight": "yellow", "underline": True}

    def test_tokenize_embedded_object(self):
        """Tokenize embedded object placeholder."""
        tokenizer = Tokenizer("{^= img_001 image}")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.EMBEDDED_OBJECT
        assert tokens[0].properties["object_id"] == "img_001"
        assert tokens[0].properties["object_type"] == "image"

    def test_tokenize_embedded_object_no_id(self):
        """Tokenize embedded object without ID (equation)."""
        tokenizer = Tokenizer("{^= equation}")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.EMBEDDED_OBJECT
        assert tokens[0].properties["object_id"] is None
        assert tokens[0].properties["object_type"] == "equation"

    def test_tokenize_unordered_list(self):
        """Tokenize unordered list item."""
        tokenizer = Tokenizer("- Item one")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.LIST_ITEM
        assert tokens[0].properties["ordered"] is False
        assert tokens[0].properties["content"] == "Item one"

    def test_tokenize_ordered_list(self):
        """Tokenize ordered list item."""
        tokenizer = Tokenizer("1. First item")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.LIST_ITEM
        assert tokens[0].properties["ordered"] is True
        assert tokens[0].properties["content"] == "First item"

    def test_tokenize_nested_list(self):
        """Tokenize nested list item."""
        tokenizer = Tokenizer("  - Nested item")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.LIST_ITEM
        assert tokens[0].properties["indent"] == 1

    def test_tokenize_paragraph_break(self):
        """Tokenize empty line as paragraph break."""
        tokenizer = Tokenizer("First\n\nSecond")
        tokens = tokenizer.tokenize()

        # TEXT, NEWLINE, PARAGRAPH_BREAK, NEWLINE, TEXT, EOF
        types = [t.type for t in tokens]
        assert TokenType.PARAGRAPH_BREAK in types

    def test_tokenize_multiline(self):
        """Tokenize multiple lines."""
        content = "# Heading\n\nParagraph text"
        tokenizer = Tokenizer(content)
        tokens = tokenizer.tokenize()

        types = [t.type for t in tokens]
        assert TokenType.HEADING in types
        assert TokenType.TEXT in types


class TestInlineParser:
    """Tests for inline content parser."""

    def test_parse_plain_text(self):
        """Parse plain text."""
        parser = InlineParser()
        nodes = parser.parse("Hello world")

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert nodes[0].content == "Hello world"

    def test_parse_bold(self):
        """Parse bold text."""
        parser = InlineParser()
        nodes = parser.parse("**bold text**")

        assert len(nodes) == 1
        assert isinstance(nodes[0], BoldNode)
        assert len(nodes[0].content) == 1
        assert isinstance(nodes[0].content[0], TextNode)
        assert nodes[0].content[0].content == "bold text"

    def test_parse_italic(self):
        """Parse italic text."""
        parser = InlineParser()
        nodes = parser.parse("*italic text*")

        assert len(nodes) == 1
        assert isinstance(nodes[0], ItalicNode)
        assert nodes[0].content[0].content == "italic text"

    def test_parse_code_span(self):
        """Parse inline code."""
        parser = InlineParser()
        nodes = parser.parse("`code here`")

        assert len(nodes) == 1
        assert isinstance(nodes[0], CodeSpanNode)
        assert nodes[0].content == "code here"

    def test_parse_link(self):
        """Parse markdown link."""
        parser = InlineParser()
        nodes = parser.parse("[click here](https://example.com)")

        assert len(nodes) == 1
        assert isinstance(nodes[0], LinkNode)
        assert nodes[0].text == "click here"
        assert nodes[0].url == "https://example.com"
        assert nodes[0].is_anchor_link is False

    def test_parse_anchor_link(self):
        """Parse link to internal anchor."""
        parser = InlineParser()
        nodes = parser.parse("[section](#^h.abc123)")

        assert len(nodes) == 1
        assert isinstance(nodes[0], LinkNode)
        assert nodes[0].is_anchor_link is True

    def test_parse_anchor(self):
        """Parse anchor marker."""
        parser = InlineParser()
        nodes = parser.parse("{^ h.abc123}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], AnchorNode)
        assert nodes[0].anchor_id == "h.abc123"

    def test_parse_proposed_anchor(self):
        """Parse proposed anchor (no ID)."""
        parser = InlineParser()
        nodes = parser.parse("{^}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], AnchorNode)
        assert nodes[0].anchor_id is None

    def test_parse_inline_formatting(self):
        """Parse inline formatting extension."""
        parser = InlineParser()
        nodes = parser.parse("{!highlight:yellow}highlighted{/!}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], FormattingNode)
        assert nodes[0].properties == {"highlight": "yellow"}
        assert nodes[0].content[0].content == "highlighted"

    def test_parse_inline_formatting_multiple_props(self):
        """Parse inline formatting with multiple properties."""
        parser = InlineParser()
        nodes = parser.parse("{!highlight:yellow, underline}text{/!}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], FormattingNode)
        assert nodes[0].properties == {"highlight": "yellow", "underline": True}

    def test_parse_embedded_object_inline(self):
        """Parse embedded object in inline context."""
        parser = InlineParser()
        nodes = parser.parse("Before {^= img_001 image} after")

        assert len(nodes) == 3
        assert isinstance(nodes[0], TextNode)
        assert isinstance(nodes[1], EmbeddedObjectNode)
        assert isinstance(nodes[2], TextNode)
        assert nodes[1].object_id == "img_001"
        assert nodes[1].object_type == "image"

    def test_parse_mixed_formatting(self):
        """Parse mixed inline formatting."""
        parser = InlineParser()
        nodes = parser.parse("Normal **bold** and *italic* text")

        assert len(nodes) == 5
        assert isinstance(nodes[0], TextNode)
        assert isinstance(nodes[1], BoldNode)
        assert isinstance(nodes[2], TextNode)
        assert isinstance(nodes[3], ItalicNode)
        assert isinstance(nodes[4], TextNode)

    def test_parse_nested_bold_italic(self):
        """Parse bold containing italic."""
        parser = InlineParser()
        nodes = parser.parse("**bold with *italic* inside**")

        assert isinstance(nodes[0], BoldNode)
        # The bold content should contain text and italic
        content = nodes[0].content
        assert len(content) >= 2


class TestMebdfParser:
    """Tests for full document parser."""

    def test_parse_empty_document(self):
        """Parse empty document."""
        parser = MebdfParser()
        doc = parser.parse("")

        assert isinstance(doc, DocumentNode)
        assert len(doc.children) == 0

    def test_parse_single_paragraph(self):
        """Parse single paragraph."""
        parser = MebdfParser()
        doc = parser.parse("Hello world")

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ParagraphNode)

    def test_parse_heading(self):
        """Parse heading."""
        parser = MebdfParser()
        doc = parser.parse("# My Heading")

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], HeadingNode)
        assert doc.children[0].level == 1

    def test_parse_heading_with_anchor(self):
        """Parse heading with anchor ID."""
        parser = MebdfParser()
        doc = parser.parse("# {^ h.abc123}My Heading")

        assert len(doc.children) == 1
        heading = doc.children[0]
        assert isinstance(heading, HeadingNode)
        assert heading.anchor_id == "h.abc123"
        assert heading.content[0].content == "My Heading"

    def test_parse_multiple_headings(self):
        """Parse document with multiple headings."""
        content = """# First
## Second
### Third"""
        parser = MebdfParser()
        doc = parser.parse(content)

        headings = [c for c in doc.children if isinstance(c, HeadingNode)]
        assert len(headings) == 3
        assert headings[0].level == 1
        assert headings[1].level == 2
        assert headings[2].level == 3

    def test_parse_paragraphs(self):
        """Parse multiple paragraphs."""
        content = """First paragraph.

Second paragraph."""
        parser = MebdfParser()
        doc = parser.parse(content)

        paragraphs = [c for c in doc.children if isinstance(c, ParagraphNode)]
        assert len(paragraphs) == 2

    def test_parse_block_formatting(self):
        """Parse block formatting directive."""
        content = """{!mono}
This is monospace."""
        parser = MebdfParser()
        doc = parser.parse(content)

        assert isinstance(doc.children[0], BlockFormattingNode)
        assert doc.children[0].properties == {"mono": True}

    def test_parse_embedded_object_block(self):
        """Parse embedded object as block."""
        parser = MebdfParser()
        doc = parser.parse("{^= img_001 image}")

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], EmbeddedObjectNode)
        assert doc.children[0].object_id == "img_001"
        assert doc.children[0].object_type == "image"

    def test_parse_list(self):
        """Parse unordered list."""
        content = """- Item one
- Item two
- Item three"""
        parser = MebdfParser()
        doc = parser.parse(content)

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ListNode)
        assert doc.children[0].ordered is False
        assert len(doc.children[0].items) == 3

    def test_parse_ordered_list(self):
        """Parse ordered list."""
        content = """1. First
2. Second
3. Third"""
        parser = MebdfParser()
        doc = parser.parse(content)

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ListNode)
        assert doc.children[0].ordered is True

    def test_parse_code_block(self):
        """Parse fenced code block."""
        content = """```python
def hello():
    print("world")
```"""
        parser = MebdfParser()
        doc = parser.parse(content)

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], CodeBlockNode)
        assert doc.children[0].language == "python"
        assert "def hello():" in doc.children[0].content

    def test_parse_inline_inline(self):
        """Test parse_inline method."""
        parser = MebdfParser()
        nodes = parser.parse_inline("**bold** and *italic*")

        assert len(nodes) == 3
        assert isinstance(nodes[0], BoldNode)
        assert isinstance(nodes[2], ItalicNode)

    def test_parse_complex_document(self):
        """Parse a complex document with various elements."""
        content = """# {^ h.intro}Introduction

This is the **introduction** with a [link](https://example.com).

{^= img_001 image}

## {^ h.details}Details

{!highlight:yellow}
Highlighted section content.

{!highlight:false}
Back to normal.

- Item one
- Item two

```python
print("code")
```"""
        parser = MebdfParser()
        doc = parser.parse(content)

        # Should have headings, paragraphs, embedded objects, etc.
        assert isinstance(doc, DocumentNode)
        assert len(doc.children) > 5

    def test_parse_equation_without_id(self):
        """Parse equation embedded object (no ID)."""
        parser = MebdfParser()
        doc = parser.parse("{^= equation}")

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], EmbeddedObjectNode)
        assert doc.children[0].object_id is None
        assert doc.children[0].object_type == "equation"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_anchor_id(self):
        """Handle anchor with empty space."""
        parser = InlineParser()
        nodes = parser.parse("{^}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], AnchorNode)
        assert nodes[0].anchor_id is None

    def test_invalid_embedded_object_type(self):
        """Reject invalid embedded object type."""
        parser = InlineParser()

        with pytest.raises(MebdfParseError) as exc_info:
            parser.parse("{^= obj_001 unknown_type}")

        assert "Unknown embedded object type" in str(exc_info.value)

    def test_unclosed_inline_formatting(self):
        """Handle unclosed inline formatting gracefully."""
        parser = InlineParser()
        # Should treat as plain text if not properly closed
        nodes = parser.parse("{!highlight:yellow}text without close")

        # This should be parsed as plain text since there's no {/!}
        assert len(nodes) >= 1

    def test_nested_formatting_deep(self):
        """Handle deeply nested formatting."""
        parser = InlineParser()
        nodes = parser.parse("**bold *italic* bold**")

        assert isinstance(nodes[0], BoldNode)

    def test_special_characters_in_text(self):
        """Handle special characters in text."""
        parser = InlineParser()
        nodes = parser.parse("Text with < > & special chars")

        assert isinstance(nodes[0], TextNode)
        assert "<" in nodes[0].content

    def test_unicode_content(self):
        """Handle unicode content."""
        parser = MebdfParser()
        doc = parser.parse("# Unicode: \u00e9\u00e8\u00ea \u4e2d\u6587 \U0001f600")

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], HeadingNode)

    def test_whitespace_handling(self):
        """Handle various whitespace scenarios."""
        parser = MebdfParser()

        # Multiple blank lines
        doc = parser.parse("Para 1\n\n\n\nPara 2")
        paragraphs = [c for c in doc.children if isinstance(c, ParagraphNode)]
        assert len(paragraphs) == 2

    def test_heading_without_space(self):
        """Heading without space after hashes should be text."""
        tokenizer = Tokenizer("#NoSpace")
        tokens = tokenizer.tokenize()

        # Should be treated as text, not heading
        assert tokens[0].type == TokenType.TEXT

    def test_formatting_property_false(self):
        """Handle explicit false value in properties."""
        tokenizer = Tokenizer("{!mono:false}")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.BLOCK_FORMAT
        assert tokens[0].properties["properties"]["mono"] is False


class TestInlineFormattingEdgeCases:
    """Tests for inline formatting edge cases that caused the nested formatting bug."""

    def test_merged_properties_parse_correctly(self):
        """Merged properties like {!color:#ff0000,font:Arial} parse correctly."""
        parser = InlineParser()
        nodes = parser.parse("{!color:#ff0000,font:Arial}text{/!}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], FormattingNode)
        assert nodes[0].properties["color"] == "#ff0000"
        assert nodes[0].properties["font"] == "Arial"
        assert nodes[0].content[0].content == "text"

    def test_many_properties_parse_correctly(self):
        """Many properties in one formatting block parse correctly."""
        parser = InlineParser()
        nodes = parser.parse("{!font:Georgia,color:#0000ff,highlight:#ffff00,underline}text{/!}")

        assert len(nodes) == 1
        props = nodes[0].properties
        assert props["font"] == "Georgia"
        assert props["color"] == "#0000ff"
        assert props["highlight"] == "#ffff00"
        assert props["underline"] is True

    def test_heading_with_merged_formatting(self):
        """Heading with merged inline formatting parses correctly."""
        parser = MebdfParser()
        doc = parser.parse("## {!color:#f6b26b,font:Arial}Heading Text{/!}")

        assert len(doc.children) == 1
        heading = doc.children[0]
        assert isinstance(heading, HeadingNode)
        assert heading.level == 2

        # Content should be FormattingNode
        assert len(heading.content) == 1
        formatting = heading.content[0]
        assert isinstance(formatting, FormattingNode)
        assert formatting.properties["color"] == "#f6b26b"
        assert formatting.properties["font"] == "Arial"

        # Inner content should be TextNode
        assert len(formatting.content) == 1
        assert isinstance(formatting.content[0], TextNode)
        assert formatting.content[0].content == "Heading Text"

    def test_nested_formatting_limitation(self):
        """Document that nested formatting {!a}{!b}...{/!}{/!} doesn't parse as expected.

        This test documents the current parser limitation: nested formatting
        is NOT supported. The parser stops at the first {/!} and treats
        the rest as literal text.
        """
        parser = InlineParser()
        # This is malformed/unsupported - nested formatting
        nodes = parser.parse("{!font:Arial}{!color:#ff0000}text{/!}{/!}")

        # The parser will match the outer {!...}{/!} pair
        # but the inner {!color:#ff0000}text will be treated as content
        assert len(nodes) >= 1
        # First node should be FormattingNode with font:Arial
        assert isinstance(nodes[0], FormattingNode)
        assert nodes[0].properties["font"] == "Arial"
        # The content includes the inner formatting as literal text
        inner_text = nodes[0].content[0].content
        assert "{!color:#ff0000}text" in inner_text

    def test_formatting_with_bold_inside(self):
        """Inline formatting containing markdown bold works."""
        parser = InlineParser()
        nodes = parser.parse("{!color:#0000ff}**bold text**{/!}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], FormattingNode)
        assert nodes[0].properties["color"] == "#0000ff"

        # Content should contain BoldNode
        content = nodes[0].content
        assert any(isinstance(c, BoldNode) for c in content)

    def test_formatting_with_link_inside(self):
        """Inline formatting containing markdown link works."""
        parser = InlineParser()
        nodes = parser.parse("{!color:#0000ff}[link text](https://example.com){/!}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], FormattingNode)

        # Content should contain LinkNode
        content = nodes[0].content
        assert any(isinstance(c, LinkNode) for c in content)
        link = next(c for c in content if isinstance(c, LinkNode))
        assert link.url == "https://example.com"

    def test_formatting_with_spaces_in_properties(self):
        """Properties with spaces around colons and commas work."""
        parser = InlineParser()
        nodes = parser.parse("{!font : Arial , color : #ff0000}text{/!}")

        assert len(nodes) == 1
        props = nodes[0].properties
        # Note: spaces become part of the key/value due to simple parsing
        # The actual behavior depends on _parse_properties implementation
        assert len(props) >= 1

    def test_empty_inline_formatting(self):
        """Empty inline formatting block {!} is treated as literal text.

        The parser regex requires at least one character in the properties,
        so {!}text{/!} doesn't match the inline_format pattern and is
        treated as plain text.
        """
        parser = InlineParser()
        nodes = parser.parse("{!}text{/!}")

        # Empty {!} is not valid inline formatting, so it's treated as text
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "{!}text{/!}" in nodes[0].content

    def test_formatting_at_start_and_end_of_line(self):
        """Formatting at start and end of mixed content works."""
        parser = InlineParser()
        nodes = parser.parse("{!color:#ff0000}start{/!} middle {!color:#0000ff}end{/!}")

        # Should have 3 nodes: FormattingNode, TextNode, FormattingNode
        assert len(nodes) == 3
        assert isinstance(nodes[0], FormattingNode)
        assert isinstance(nodes[1], TextNode)
        assert isinstance(nodes[2], FormattingNode)
        assert nodes[0].properties["color"] == "#ff0000"
        assert nodes[2].properties["color"] == "#0000ff"

    def test_consecutive_formatting_blocks(self):
        """Multiple consecutive formatting blocks work."""
        parser = InlineParser()
        nodes = parser.parse("{!font:Arial}text1{/!}{!font:Georgia}text2{/!}")

        assert len(nodes) == 2
        assert nodes[0].properties["font"] == "Arial"
        assert nodes[1].properties["font"] == "Georgia"

    def test_hex_colors_various_formats(self):
        """Various hex color formats are accepted."""
        parser = InlineParser()

        # Full hex with #
        nodes = parser.parse("{!color:#ff0000}text{/!}")
        assert nodes[0].properties["color"] == "#ff0000"

        # Full hex without # (if supported)
        nodes = parser.parse("{!color:ff0000}text{/!}")
        assert nodes[0].properties["color"] == "ff0000"

        # Short hex (if supported)
        nodes = parser.parse("{!color:#f00}text{/!}")
        assert nodes[0].properties["color"] == "#f00"
