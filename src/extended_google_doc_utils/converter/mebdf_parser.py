"""MEBDF Parser - Markdown Extensions for Basic Doc Formatting.

This module implements parsing for MEBDF v1.4 syntax including:
- Standard markdown (headings, bold, italic, links, lists, code)
- Inline formatting: {!props}text{/!}
- Block formatting: {!props} (standalone line)
- Anchors: {^ id} and {^} (proposed)
- Embedded objects: {^= id type}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from extended_google_doc_utils.converter.exceptions import MebdfParseError

# =============================================================================
# Token Types
# =============================================================================


class TokenType(Enum):
    """Types of tokens in MEBDF."""

    TEXT = auto()
    HEADING = auto()
    BOLD = auto()
    ITALIC = auto()
    LINK = auto()
    LIST_ITEM = auto()
    CODE_SPAN = auto()
    CODE_BLOCK = auto()

    # MEBDF Extensions
    INLINE_FORMAT_START = auto()  # {!props}
    INLINE_FORMAT_END = auto()  # {/!}
    BLOCK_FORMAT = auto()  # {!props} standalone
    ANCHOR = auto()  # {^ id}
    PROPOSED_ANCHOR = auto()  # {^}
    EMBEDDED_OBJECT = auto()  # {^= id type}

    NEWLINE = auto()
    PARAGRAPH_BREAK = auto()
    EOF = auto()


@dataclass
class Token:
    """A lexical token from MEBDF content."""

    type: TokenType
    value: str
    line: int
    column: int
    properties: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# AST Nodes
# =============================================================================


@dataclass
class TextNode:
    """Plain text content."""

    content: str


@dataclass
class BoldNode:
    """Bold formatted text."""

    content: list


@dataclass
class ItalicNode:
    """Italic formatted text."""

    content: list


@dataclass
class CodeSpanNode:
    """Inline code."""

    content: str


@dataclass
class CodeBlockNode:
    """Fenced code block."""

    content: str
    language: str = ""


@dataclass
class HeadingNode:
    """Markdown heading with optional anchor."""

    level: int  # 1-6
    anchor_id: str | None  # From {^ id} if present
    content: list  # Child nodes (text, formatting, etc.)


@dataclass
class FormattingNode:
    """Inline formatting span - {!props}text{/!}."""

    properties: dict[str, str | bool]
    content: list  # Child nodes


@dataclass
class BlockFormattingNode:
    """Block-level formatting directive - {!props} standalone."""

    properties: dict[str, str | bool]


@dataclass
class AnchorNode:
    """Anchor marker - {^ id} or {^}."""

    anchor_id: str | None  # None for proposed anchors {^}


@dataclass
class EmbeddedObjectNode:
    """Embedded object placeholder - {^= id type}."""

    object_id: str | None  # None for equations
    object_type: str  # "image", "drawing", "chart", "equation", "video", "embed"


@dataclass
class LinkNode:
    """Markdown link [text](url)."""

    text: str
    url: str
    is_anchor_link: bool = False  # True if url references internal anchor


@dataclass
class ListNode:
    """List container."""

    ordered: bool
    items: list  # List of ListItemNode


@dataclass
class ListItemNode:
    """Single list item."""

    content: list  # Child nodes
    indent_level: int = 0


@dataclass
class ParagraphNode:
    """Paragraph container."""

    content: list  # Child nodes


@dataclass
class DocumentNode:
    """Root document node."""

    children: list = field(default_factory=list)


# =============================================================================
# Valid Properties
# =============================================================================

# Properties valid for {!...} inline syntax
INLINE_PROPERTIES = {
    "color",  # #hexcode
    "highlight",  # color name or #hex
    "font",  # font name
    "underline",  # boolean
    "mono",  # boolean
}

# Properties valid for {!...} block syntax (superset of inline)
BLOCK_PROPERTIES = INLINE_PROPERTIES | {
    "weight",  # Thin, Light, Normal, Bold, etc.
    "size",  # 12pt
    "align",  # left, center, right, justify
    "indent-left",  # 0.5in
    "indent-right",
    "first-line-indent",
    "hanging-indent",
    "line-spacing",  # single, 1.15, 1.5, double
    "space-before",  # 12pt
    "space-after",
}

# Valid embedded object types
EMBEDDED_OBJECT_TYPES = {"image", "drawing", "chart", "equation", "video", "embed"}


# =============================================================================
# Tokenizer
# =============================================================================


class Tokenizer:
    """Tokenize MEBDF content into tokens."""

    # Regex patterns for MEBDF syntax
    PATTERNS = {
        # MEBDF extensions (check first - more specific)
        "embedded_object": re.compile(
            r"\{\^=\s*(?:([a-zA-Z0-9_]+)\s+)?(\w+)\s*\}"
        ),  # {^= id type} or {^= type}
        "anchor": re.compile(r"\{\^\s+([a-zA-Z0-9_.]+)\}"),  # {^ id}
        "proposed_anchor": re.compile(r"\{\^\}"),  # {^}
        "inline_format_start": re.compile(
            r"\{!([^}]+)\}"
        ),  # {!props} (not at line start)
        "inline_format_end": re.compile(r"\{/!\}"),  # {/!}
        # Standard markdown
        "heading": re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE),
        "bold": re.compile(r"\*\*(.+?)\*\*"),
        "italic": re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"),
        "code_span": re.compile(r"`([^`]+)`"),
        "code_block_start": re.compile(r"^```(\w*)$", re.MULTILINE),
        "code_block_end": re.compile(r"^```$", re.MULTILINE),
        "link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
        "unordered_list": re.compile(r"^(\s*)[-*]\s+(.*)$", re.MULTILINE),
        "ordered_list": re.compile(r"^(\s*)\d+\.\s+(.*)$", re.MULTILINE),
    }

    def __init__(self, content: str):
        self.content = content
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """Tokenize the full content into tokens."""
        # For now, we'll use a simpler approach:
        # Return the content split by lines for block-level parsing
        lines = self.content.split("\n")
        for i, line in enumerate(lines):
            self.line = i + 1
            self._tokenize_line(line)
            if i < len(lines) - 1:
                self.tokens.append(
                    Token(TokenType.NEWLINE, "\n", self.line, len(line) + 1)
                )

        self.tokens.append(Token(TokenType.EOF, "", self.line, 0))
        return self.tokens

    def _tokenize_line(self, line: str) -> None:
        """Tokenize a single line."""
        stripped = line.strip()

        # Check for block-level formatting directive (standalone {!...})
        if stripped.startswith("{!") and stripped.endswith("}") and "{/!}" not in line:
            props = self._parse_properties(stripped[2:-1])
            self.tokens.append(
                Token(
                    TokenType.BLOCK_FORMAT,
                    stripped,
                    self.line,
                    1,
                    {"properties": props},
                )
            )
            return

        # Check for embedded object (standalone {^= ...})
        match = self.PATTERNS["embedded_object"].match(stripped)
        if match and match.group(0) == stripped:
            obj_id = match.group(1)  # May be None for equations
            obj_type = match.group(2)
            self.tokens.append(
                Token(
                    TokenType.EMBEDDED_OBJECT,
                    stripped,
                    self.line,
                    1,
                    {"object_id": obj_id, "object_type": obj_type},
                )
            )
            return

        # Check for heading
        heading_match = self.PATTERNS["heading"].match(line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2)
            self.tokens.append(
                Token(
                    TokenType.HEADING,
                    line,
                    self.line,
                    1,
                    {"level": level, "content": content},
                )
            )
            return

        # Check for list items
        ul_match = self.PATTERNS["unordered_list"].match(line)
        if ul_match:
            indent = len(ul_match.group(1))
            content = ul_match.group(2)
            self.tokens.append(
                Token(
                    TokenType.LIST_ITEM,
                    line,
                    self.line,
                    1,
                    {"ordered": False, "indent": indent // 2, "content": content},
                )
            )
            return

        ol_match = self.PATTERNS["ordered_list"].match(line)
        if ol_match:
            indent = len(ol_match.group(1))
            content = ol_match.group(2)
            self.tokens.append(
                Token(
                    TokenType.LIST_ITEM,
                    line,
                    self.line,
                    1,
                    {"ordered": True, "indent": indent // 2, "content": content},
                )
            )
            return

        # Default: treat as text content
        if stripped:
            self.tokens.append(Token(TokenType.TEXT, line, self.line, 1))
        else:
            self.tokens.append(Token(TokenType.PARAGRAPH_BREAK, "", self.line, 1))

    def _parse_properties(self, props_str: str) -> dict[str, str | bool]:
        """Parse property string like 'highlight:yellow, underline'."""
        properties: dict[str, str | bool] = {}
        parts = [p.strip() for p in props_str.split(",")]

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Handle boolean false values
                if value.lower() == "false":
                    properties[key] = False
                else:
                    properties[key] = value
            else:
                # Boolean property (presence = true)
                properties[part] = True

        return properties


# =============================================================================
# Inline Parser
# =============================================================================


class InlineParser:
    """Parse inline content (text with inline formatting, anchors, links, etc.)."""

    # Patterns for inline elements (order matters!)
    INLINE_PATTERNS = [
        # MEBDF extensions first
        ("embedded_object", re.compile(r"\{\^=\s*(?:([a-zA-Z0-9_]+)\s+)?(\w+)\s*\}")),
        ("anchor", re.compile(r"\{\^\s+([a-zA-Z0-9_.]+)\}")),
        ("proposed_anchor", re.compile(r"\{\^\}")),
        ("inline_format", re.compile(r"\{!([^}]+)\}(.*?)\{/!\}", re.DOTALL)),
        # Standard markdown
        ("code_span", re.compile(r"`([^`]+)`")),
        ("bold", re.compile(r"\*\*(.+?)\*\*")),
        ("italic", re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")),
        ("link", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
    ]

    def parse(self, content: str, line: int = 1) -> list:
        """Parse inline content into AST nodes."""
        if not content:
            return []

        nodes: list = []
        pos = 0

        while pos < len(content):
            # Find the earliest matching pattern
            earliest_match = None
            earliest_pos = len(content)
            pattern_name = None

            for name, pattern in self.INLINE_PATTERNS:
                match = pattern.search(content, pos)
                if match and match.start() < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start()
                    pattern_name = name

            if earliest_match is None:
                # No more patterns - rest is plain text
                if pos < len(content):
                    nodes.append(TextNode(content[pos:]))
                break

            # Add text before the match
            if earliest_pos > pos:
                nodes.append(TextNode(content[pos:earliest_pos]))

            # Process the match
            node = self._process_match(pattern_name, earliest_match, line)
            if node:
                nodes.append(node)

            pos = earliest_match.end()

        return nodes

    def _process_match(self, pattern_name: str, match: re.Match, line: int) -> Any:
        """Process a regex match into an AST node."""
        if pattern_name == "bold":
            inner_content = match.group(1)
            return BoldNode(content=self.parse(inner_content, line))

        elif pattern_name == "italic":
            inner_content = match.group(1)
            return ItalicNode(content=self.parse(inner_content, line))

        elif pattern_name == "code_span":
            return CodeSpanNode(content=match.group(1))

        elif pattern_name == "link":
            text = match.group(1)
            url = match.group(2)
            is_anchor = url.startswith("#^")
            return LinkNode(text=text, url=url, is_anchor_link=is_anchor)

        elif pattern_name == "anchor":
            anchor_id = match.group(1)
            return AnchorNode(anchor_id=anchor_id)

        elif pattern_name == "proposed_anchor":
            return AnchorNode(anchor_id=None)

        elif pattern_name == "embedded_object":
            obj_id = match.group(1)  # May be None
            obj_type = match.group(2)
            if obj_type not in EMBEDDED_OBJECT_TYPES:
                raise MebdfParseError(
                    f"Unknown embedded object type: {obj_type}", line
                )
            return EmbeddedObjectNode(object_id=obj_id, object_type=obj_type)

        elif pattern_name == "inline_format":
            props_str = match.group(1)
            inner_content = match.group(2)
            properties = self._parse_properties(props_str)
            return FormattingNode(
                properties=properties, content=self.parse(inner_content, line)
            )

        return None

    def _parse_properties(self, props_str: str) -> dict[str, str | bool]:
        """Parse property string like 'highlight:yellow, underline'."""
        properties: dict[str, str | bool] = {}
        parts = [p.strip() for p in props_str.split(",")]

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value.lower() == "false":
                    properties[key] = False
                else:
                    properties[key] = value
            else:
                properties[part] = True

        return properties


# =============================================================================
# Block Parser
# =============================================================================


class BlockParser:
    """Parse block-level content (paragraphs, headings, lists, code blocks)."""

    def __init__(self):
        self.inline_parser = InlineParser()
        self.block_formatting_state: dict[str, str | bool] = {}

    def parse(self, tokens: list[Token]) -> list:
        """Parse tokens into block-level AST nodes."""
        nodes: list = []
        i = 0
        current_paragraph: list = []
        in_code_block = False
        code_block_content: list[str] = []
        code_block_lang = ""

        while i < len(tokens):
            token = tokens[i]

            # Handle code blocks
            if token.type == TokenType.TEXT:
                line = token.value.strip()
                if line.startswith("```") and not in_code_block:
                    # Flush current paragraph
                    if current_paragraph:
                        nodes.append(self._make_paragraph(current_paragraph))
                        current_paragraph = []
                    in_code_block = True
                    code_block_lang = line[3:].strip()
                    i += 1
                    continue
                elif line == "```" and in_code_block:
                    nodes.append(
                        CodeBlockNode(
                            content="\n".join(code_block_content), language=code_block_lang
                        )
                    )
                    in_code_block = False
                    code_block_content = []
                    code_block_lang = ""
                    i += 1
                    continue

            if in_code_block:
                code_block_content.append(token.value if token.type == TokenType.TEXT else "")
                i += 1
                continue

            if token.type == TokenType.EOF:
                break

            elif token.type == TokenType.HEADING:
                # Flush current paragraph
                if current_paragraph:
                    nodes.append(self._make_paragraph(current_paragraph))
                    current_paragraph = []

                level = token.properties["level"]
                content_str = token.properties["content"]

                # Check for anchor in heading content
                anchor_id = None
                anchor_match = re.match(r"\{\^\s+([a-zA-Z0-9_.]+)\}(.*)$", content_str)
                if anchor_match:
                    anchor_id = anchor_match.group(1)
                    content_str = anchor_match.group(2).strip()

                heading_content = self.inline_parser.parse(content_str, token.line)
                nodes.append(
                    HeadingNode(level=level, anchor_id=anchor_id, content=heading_content)
                )

            elif token.type == TokenType.BLOCK_FORMAT:
                # Flush current paragraph
                if current_paragraph:
                    nodes.append(self._make_paragraph(current_paragraph))
                    current_paragraph = []

                properties = token.properties.get("properties", {})
                # Update block formatting state
                for key, value in properties.items():
                    if value is False:
                        self.block_formatting_state.pop(key, None)
                    else:
                        self.block_formatting_state[key] = value

                nodes.append(BlockFormattingNode(properties=properties))

            elif token.type == TokenType.EMBEDDED_OBJECT:
                # Flush current paragraph
                if current_paragraph:
                    nodes.append(self._make_paragraph(current_paragraph))
                    current_paragraph = []

                obj_id = token.properties.get("object_id")
                obj_type = token.properties.get("object_type", "embed")
                nodes.append(EmbeddedObjectNode(object_id=obj_id, object_type=obj_type))

            elif token.type == TokenType.LIST_ITEM:
                # Flush current paragraph
                if current_paragraph:
                    nodes.append(self._make_paragraph(current_paragraph))
                    current_paragraph = []

                # Collect consecutive list items
                list_items: list[ListItemNode] = []
                is_ordered = token.properties.get("ordered", False)

                while i < len(tokens) and tokens[i].type == TokenType.LIST_ITEM:
                    item_token = tokens[i]
                    content_str = item_token.properties.get("content", "")
                    indent = item_token.properties.get("indent", 0)
                    item_content = self.inline_parser.parse(content_str, item_token.line)
                    list_items.append(
                        ListItemNode(content=item_content, indent_level=indent)
                    )
                    i += 1
                    # Skip newline after list item
                    if i < len(tokens) and tokens[i].type == TokenType.NEWLINE:
                        i += 1

                nodes.append(ListNode(ordered=is_ordered, items=list_items))
                continue  # Already advanced i

            elif token.type == TokenType.TEXT:
                # Add to current paragraph
                inline_nodes = self.inline_parser.parse(token.value, token.line)
                current_paragraph.extend(inline_nodes)

            elif token.type == TokenType.PARAGRAPH_BREAK:
                # Flush current paragraph
                if current_paragraph:
                    nodes.append(self._make_paragraph(current_paragraph))
                    current_paragraph = []

            elif token.type == TokenType.NEWLINE:
                # Single newline - add space to paragraph
                if current_paragraph:
                    # Don't add trailing whitespace
                    pass

            i += 1

        # Flush any remaining paragraph
        if current_paragraph:
            nodes.append(self._make_paragraph(current_paragraph))

        return nodes

    def _make_paragraph(self, content: list) -> ParagraphNode:
        """Create a paragraph node, merging adjacent text nodes."""
        # Merge adjacent TextNodes
        merged: list = []
        for node in content:
            if isinstance(node, TextNode) and merged and isinstance(merged[-1], TextNode):
                merged[-1] = TextNode(merged[-1].content + node.content)
            else:
                merged.append(node)
        return ParagraphNode(content=merged)


# =============================================================================
# Document Parser (Main Entry Point)
# =============================================================================


class MebdfParser:
    """Main parser for MEBDF documents.

    Combines tokenization, block parsing, and inline parsing to produce
    a complete AST from MEBDF content.
    """

    def __init__(self):
        self.inline_parser = InlineParser()

    def parse(self, content: str) -> DocumentNode:
        """Parse MEBDF content into an AST.

        Args:
            content: MEBDF markdown string.

        Returns:
            DocumentNode representing the parsed content.

        Raises:
            MebdfParseError: If content contains invalid syntax.
        """
        tokenizer = Tokenizer(content)
        tokens = tokenizer.tokenize()

        block_parser = BlockParser()
        children = block_parser.parse(tokens)

        return DocumentNode(children=children)

    def parse_inline(self, content: str) -> list:
        """Parse inline content (text with inline formatting).

        Useful for parsing just the content of a heading or paragraph
        without block-level structure.

        Args:
            content: Inline MEBDF content.

        Returns:
            List of AST nodes.
        """
        return self.inline_parser.parse(content)
