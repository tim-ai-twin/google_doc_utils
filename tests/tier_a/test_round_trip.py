"""Round-trip tests for MEBDF conversion.

Tests verify that export→import preserves all formatting and anchors.
"""


from extended_google_doc_utils.converter.mebdf_parser import (
    AnchorNode,
    BoldNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    ListNode,
    MebdfParser,
    ParagraphNode,
)
from extended_google_doc_utils.converter.mebdf_serializer import MebdfSerializer


class TestRoundTripFormatting:
    """Tests for formatting preservation through round-trip."""

    def setup_method(self):
        """Set up parser and serializer."""
        self.parser = MebdfParser()
        self.serializer = MebdfSerializer()

    def test_bold_round_trip(self):
        """Bold formatting survives round-trip."""
        original = "This has **bold** text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        # Find bold node in both
        def find_bold(node):
            if isinstance(node, BoldNode):
                return True
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_bold(c) for c in children)
            return False

        assert find_bold(doc)
        assert find_bold(doc2)

    def test_italic_round_trip(self):
        """Italic formatting survives round-trip."""
        original = "This has *italic* text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_italic(node):
            if isinstance(node, ItalicNode):
                return True
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_italic(c) for c in children)
            return False

        assert find_italic(doc)
        assert find_italic(doc2)

    def test_highlight_round_trip(self):
        """Highlight formatting survives round-trip."""
        original = "This has {!highlight:yellow}highlighted{/!} text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_formatting_with_highlight(node):
            if isinstance(node, FormattingNode):
                return "highlight" in node.properties
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_formatting_with_highlight(c) for c in children)
            return False

        assert find_formatting_with_highlight(doc)
        assert find_formatting_with_highlight(doc2)

    def test_underline_round_trip(self):
        """Underline formatting survives round-trip."""
        original = "This has {!underline}underlined{/!} text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_formatting_with_underline(node):
            if isinstance(node, FormattingNode):
                return node.properties.get("underline") is True
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_formatting_with_underline(c) for c in children)
            return False

        assert find_formatting_with_underline(doc)
        assert find_formatting_with_underline(doc2)

    def test_mono_round_trip(self):
        """Monospace formatting survives round-trip."""
        original = "This has {!mono}monospace{/!} text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_formatting_with_mono(node):
            if isinstance(node, FormattingNode):
                return node.properties.get("mono") is True
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_formatting_with_mono(c) for c in children)
            return False

        assert find_formatting_with_mono(doc)
        assert find_formatting_with_mono(doc2)

    def test_color_round_trip(self):
        """Text color survives round-trip."""
        original = "This has {!color:#ff0000}red{/!} text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_formatting_with_color(node):
            if isinstance(node, FormattingNode):
                return "color" in node.properties
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_formatting_with_color(c) for c in children)
            return False

        assert find_formatting_with_color(doc)
        assert find_formatting_with_color(doc2)

    def test_combined_formatting_round_trip(self):
        """Combined formatting survives round-trip."""
        original = "This has {!highlight:yellow, underline}combined{/!} text."

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_combined(node):
            if isinstance(node, FormattingNode):
                return "highlight" in node.properties and "underline" in node.properties
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_combined(c) for c in children)
            return False

        assert find_combined(doc)
        assert find_combined(doc2)


class TestRoundTripAnchors:
    """Tests for anchor preservation through round-trip."""

    def setup_method(self):
        """Set up parser and serializer."""
        self.parser = MebdfParser()
        self.serializer = MebdfSerializer()

    def test_heading_anchor_round_trip(self):
        """Heading anchor survives round-trip."""
        original = "# {^ h.abc123}My Heading"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        # Both should have heading with anchor
        heading1 = doc.children[0]
        heading2 = doc2.children[0]

        assert isinstance(heading1, HeadingNode)
        assert isinstance(heading2, HeadingNode)
        assert heading1.anchor_id == "h.abc123"
        assert heading2.anchor_id == "h.abc123"

    def test_inline_anchor_round_trip(self):
        """Inline anchor survives round-trip."""
        original = "{^ bookmark_001}Text with bookmark"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_anchor(node):
            if isinstance(node, AnchorNode):
                return node.anchor_id
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                for c in children:
                    result = find_anchor(c)
                    if result:
                        return result
            return None

        assert find_anchor(doc) == "bookmark_001"
        assert find_anchor(doc2) == "bookmark_001"

    def test_proposed_anchor_round_trip(self):
        """Proposed anchor survives round-trip."""
        original = "{^}Text with proposed anchor"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_proposed_anchor(node):
            if isinstance(node, AnchorNode) and node.anchor_id is None:
                return True
            if isinstance(node, (DocumentNode, ParagraphNode)):
                children = node.children if hasattr(node, "children") else node.content
                return any(find_proposed_anchor(c) for c in children)
            return False

        assert find_proposed_anchor(doc)
        assert find_proposed_anchor(doc2)

    def test_multiple_anchors_round_trip(self):
        """Multiple anchors survive round-trip."""
        original = """# {^ h.first}First Heading

Content

## {^ h.second}Second Heading"""

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        headings1 = [c for c in doc.children if isinstance(c, HeadingNode)]
        headings2 = [c for c in doc2.children if isinstance(c, HeadingNode)]

        assert len(headings1) == 2
        assert len(headings2) == 2
        assert headings1[0].anchor_id == "h.first"
        assert headings2[0].anchor_id == "h.first"
        assert headings1[1].anchor_id == "h.second"
        assert headings2[1].anchor_id == "h.second"


class TestRoundTripEmbeddedObjects:
    """Tests for embedded object preservation through round-trip."""

    def setup_method(self):
        """Set up parser and serializer."""
        self.parser = MebdfParser()
        self.serializer = MebdfSerializer()

    def test_image_round_trip(self):
        """Image placeholder survives round-trip."""
        original = "{^= img_001 image}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        def find_embedded(node):
            if isinstance(node, EmbeddedObjectNode):
                return node
            if isinstance(node, DocumentNode):
                for c in node.children:
                    result = find_embedded(c)
                    if result:
                        return result
            return None

        obj1 = find_embedded(doc)
        obj2 = find_embedded(doc2)

        assert obj1.object_id == "img_001"
        assert obj1.object_type == "image"
        assert obj2.object_id == "img_001"
        assert obj2.object_type == "image"

    def test_drawing_round_trip(self):
        """Drawing placeholder survives round-trip."""
        original = "{^= drw_002 drawing}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        obj = doc2.children[0]
        assert isinstance(obj, EmbeddedObjectNode)
        assert obj.object_id == "drw_002"
        assert obj.object_type == "drawing"

    def test_chart_round_trip(self):
        """Chart placeholder survives round-trip."""
        original = "{^= cht_003 chart}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        obj = doc2.children[0]
        assert isinstance(obj, EmbeddedObjectNode)
        assert obj.object_type == "chart"

    def test_equation_round_trip(self):
        """Equation placeholder (no ID) survives round-trip."""
        original = "{^= equation}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        obj = doc2.children[0]
        assert isinstance(obj, EmbeddedObjectNode)
        assert obj.object_id is None
        assert obj.object_type == "equation"

    def test_video_round_trip(self):
        """Video placeholder survives round-trip."""
        original = "{^= vid_004 video}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        obj = doc2.children[0]
        assert isinstance(obj, EmbeddedObjectNode)
        assert obj.object_type == "video"


class TestRoundTripHeadingFormatting:
    """Tests for heading formatting preservation through round-trip.

    BUG: Currently headings lose their inline formatting (font, color, etc.)
    when writing to Google Docs because namedStyleType overwrites text styles.
    These tests verify that heading formatting survives MEBDF round-trip
    (parse→serialize→parse).
    """

    def setup_method(self):
        """Set up parser and serializer."""
        self.parser = MebdfParser()
        self.serializer = MebdfSerializer()

    def test_heading_with_bold_round_trip(self):
        """Heading with bold text survives MEBDF round-trip."""
        original = "# Normal and **bold** heading"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        # Both should have heading
        heading1 = doc.children[0]
        heading2 = doc2.children[0]
        assert isinstance(heading1, HeadingNode)
        assert isinstance(heading2, HeadingNode)

        # Both should have bold node in content
        def has_bold(content):
            return any(isinstance(n, BoldNode) for n in content)

        assert has_bold(heading1.content)
        assert has_bold(heading2.content)

    def test_heading_with_font_round_trip(self):
        """Heading with custom font survives MEBDF round-trip."""
        original = "# {!font:Roboto, weight:300}Light Font Heading{/!}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        heading1 = doc.children[0]
        heading2 = doc2.children[0]
        assert isinstance(heading1, HeadingNode)
        assert isinstance(heading2, HeadingNode)

        # Both should have FormattingNode with font property
        def get_font_props(content):
            for n in content:
                if isinstance(n, FormattingNode):
                    return n.properties
            return {}

        props1 = get_font_props(heading1.content)
        props2 = get_font_props(heading2.content)
        assert props1.get("font") == "Roboto"
        assert props2.get("font") == "Roboto"
        # Weight might be normalized to int
        assert int(props1.get("weight", 0)) == 300
        assert int(props2.get("weight", 0)) == 300

    def test_heading_with_color_round_trip(self):
        """Heading with text color survives MEBDF round-trip."""
        original = "## {!color:#ff0000}Red Heading{/!}"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        heading1 = doc.children[0]
        heading2 = doc2.children[0]
        assert isinstance(heading1, HeadingNode)
        assert isinstance(heading2, HeadingNode)

        # Both should have FormattingNode with color property
        def has_color(content):
            for n in content:
                if isinstance(n, FormattingNode) and "color" in n.properties:
                    return True
            return False

        assert has_color(heading1.content)
        assert has_color(heading2.content)

    def test_heading_with_mixed_formatting_round_trip(self):
        """Heading with multiple formatting types survives round-trip."""
        original = "# Normal **bold** *italic* {!underline}underlined{/!} text"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        heading1 = doc.children[0]
        heading2 = doc2.children[0]

        def count_formatting(content):
            bold = sum(1 for n in content if isinstance(n, BoldNode))
            italic = sum(1 for n in content if isinstance(n, ItalicNode))
            underline = sum(1 for n in content if isinstance(n, FormattingNode) and n.properties.get("underline"))
            return bold, italic, underline

        b1, i1, u1 = count_formatting(heading1.content)
        b2, i2, u2 = count_formatting(heading2.content)

        assert b1 == b2 == 1
        assert i1 == i2 == 1
        assert u1 == u2 == 1

    def test_heading_anchor_with_formatting_round_trip(self):
        """Heading with both anchor and formatting survives round-trip."""
        original = "# {^ h.test}**Bold Anchor Heading**"

        doc = self.parser.parse(original)
        output = self.serializer.serialize(doc)
        doc2 = self.parser.parse(output)

        heading1 = doc.children[0]
        heading2 = doc2.children[0]

        # Both should preserve anchor
        assert heading1.anchor_id == "h.test"
        assert heading2.anchor_id == "h.test"

        # Both should have bold content
        def has_bold(content):
            return any(isinstance(n, BoldNode) for n in content)

        assert has_bold(heading1.content)
        assert has_bold(heading2.content)


class TestRoundTripComplexDocument:
    """Tests for complex document round-trip."""

    def setup_method(self):
        """Set up parser and serializer."""
        self.parser = MebdfParser()
        self.serializer = MebdfSerializer()

    def test_full_document_round_trip(self):
        """Complex document survives round-trip."""
        original = """# {^ h.intro}Introduction

This is the **introduction** with *italic* text.

{^= img_001 image}

## {^ h.details}Details

{!highlight:yellow}Highlighted section.{/!}

Some {!underline}underlined{/!} content.

- Item one
- Item two
- Item three

### {^ h.sub}Subsection

Final {!mono}monospace{/!} code."""

        doc1 = self.parser.parse(original)
        output = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(output)

        # Compare structure
        assert len(doc1.children) == len(doc2.children)

        # Count headings
        headings1 = [c for c in doc1.children if isinstance(c, HeadingNode)]
        headings2 = [c for c in doc2.children if isinstance(c, HeadingNode)]
        assert len(headings1) == len(headings2)

        # Count embedded objects
        embeds1 = [c for c in doc1.children if isinstance(c, EmbeddedObjectNode)]
        embeds2 = [c for c in doc2.children if isinstance(c, EmbeddedObjectNode)]
        assert len(embeds1) == len(embeds2)

        # Count lists
        lists1 = [c for c in doc1.children if isinstance(c, ListNode)]
        lists2 = [c for c in doc2.children if isinstance(c, ListNode)]
        assert len(lists1) == len(lists2)

    def test_semantic_equivalence(self):
        """Verify semantic equivalence after round-trip."""
        original = """# {^ h.test}Test

**Bold** and *italic* and `code` content.

{!highlight:yellow, underline}Combined formatting.{/!}"""

        doc1 = self.parser.parse(original)
        output1 = self.serializer.serialize(doc1)
        doc2 = self.parser.parse(output1)
        output2 = self.serializer.serialize(doc2)

        # Two round-trips should produce identical output
        doc3 = self.parser.parse(output2)
        output3 = self.serializer.serialize(doc3)

        assert output2 == output3
