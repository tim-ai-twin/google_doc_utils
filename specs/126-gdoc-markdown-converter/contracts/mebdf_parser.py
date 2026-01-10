"""MEBDF Parser Contract.

Defines the interface for parsing MEBDF (Markdown Extensions for Basic Doc Formatting).
Supports MEBDF v1.4 syntax including:
- Inline formatting: {!props}text{/!}
- Block formatting: {!props} (standalone line)
- Anchors: {^ id} and {^} (proposed)
- Embedded objects: {^= id type}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


# =============================================================================
# Token Types
# =============================================================================


class TokenType(Enum):
    """Types of tokens in MEBDF."""

    TEXT = "text"                    # Plain text
    HEADING = "heading"              # Markdown heading (# through ######)
    BOLD = "bold"                    # **text**
    ITALIC = "italic"                # *text*
    LINK = "link"                    # [text](url)
    LIST_ITEM = "list_item"          # - item or 1. item
    CODE_SPAN = "code_span"          # `code`
    CODE_BLOCK = "code_block"        # ```code```

    # MEBDF Extensions
    INLINE_FORMAT = "inline_format"  # {!props}text{/!}
    BLOCK_FORMAT = "block_format"    # {!props} standalone
    ANCHOR = "anchor"                # {^ id}
    PROPOSED_ANCHOR = "proposed_anchor"  # {^}
    EMBEDDED_OBJECT = "embedded_object"  # {^= id type}

    NEWLINE = "newline"
    EOF = "eof"


# =============================================================================
# AST Nodes
# =============================================================================


@dataclass
class TextNode:
    """Plain text content."""

    content: str


@dataclass
class HeadingNode:
    """Markdown heading."""

    level: int  # 1-6
    anchor_id: str | None  # From {^ id} if present
    content: list  # Child nodes (text, formatting, etc.)


@dataclass
class FormattingNode:
    """Inline formatting span."""

    properties: dict[str, str | bool]  # e.g., {"highlight": "yellow", "underline": True}
    content: list  # Child nodes


@dataclass
class BlockFormattingNode:
    """Block-level formatting directive."""

    properties: dict[str, str | bool]


@dataclass
class AnchorNode:
    """Anchor marker."""

    anchor_id: str | None  # None for proposed anchors {^}


@dataclass
class EmbeddedObjectNode:
    """Embedded object placeholder."""

    object_id: str | None  # None for equations
    object_type: str  # "image", "drawing", "chart", "equation", "video", "embed"


@dataclass
class LinkNode:
    """Markdown link."""

    text: str
    url: str
    is_anchor_link: bool = False  # True if url starts with #^


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
# Parser Protocol
# =============================================================================


class MebdfParser(Protocol):
    """Protocol for MEBDF parsing."""

    def parse(self, content: str) -> DocumentNode:
        """Parse MEBDF content into an AST.

        Args:
            content: MEBDF markdown string.

        Returns:
            DocumentNode representing the parsed content.

        Raises:
            MebdfParseError: If content contains invalid syntax.
        """
        ...

    def parse_inline(self, content: str) -> list:
        """Parse inline content (text with inline formatting).

        Useful for parsing just the content of a heading or paragraph.

        Args:
            content: Inline MEBDF content.

        Returns:
            List of AST nodes.
        """
        ...


# =============================================================================
# Serializer Protocol
# =============================================================================


class MebdfSerializer(Protocol):
    """Protocol for MEBDF serialization (AST → string)."""

    def serialize(self, document: DocumentNode) -> str:
        """Serialize AST back to MEBDF string.

        Args:
            document: Root document node.

        Returns:
            MEBDF markdown string.
        """
        ...


# =============================================================================
# Formatting Property Definitions
# =============================================================================

# Valid properties for {!...} syntax
INLINE_PROPERTIES = {
    # Value properties (require a value)
    "color": str,        # #hexcode
    "highlight": str,    # color name or #hex
    "font": str,         # font name

    # Boolean properties (no value = true)
    "underline": bool,
    "mono": bool,
}

BLOCK_PROPERTIES = {
    **INLINE_PROPERTIES,
    "weight": str,       # Thin, Light, Normal, Bold, etc.
    "size": str,         # 12pt
    "align": str,        # left, center, right, justify
    "indent-left": str,  # 0.5in
    "indent-right": str,
    "first-line-indent": str,
    "hanging-indent": str,
    "line-spacing": str,  # single, 1.15, 1.5, double
    "space-before": str,  # 12pt
    "space-after": str,
}

# Valid embedded object types
EMBEDDED_OBJECT_TYPES = {"image", "drawing", "chart", "equation", "video", "embed"}
