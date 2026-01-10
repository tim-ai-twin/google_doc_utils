"""Google Docs to Markdown Converter.

Bidirectional conversion between Google Docs native format and MEBDF
(Markdown Extensions for Basic Doc Formatting) v1.4.

Public API:
    - GoogleDocsConverter: Main converter class
    - TabReference: Reference to a document tab
    - HierarchyResult, ExportResult, ImportResult: Result types
    - ConverterError and subclasses: Exception types
"""

from extended_google_doc_utils.converter.converter import GoogleDocsConverter
from extended_google_doc_utils.converter.exceptions import (
    AnchorNotFoundError,
    ConverterError,
    EmbeddedObjectNotFoundError,
    MebdfParseError,
    MultipleTabsError,
)
from extended_google_doc_utils.converter.types import (
    EmbeddedObjectType,
    ExportResult,
    HeadingAnchor,
    HierarchyResult,
    ImportResult,
    TabReference,
)

__all__ = [
    # Main converter
    "GoogleDocsConverter",
    # Types
    "TabReference",
    "HeadingAnchor",
    "HierarchyResult",
    "ExportResult",
    "ImportResult",
    "EmbeddedObjectType",
    # Exceptions
    "ConverterError",
    "MultipleTabsError",
    "AnchorNotFoundError",
    "EmbeddedObjectNotFoundError",
    "MebdfParseError",
]
