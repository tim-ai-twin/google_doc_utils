"""Section tools for Google Docs MCP server.

Tools:
- export_section: Export a specific section to MEBDF markdown
- import_section: Replace a section's content with MEBDF markdown

These tools enable safe, targeted editing where only the specified section
is modified while all other content remains unchanged.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from pydantic import Field

from extended_google_doc_utils.converter.types import TabReference
from extended_google_doc_utils.mcp.errors import (
    AnchorNotFoundError,
    MebdfParseError,
    MultipleTabsError,
    create_error_response,
)
from extended_google_doc_utils.mcp.schemas import (
    ExportSectionResponse,
    ImportSectionResponse,
)
from extended_google_doc_utils.mcp.server import get_converter, mcp


@mcp.tool()
def export_section(
    document_id: Annotated[str, Field(description="Google Doc ID (from the document URL)")],
    anchor_id: Annotated[str, Field(description="Heading anchor ID from get_hierarchy. Use empty string for preamble.")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Export a specific section of a document to MEBDF markdown.

    Use this tool to read ONE section of a document without retrieving
    the entire document. The section includes content from the heading
    through all subsections until the next heading of equal or higher level.

    IMPORTANT: Call get_hierarchy first to find the anchor_id for your
    target section.

    Args:
        document_id: Google Doc ID (from the document URL).
        anchor_id: Heading anchor ID from get_hierarchy. Use empty string
                   "" for the preamble (content before the first heading).
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - content: MEBDF markdown content of the section
        - anchor_id: Echo back the requested anchor ID
        - warnings: List of any non-fatal issues (e.g., unsupported formatting)

    Example:
        First call: get_hierarchy(document_id="abc123")
        Response shows: {"headings": [{"anchor_id": "h.xyz", "text": "My Section"}]}
        Then call: export_section(document_id="abc123", anchor_id="h.xyz")
    """
    try:
        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        result = converter.export_section(tab, anchor_id)

        response = ExportSectionResponse(
            success=True,
            content=result.content,
            anchor_id=anchor_id,
            warnings=result.warnings,
        )

        return asdict(response)

    except Exception as e:
        error_response = _handle_section_error(e, document_id, anchor_id, tab_id)
        return asdict(error_response)


@mcp.tool()
def import_section(
    document_id: Annotated[str, Field(description="Google Doc ID (from the document URL)")],
    anchor_id: Annotated[str, Field(description="Heading anchor ID for the section to replace. Use empty string for preamble.")],
    content: Annotated[str, Field(description="MEBDF markdown content to write. Should include the section heading line.")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Replace a section's content with new MEBDF markdown.

    IMPORTANT: Only the target section is modified. All other content
    in the document remains UNCHANGED. This enables safe editing of
    shared documents where you only modify your assigned section.

    The content should include the section heading (unless replacing preamble).
    Use MEBDF format for formatting:
    - Standard markdown: # headings, **bold**, *italic*, [links](url)
    - Extensions: {!highlight:yellow}text{/!}, {!underline}text{/!}
    - Preserve images: Include {^= objectId image} placeholders

    Args:
        document_id: Google Doc ID (from the document URL).
        anchor_id: Heading anchor ID for the section to replace.
                   Use empty string "" for the preamble.
        content: MEBDF markdown content to write. Should include the
                 section heading line.
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - anchor_id: Echo back the target anchor ID
        - preserved_objects: List of embedded object IDs that were preserved
        - warnings: List of any non-fatal issues

    Example:
        import_section(
            document_id="abc123",
            anchor_id="h.xyz",
            content="## My Section\\n\\nUpdated content with **bold** text."
        )
    """
    try:
        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        result = converter.import_section(tab, anchor_id, content)

        response = ImportSectionResponse(
            success=result.success,
            anchor_id=anchor_id,
            preserved_objects=result.preserved_objects,
            warnings=result.warnings,
        )

        return asdict(response)

    except Exception as e:
        error_response = _handle_section_error(e, document_id, anchor_id, tab_id)
        return asdict(error_response)


def _handle_section_error(
    error: Exception,
    document_id: str,
    anchor_id: str,
    tab_id: str
) -> Any:
    """Convert converter exceptions to MCP error responses."""
    from extended_google_doc_utils.converter import exceptions as conv_exc

    if isinstance(error, conv_exc.MultipleTabsError):
        return MultipleTabsError(document_id, error.tab_count).to_error_response()
    elif isinstance(error, conv_exc.AnchorNotFoundError):
        return AnchorNotFoundError(document_id, anchor_id).to_error_response()
    elif isinstance(error, conv_exc.MebdfParseError):
        return MebdfParseError(str(error)).to_error_response()
    else:
        return create_error_response(error)
