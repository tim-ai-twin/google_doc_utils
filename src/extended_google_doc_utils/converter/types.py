"""Data types for Google Docs to Markdown Converter.

This module defines the core data classes and enums used throughout
the converter package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EmbeddedObjectType(Enum):
    """Types of embedded objects in Google Docs."""

    IMAGE = "image"
    DRAWING = "drawing"
    CHART = "chart"
    EQUATION = "equation"
    VIDEO = "video"
    EMBED = "embed"  # Generic/unknown


class AnchorType(Enum):
    """Types of anchors in a document."""

    HEADING = "heading"  # From paragraphStyle.headingId
    BOOKMARK = "bookmark"  # From namedRanges or bookmarks
    COMMENT = "comment"  # From comment anchors


@dataclass(frozen=True)
class TabReference:
    """Reference to a specific tab in a Google Doc.

    Attributes:
        document_id: The Google Doc ID (from document URL).
        tab_id: The tab ID. Empty string for single-tab documents.
    """

    document_id: str
    tab_id: str = ""

    def __post_init__(self) -> None:
        """Validate that document_id is provided."""
        if not self.document_id:
            raise ValueError("document_id is required")


@dataclass(frozen=True)
class HeadingAnchor:
    """A heading in the document hierarchy.

    Attributes:
        anchor_id: Google Docs headingId (e.g., "h.abc123").
        level: Heading level 1-6.
        text: The heading text content.
        start_index: Character position in document.
    """

    anchor_id: str
    level: int
    text: str
    start_index: int = 0


@dataclass
class Section:
    """A portion of a document from one heading to the next.

    Section boundaries are determined by heading levels:
    - Preamble: index 0 to first heading's start_index
    - Section: heading start_index to next same-or-higher heading's start_index
    - Last section: heading start_index to document end

    Attributes:
        anchor_id: Heading anchor ID (empty = preamble).
        level: Heading level (0 = preamble).
        start_index: Start character index (inclusive).
        end_index: End character index (exclusive).
    """

    anchor_id: str
    level: int
    start_index: int
    end_index: int

    @property
    def is_preamble(self) -> bool:
        """Check if this section is the preamble (content before first heading)."""
        return self.anchor_id == ""


@dataclass
class EmbeddedObject:
    """An opaque object preserved through conversion.

    Attributes:
        object_id: Object ID (None for equations which have no ID).
        object_type: Type of embedded object.
        start_index: Position in document.
    """

    object_id: str | None
    object_type: EmbeddedObjectType
    start_index: int


@dataclass
class Anchor:
    """A position marker for comments, bookmarks, or headings.

    Attributes:
        anchor_id: Unique identifier.
        anchor_type: Type of anchor (heading, bookmark, comment).
        start_index: Position in document.
    """

    anchor_id: str
    anchor_type: AnchorType
    start_index: int


@dataclass
class TextFormatting:
    """Text formatting properties.

    Attributes:
        bold: Whether text is bold.
        italic: Whether text is italic.
        underline: Whether text is underlined.
        strikethrough: Whether text has strikethrough (not supported in MEBDF).
        highlight_color: Highlight color (e.g., "yellow" or "#ffff00").
        text_color: Text color (e.g., "#cc0000").
        font_family: Font family name (e.g., "Roboto Mono").
        is_monospace: Whether text should be monospace.
    """

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    highlight_color: str | None = None
    text_color: str | None = None
    font_family: str | None = None
    is_monospace: bool = False


@dataclass
class FormattingSpan:
    """A contiguous span with uniform formatting.

    Attributes:
        start_index: Start position.
        end_index: End position.
        formatting: The formatting applied to this span.
    """

    start_index: int
    end_index: int
    formatting: TextFormatting


@dataclass
class BlockFormatting:
    """Paragraph-level formatting state.

    Attributes:
        named_style: Style name (e.g., "Normal text", "Heading 1").
        font_family: Font family name.
        font_weight: Font weight (e.g., "Light", "Bold").
        font_size: Font size (e.g., "12pt").
        text_color: Text color.
        alignment: Text alignment ("left", "center", "right", "justify").
        indent_left: Left indentation (e.g., "0.5in").
        indent_right: Right indentation.
        line_spacing: Line spacing ("single", "1.5", "double").
        space_before: Space before paragraph (e.g., "12pt").
        space_after: Space after paragraph.
    """

    named_style: str | None = None
    font_family: str | None = None
    font_weight: str | None = None
    font_size: str | None = None
    text_color: str | None = None
    alignment: str | None = None
    indent_left: str | None = None
    indent_right: str | None = None
    line_spacing: str | None = None
    space_before: str | None = None
    space_after: str | None = None


@dataclass
class HierarchyResult:
    """Result of tab hierarchy extraction.

    Attributes:
        headings: List of headings with their anchors.
        markdown: Pure markdown representation (# lines with anchors).
    """

    headings: list[HeadingAnchor] = field(default_factory=list)
    markdown: str = ""


@dataclass
class ExportResult:
    """Result of exporting Google Doc to MEBDF.

    Attributes:
        content: The MEBDF markdown content.
        anchors: All anchors found in the content.
        embedded_objects: Objects that were preserved as placeholders.
        warnings: List of non-fatal warnings (e.g., unsupported formatting).
    """

    content: str
    anchors: list[Anchor] = field(default_factory=list)
    embedded_objects: list[EmbeddedObject] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportResult:
    """Result of importing MEBDF to Google Doc.

    Attributes:
        success: Whether the import completed successfully.
        requests: Google Docs API batchUpdate requests generated.
        preserved_objects: Object IDs that were preserved.
        warnings: List of non-fatal warnings.
    """

    success: bool
    requests: list[dict] = field(default_factory=list)
    preserved_objects: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
