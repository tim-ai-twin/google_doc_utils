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
    DocumentAccessError,
    EmbeddedObjectNotFoundError,
    MebdfParseError,
    MultipleTabsError,
    StyleReadError,
    StyleTransferError,
    StyleWriteError,
)
from extended_google_doc_utils.converter.style_reader import (
    read_document_styles,
    read_effective_style,
)
from extended_google_doc_utils.converter.style_writer import (
    apply_document_properties,
    apply_document_styles,
    apply_effective_styles,
)
from extended_google_doc_utils.converter.types import (
    DocumentProperties,
    DocumentStyles,
    EffectiveStyle,
    EmbeddedObjectType,
    ExportResult,
    HeadingAnchor,
    HierarchyResult,
    ImportResult,
    NamedStyleType,
    ParagraphStyleProperties,
    RGBColor,
    StyleApplicationResult,
    StyleSource,
    StyleTransferOptions,
    StyleTransferResult,
    TabReference,
    TextStyleProperties,
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
    # Style transfer types (Feature 130)
    "NamedStyleType",
    "StyleSource",
    "RGBColor",
    "TextStyleProperties",
    "ParagraphStyleProperties",
    "EffectiveStyle",
    "DocumentProperties",
    "DocumentStyles",
    "StyleTransferOptions",
    "StyleApplicationResult",
    "StyleTransferResult",
    # Style transfer functions (Feature 130)
    "read_document_styles",
    "read_effective_style",
    "apply_document_styles",
    "apply_document_properties",
    "apply_effective_styles",
    # Exceptions
    "ConverterError",
    "MultipleTabsError",
    "AnchorNotFoundError",
    "EmbeddedObjectNotFoundError",
    "MebdfParseError",
    # Style transfer exceptions (Feature 130)
    "StyleTransferError",
    "DocumentAccessError",
    "StyleReadError",
    "StyleWriteError",
]
