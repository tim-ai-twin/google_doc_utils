"""Custom exceptions for Google Docs to Markdown Converter."""

from __future__ import annotations


class ConverterError(Exception):
    """Base exception for converter errors."""

    pass


class MultipleTabsError(ConverterError):
    """Raised when tab_id is required but not provided.

    This error occurs when a document has multiple tabs and the operation
    requires specifying which tab to operate on.

    Attributes:
        tab_count: Number of tabs in the document.
    """

    def __init__(self, tab_count: int):
        self.tab_count = tab_count
        super().__init__(
            f"Document has {tab_count} tabs. Specify tab_id to select one."
        )


class AnchorNotFoundError(ConverterError):
    """Raised when a section anchor ID doesn't exist.

    This can happen if:
    - The heading was deleted
    - The heading was copy-pasted (creates new anchor ID)
    - The heading format was significantly modified

    Attributes:
        anchor_id: The anchor ID that was not found.
    """

    def __init__(self, anchor_id: str):
        self.anchor_id = anchor_id
        super().__init__(
            f"Anchor '{anchor_id}' not found. The heading may have been "
            "deleted or modified. Re-fetch the hierarchy to get current anchors."
        )


class EmbeddedObjectNotFoundError(ConverterError):
    """Raised when an embedded object placeholder references a missing object.

    Embedded objects (images, drawings, charts, etc.) cannot be created via
    placeholders - they must already exist in the document.

    Attributes:
        object_id: The object ID that was not found.
        object_type: The type of object (image, drawing, chart, etc.).
    """

    def __init__(self, object_id: str, object_type: str):
        self.object_id = object_id
        self.object_type = object_type
        super().__init__(
            f"Embedded {object_type} with ID '{object_id}' not found in document. "
            "Embedded objects cannot be created via placeholder."
        )


class MebdfParseError(ConverterError):
    """Raised when MEBDF content cannot be parsed.

    This error indicates syntax errors in the MEBDF markdown content.

    Attributes:
        line: The line number where the error occurred (if known).
        message: Description of the parse error.
    """

    def __init__(self, message: str, line: int | None = None):
        self.line = line
        self._message = message
        prefix = f"Line {line}: " if line else ""
        super().__init__(f"MEBDF parse error: {prefix}{message}")
