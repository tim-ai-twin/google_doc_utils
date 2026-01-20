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


# =============================================================================
# Style Transfer Types (Feature 130)
# =============================================================================


class NamedStyleType(str, Enum):
    """The 9 Google Docs named style types."""

    NORMAL_TEXT = "NORMAL_TEXT"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"


class StyleSource(str, Enum):
    """Indicates where an effective style was derived from."""

    PARAGRAPH_SAMPLE = "paragraph_sample"  # From actual paragraph in document
    STYLE_DEFINITION = "style_definition"  # Fallback to named style definition


@dataclass(frozen=True)
class RGBColor:
    """RGB color with values 0.0-1.0.

    Attributes:
        red: Red component (0.0-1.0).
        green: Green component (0.0-1.0).
        blue: Blue component (0.0-1.0).
    """

    red: float
    green: float
    blue: float

    def __post_init__(self) -> None:
        """Validate color values are in range."""
        for name, value in [("red", self.red), ("green", self.green), ("blue", self.blue)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}")

    def to_hex(self) -> str:
        """Convert to hex string like '#ff0000'."""
        r = int(self.red * 255)
        g = int(self.green * 255)
        b = int(self.blue * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> "RGBColor":
        """Parse hex string like '#FF0000' or 'FF0000'."""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        r = int(hex_str[0:2], 16) / 255
        g = int(hex_str[2:4], 16) / 255
        b = int(hex_str[4:6], 16) / 255
        return cls(red=r, green=g, blue=b)


@dataclass(frozen=True)
class TextStyleProperties:
    """Text-level style properties for a named style (FR-012).

    Attributes:
        font_family: Font family name (e.g., "Arial", "Roboto").
        font_size_pt: Font size in points.
        font_weight: Font weight 100-900 (400=normal, 700=bold).
        text_color: Text foreground color.
        highlight_color: Text background/highlight color.
        bold: Whether text is bold.
        italic: Whether text is italic.
        underline: Whether text is underlined.
    """

    font_family: str | None = None
    font_size_pt: float | None = None
    font_weight: int | None = None
    text_color: RGBColor | None = None
    highlight_color: RGBColor | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None


@dataclass(frozen=True)
class ParagraphStyleProperties:
    """Paragraph-level style properties for a named style (FR-013).

    Attributes:
        alignment: Text alignment (START, CENTER, END, JUSTIFIED).
        line_spacing: Line height multiplier (1.0 = single, 1.5 = 1.5x).
        space_before_pt: Space before paragraph in points.
        space_after_pt: Space after paragraph in points.
        indent_start_pt: Left indent in points (LTR).
        indent_end_pt: Right indent in points (LTR).
        first_line_indent_pt: First line indent in points.
    """

    alignment: str | None = None
    line_spacing: float | None = None
    space_before_pt: float | None = None
    space_after_pt: float | None = None
    indent_start_pt: float | None = None
    indent_end_pt: float | None = None
    first_line_indent_pt: float | None = None


@dataclass(frozen=True)
class EffectiveStyle:
    """Effective (visible) style for a named style type.

    Captures what the user actually sees, not just the style definition.
    If paragraphs have consistent overrides, those overrides are captured.

    Attributes:
        style_type: The named style type this represents.
        text_style: Character-level formatting properties.
        paragraph_style: Block-level formatting properties.
        source: Where this style came from (paragraph or definition).
    """

    style_type: NamedStyleType
    text_style: TextStyleProperties
    paragraph_style: ParagraphStyleProperties
    source: StyleSource


@dataclass(frozen=True)
class DocumentProperties:
    """Document-level properties (page settings).

    Attributes:
        background_color: Document background color.
        margin_top_pt: Top margin in points.
        margin_bottom_pt: Bottom margin in points.
        margin_left_pt: Left margin in points.
        margin_right_pt: Right margin in points.
        page_width_pt: Page width in points.
        page_height_pt: Page height in points.
    """

    background_color: RGBColor | None = None
    margin_top_pt: float | None = None
    margin_bottom_pt: float | None = None
    margin_left_pt: float | None = None
    margin_right_pt: float | None = None
    page_width_pt: float | None = None
    page_height_pt: float | None = None


@dataclass(frozen=True)
class DocumentStyles:
    """Complete style information for a document.

    Contains document-level properties and effective styles for all 9
    named style types.

    Attributes:
        document_id: The Google Doc ID.
        document_properties: Page-level settings.
        effective_styles: Dict of style type to effective style.
    """

    document_id: str
    document_properties: DocumentProperties
    effective_styles: dict[NamedStyleType, EffectiveStyle]

    def get_style(self, style_type: NamedStyleType) -> EffectiveStyle | None:
        """Get effective style for a specific type."""
        return self.effective_styles.get(style_type)


@dataclass(frozen=True)
class StyleTransferOptions:
    """Options controlling what gets transferred.

    Attributes:
        include_document_properties: Whether to transfer doc-level properties.
        include_effective_styles: Whether to transfer named styles.
        style_types: Which styles to transfer. None = all 9 types.
    """

    include_document_properties: bool = True
    include_effective_styles: bool = True
    style_types: list[NamedStyleType] | None = None


@dataclass(frozen=True)
class StyleApplicationResult:
    """Result of applying one style type to target document.

    Attributes:
        style_type: The style type that was applied.
        paragraphs_updated: Number of paragraphs updated.
        success: Whether the operation succeeded.
        error: Error message if failed.
    """

    style_type: NamedStyleType
    paragraphs_updated: int
    success: bool = True
    error: str | None = None


@dataclass
class StyleTransferResult:
    """Result of a style transfer operation.

    Attributes:
        success: Whether all operations completed.
        document_properties_applied: Whether doc properties were updated.
        styles_applied: Dict of style type to application result.
        total_paragraphs_updated: Sum of all paragraph updates.
        errors: List of any error messages.
    """

    success: bool
    document_properties_applied: bool
    styles_applied: dict[NamedStyleType, StyleApplicationResult] = field(
        default_factory=dict
    )
    total_paragraphs_updated: int = 0
    errors: list[str] = field(default_factory=list)
