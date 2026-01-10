"""Structured error types for MCP tools.

All MCP tools return structured error responses that include:
- Error type for programmatic handling
- Human-readable message
- Actionable suggestion for recovery

This enables LLMs to understand errors and recover appropriately.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ErrorDetail:
    """Detailed error information for structured error responses.

    Attributes:
        type: Error class name (e.g., "AnchorNotFoundError").
        message: Human-readable error description.
        suggestion: How to fix the issue (optional).
    """

    type: str
    message: str
    suggestion: str | None = None


@dataclass
class ErrorResponse:
    """Standard error response returned by all MCP tools on failure.

    Attributes:
        success: Always False for error responses.
        error: Detailed error information.
    """

    success: bool = False
    error: ErrorDetail | None = None


class MCPError(Exception):
    """Base class for all MCP-related errors."""

    suggestion: str | None = None

    def to_error_response(self) -> ErrorResponse:
        """Convert exception to structured error response."""
        return ErrorResponse(
            success=False,
            error=ErrorDetail(
                type=self.__class__.__name__,
                message=str(self),
                suggestion=self.suggestion,
            ),
        )


class DocumentNotFoundError(MCPError):
    """Raised when document ID is invalid or not accessible."""

    suggestion = "Verify the document ID from the URL. The ID is the long string after '/d/' in the document URL."

    def __init__(self, document_id: str):
        super().__init__(f"Document '{document_id}' not found or not accessible")
        self.document_id = document_id


class PermissionDeniedError(MCPError):
    """Raised when user lacks required permissions."""

    suggestion = "Request access to the document or use a different Google account with appropriate permissions."

    def __init__(self, document_id: str, required_permission: str = "edit"):
        super().__init__(
            f"Permission denied: {required_permission} access required for document '{document_id}'"
        )
        self.document_id = document_id
        self.required_permission = required_permission


class MultipleTabsError(MCPError):
    """Raised when tab_id is required but not provided for multi-tab document."""

    suggestion = "Call get_metadata first to see available tab IDs, then specify tab_id in your request."

    def __init__(self, document_id: str, tab_count: int):
        super().__init__(
            f"Document '{document_id}' has {tab_count} tabs. Please specify tab_id."
        )
        self.document_id = document_id
        self.tab_count = tab_count


class TabNotFoundError(MCPError):
    """Raised when the specified tab_id doesn't exist."""

    suggestion = "Call get_metadata to see available tab IDs for this document."

    def __init__(self, document_id: str, tab_id: str):
        super().__init__(f"Tab '{tab_id}' not found in document '{document_id}'")
        self.document_id = document_id
        self.tab_id = tab_id


class AnchorNotFoundError(MCPError):
    """Raised when anchor_id doesn't exist in the document."""

    suggestion = "Call get_hierarchy to see available anchor IDs for sections in this document."

    def __init__(self, document_id: str, anchor_id: str):
        super().__init__(f"Anchor '{anchor_id}' not found in document '{document_id}'")
        self.document_id = document_id
        self.anchor_id = anchor_id


class MebdfParseError(MCPError):
    """Raised when MEBDF content cannot be parsed."""

    suggestion = "Check the MEBDF format specification. Common issues: unmatched formatting tags, invalid anchor syntax."

    def __init__(self, message: str, line_number: int | None = None):
        if line_number:
            full_message = f"MEBDF parse error at line {line_number}: {message}"
        else:
            full_message = f"MEBDF parse error: {message}"
        super().__init__(full_message)
        self.line_number = line_number


class EmbeddedObjectNotFoundError(MCPError):
    """Raised when embedded object placeholder references missing object."""

    suggestion = "The object ID must exist in the document. Export the document first to see available object IDs."

    def __init__(self, object_id: str):
        super().__init__(f"Embedded object '{object_id}' not found in document")
        self.object_id = object_id


class CredentialError(MCPError):
    """Raised when OAuth credentials are missing or invalid."""

    suggestion = "Run 'python scripts/bootstrap_oauth.py' to set up Google API credentials."

    def __init__(self, message: str = "OAuth credentials not available"):
        super().__init__(message)


class GoogleAPIError(MCPError):
    """Raised when Google API returns an error."""

    suggestion = "Check the error message for details. If the issue persists, verify your API quotas and permissions."

    def __init__(self, message: str, status_code: int | None = None):
        if status_code:
            full_message = f"Google API error ({status_code}): {message}"
        else:
            full_message = f"Google API error: {message}"
        super().__init__(full_message)
        self.status_code = status_code


def create_error_response(error: Exception) -> ErrorResponse:
    """Create a structured error response from any exception.

    Args:
        error: The exception to convert.

    Returns:
        ErrorResponse with structured error details.
    """
    if isinstance(error, MCPError):
        return error.to_error_response()

    # Handle unknown errors
    return ErrorResponse(
        success=False,
        error=ErrorDetail(
            type=error.__class__.__name__,
            message=str(error),
            suggestion="An unexpected error occurred. Check the error message for details.",
        ),
    )
