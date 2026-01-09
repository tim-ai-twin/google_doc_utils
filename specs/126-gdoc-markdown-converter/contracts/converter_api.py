"""API Contracts for Google Docs to Markdown Converter.

This module defines the public interface for the converter library.
These are contract definitions - actual implementation will follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


# =============================================================================
# Enums
# =============================================================================


class EmbeddedObjectType(Enum):
    """Types of embedded objects in Google Docs."""

    IMAGE = "image"
    DRAWING = "drawing"
    CHART = "chart"
    EQUATION = "equation"
    VIDEO = "video"
    EMBED = "embed"  # Generic/unknown


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(frozen=True)
class TabReference:
    """Reference to a specific tab in a Google Doc.

    Attributes:
        document_id: The Google Doc ID (from document URL).
        tab_id: The tab ID. Empty string for single-tab documents.
    """

    document_id: str
    tab_id: str = ""


@dataclass(frozen=True)
class HeadingAnchor:
    """A heading in the document hierarchy.

    Attributes:
        anchor_id: Google Docs headingId (e.g., "h.abc123").
        level: Heading level 1-6.
        text: The heading text content.
    """

    anchor_id: str
    level: int
    text: str


@dataclass
class HierarchyResult:
    """Result of tab hierarchy extraction.

    Attributes:
        headings: List of headings with their anchors.
        markdown: Pure markdown representation (# lines with anchors).
    """

    headings: list[HeadingAnchor]
    markdown: str


@dataclass
class ExportResult:
    """Result of exporting Google Doc to MEBDF.

    Attributes:
        content: The MEBDF markdown content.
        warnings: List of non-fatal warnings (e.g., unsupported formatting).
    """

    content: str
    warnings: list[str]


@dataclass
class ImportResult:
    """Result of importing MEBDF to Google Doc.

    Attributes:
        success: Whether the import completed successfully.
        warnings: List of non-fatal warnings.
    """

    success: bool
    warnings: list[str]


# =============================================================================
# Exceptions
# =============================================================================


class ConverterError(Exception):
    """Base exception for converter errors."""

    pass


class MultipleTabsError(ConverterError):
    """Raised when tab_id is required but not provided."""

    def __init__(self, tab_count: int):
        self.tab_count = tab_count
        super().__init__(
            f"Document has {tab_count} tabs. Specify tab_id to select one."
        )


class AnchorNotFoundError(ConverterError):
    """Raised when a section anchor ID doesn't exist."""

    def __init__(self, anchor_id: str):
        self.anchor_id = anchor_id
        super().__init__(
            f"Anchor '{anchor_id}' not found. The heading may have been "
            "deleted or modified. Re-fetch the hierarchy to get current anchors."
        )


class EmbeddedObjectNotFoundError(ConverterError):
    """Raised when an embedded object placeholder references a missing object."""

    def __init__(self, object_id: str, object_type: str):
        self.object_id = object_id
        self.object_type = object_type
        super().__init__(
            f"Embedded {object_type} with ID '{object_id}' not found in document. "
            "Embedded objects cannot be created via placeholder."
        )


class MebdfParseError(ConverterError):
    """Raised when MEBDF content cannot be parsed."""

    def __init__(self, message: str, line: int | None = None):
        self.line = line
        prefix = f"Line {line}: " if line else ""
        super().__init__(f"MEBDF parse error: {prefix}{message}")


# =============================================================================
# Converter Protocol
# =============================================================================


class GoogleDocsConverter(Protocol):
    """Protocol defining the converter interface.

    This is the main public API for the converter library.
    """

    # -------------------------------------------------------------------------
    # Hierarchy Operations
    # -------------------------------------------------------------------------

    def get_hierarchy(self, tab: TabReference) -> HierarchyResult:
        """Get the heading hierarchy of a tab.

        Returns only headings as pure markdown with anchor IDs.
        Format: `## {^ anchor_id}Heading Text`

        Args:
            tab: Reference to the document tab.

        Returns:
            HierarchyResult with headings and markdown representation.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
        """
        ...

    # -------------------------------------------------------------------------
    # Export Operations (Google Docs → MEBDF)
    # -------------------------------------------------------------------------

    def export_tab(self, tab: TabReference) -> ExportResult:
        """Export entire tab to MEBDF markdown.

        Args:
            tab: Reference to the document tab.

        Returns:
            ExportResult with MEBDF content and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
        """
        ...

    def export_section(self, tab: TabReference, anchor_id: str) -> ExportResult:
        """Export a specific section to MEBDF markdown.

        The section includes content from the heading through all subsections
        until the next heading of equal or higher level.

        Args:
            tab: Reference to the document tab.
            anchor_id: Heading anchor ID from hierarchy. Empty string for preamble.

        Returns:
            ExportResult with MEBDF content and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
            AnchorNotFoundError: If anchor_id doesn't exist in the document.
        """
        ...

    # -------------------------------------------------------------------------
    # Import Operations (MEBDF → Google Docs)
    # -------------------------------------------------------------------------

    def import_tab(self, tab: TabReference, content: str) -> ImportResult:
        """Import MEBDF markdown to replace entire tab content.

        Args:
            tab: Reference to the document tab.
            content: MEBDF markdown content.

        Returns:
            ImportResult indicating success and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
            MebdfParseError: If content has invalid MEBDF syntax.
            EmbeddedObjectNotFoundError: If placeholder references missing object.
        """
        ...

    def import_section(
        self, tab: TabReference, anchor_id: str, content: str
    ) -> ImportResult:
        """Import MEBDF markdown to replace a specific section.

        Only the target section is modified; content before and after
        remains unchanged.

        Args:
            tab: Reference to the document tab.
            anchor_id: Heading anchor ID for the section. Empty string for preamble.
            content: MEBDF markdown content for the section.

        Returns:
            ImportResult indicating success and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
            AnchorNotFoundError: If anchor_id doesn't exist in the document.
            MebdfParseError: If content has invalid MEBDF syntax.
            EmbeddedObjectNotFoundError: If placeholder references missing object.
        """
        ...
