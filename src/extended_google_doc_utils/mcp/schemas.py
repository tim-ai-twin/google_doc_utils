"""Response dataclasses for MCP tools.

These dataclasses define the structured responses returned by all MCP tools,
ensuring consistent typing and serialization for LLM consumption.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# =============================================================================
# Navigation Tool Responses
# =============================================================================


@dataclass
class DocumentSummary:
    """Summary information about a Google Doc.

    Attributes:
        document_id: Google Doc ID (from document URL).
        title: Document title.
        last_modified: ISO 8601 timestamp of last modification.
        owner: Owner's email address.
    """

    document_id: str
    title: str
    last_modified: str
    owner: str


@dataclass
class ListDocumentsResponse:
    """Response from list_documents tool.

    Attributes:
        success: Whether the operation succeeded.
        documents: List of document summaries.
        total_count: Total matching documents (may exceed returned limit).
    """

    success: bool
    documents: list[DocumentSummary] = field(default_factory=list)
    total_count: int = 0


@dataclass
class TabInfo:
    """Information about a tab within a document.

    Attributes:
        tab_id: Tab identifier for use in other tools.
        title: Tab title.
        index: Tab position (0-based).
    """

    tab_id: str
    title: str
    index: int


@dataclass
class DocumentMetadata:
    """Response from get_metadata tool.

    Attributes:
        success: Whether the operation succeeded.
        document_id: Google Doc ID.
        title: Document title.
        tabs: List of tabs in the document.
        can_edit: Whether user has edit permission.
        can_comment: Whether user has comment permission.
    """

    success: bool
    document_id: str = ""
    title: str = ""
    tabs: list[TabInfo] = field(default_factory=list)
    can_edit: bool = False
    can_comment: bool = False


@dataclass
class HeadingInfo:
    """Information about a heading in the document hierarchy.

    Attributes:
        anchor_id: Heading anchor ID for use in section operations.
        level: Heading level (1-6 for H1-H6).
        text: Heading text content.
    """

    anchor_id: str
    level: int
    text: str


@dataclass
class HierarchyResponse:
    """Response from get_hierarchy tool.

    Attributes:
        success: Whether the operation succeeded.
        headings: List of headings with their anchors.
        markdown: Pure markdown representation of hierarchy.
    """

    success: bool
    headings: list[HeadingInfo] = field(default_factory=list)
    markdown: str = ""


# =============================================================================
# Section Tool Responses
# =============================================================================


@dataclass
class ExportSectionResponse:
    """Response from export_section tool.

    Attributes:
        success: Whether the operation succeeded.
        content: MEBDF markdown content of the section.
        anchor_id: Echo back the requested anchor ID.
        warnings: List of non-fatal issues encountered.
    """

    success: bool
    content: str = ""
    anchor_id: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportSectionResponse:
    """Response from import_section tool.

    Attributes:
        success: Whether the operation succeeded.
        anchor_id: Echo back the target anchor ID.
        preserved_objects: List of embedded object IDs that were preserved.
        warnings: List of non-fatal issues encountered.
    """

    success: bool
    anchor_id: str = ""
    preserved_objects: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# Tab Tool Responses
# =============================================================================


@dataclass
class ExportTabResponse:
    """Response from export_tab tool.

    Attributes:
        success: Whether the operation succeeded.
        content: Full MEBDF markdown content.
        tab_id: Echo back the resolved tab ID.
        warnings: List of non-fatal issues encountered.
    """

    success: bool
    content: str = ""
    tab_id: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportTabResponse:
    """Response from import_tab tool.

    Attributes:
        success: Whether the operation succeeded.
        tab_id: Echo back the target tab ID.
        preserved_objects: List of embedded object IDs that were preserved.
        warnings: List of non-fatal issues encountered.
    """

    success: bool
    tab_id: str = ""
    preserved_objects: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# Formatting Tool Responses
# =============================================================================


@dataclass
class NormalizeFormattingResponse:
    """Response from normalize_formatting tool.

    Attributes:
        success: Whether the operation succeeded.
        changes_made: Number of formatting changes applied.
        warnings: List of non-fatal issues (e.g., unsupported formatting preserved).
    """

    success: bool
    changes_made: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class StyleDefinition:
    """A formatting style definition for a document element type.

    Attributes:
        element_type: Type of element ("body", "heading1", "heading2", etc.).
        font_family: Font family name.
        font_size: Font size (e.g., "11pt").
        font_weight: Font weight (e.g., "bold", "normal").
        text_color: Text color (e.g., "#000000").
        line_spacing: Line spacing ("single", "1.5", "double").
        space_before: Space before paragraph (e.g., "6pt").
        space_after: Space after paragraph (e.g., "6pt").
    """

    element_type: str
    font_family: str | None = None
    font_size: str | None = None
    font_weight: str | None = None
    text_color: str | None = None
    line_spacing: str | None = None
    space_before: str | None = None
    space_after: str | None = None


@dataclass
class ExtractStylesResponse:
    """Response from extract_styles tool.

    Attributes:
        success: Whether the operation succeeded.
        styles: List of style definitions extracted from the document.
        source_document_id: ID of the source document.
    """

    success: bool
    styles: list[StyleDefinition] = field(default_factory=list)
    source_document_id: str = ""


@dataclass
class ApplyStylesResponse:
    """Response from apply_styles tool.

    Attributes:
        success: Whether the operation succeeded.
        changes_made: Number of formatting changes applied.
        warnings: List of non-fatal issues encountered.
    """

    success: bool
    changes_made: int = 0
    warnings: list[str] = field(default_factory=list)
