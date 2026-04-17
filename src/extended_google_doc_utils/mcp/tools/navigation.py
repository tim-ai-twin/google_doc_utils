"""Navigation tools for Google Docs MCP server.

Tools:
- get_hierarchy: Get the heading structure of a document tab
- list_documents: List accessible Google Docs (Phase 4)
- get_metadata: Get document metadata including tabs (Phase 4)
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from pydantic import Field

from extended_google_doc_utils.converter.types import TabReference
from extended_google_doc_utils.mcp.errors import (
    create_error_response,
    map_converter_error,
)
from extended_google_doc_utils.mcp.schemas import (
    DocumentMetadata,
    DocumentSummary,
    HeadingInfo,
    HierarchyResponse,
    ListDocumentsResponse,
    TabInfo,
)
from extended_google_doc_utils.mcp.server import get_converter, mcp


@mcp.tool()
def get_hierarchy(
    document_id: Annotated[str, Field(description="Google Doc ID (the long string after '/d/' in the URL)")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Leave empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Get the heading structure of a document tab with word counts.

    Returns headings with anchor IDs needed for section operations.
    Call this BEFORE using read_section or write_section to find
    the anchor_id for your target section.

    If the tab contains content before the first heading (or has no
    headings at all), the first entry will be a preamble pseudo-entry:
    ``anchor_id=""``, ``level=0``, ``text="(preamble)"``. Pass the empty
    anchor to ``read_section`` / ``write_section`` to target that region.

    Each heading includes ``word_count`` and ``char_count`` for the content
    under that section (up to the next heading of equal or higher level).
    The response also includes ``total_word_count`` and ``total_char_count``
    for the entire tab. Use these counts to:
    - Judge section size before deciding what to read
    - Get an overview of tab size to choose between reading the full tab
      vs. reading individual sections (e.g., skip full-tab export for
      documents under 2000 words)
    - Identify the largest sections in a document

    This is especially useful for large documents where you want to avoid
    reading unnecessary content and instead target only the relevant section.

    Args:
        document_id: Google Doc ID (the long string after '/d/' in the URL).
        tab_id: Tab ID for multi-tab documents. Leave empty for single-tab docs.
                Call get_metadata to find available tab IDs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - headings: List of headings with anchor_id, level (0-6; 0 = preamble),
                    text, word_count, and char_count
        - markdown: Pure markdown representation with anchors
        - total_word_count: Total words across the entire tab
        - total_char_count: Total characters across the entire tab

    Example response:
        {
            "success": true,
            "headings": [
                {"anchor_id": "", "level": 0, "text": "(preamble)",
                 "word_count": 42, "char_count": 310},
                {"anchor_id": "h.abc123", "level": 1, "text": "Introduction",
                 "word_count": 350, "char_count": 2100},
                {"anchor_id": "h.def456", "level": 2, "text": "Background",
                 "word_count": 120, "char_count": 780}
            ],
            "markdown": "{^ }(preamble) (42 words)\\n# {^ h.abc123}Introduction (350 words)\\n## {^ h.def456}Background (120 words)",
            "total_word_count": 512,
            "total_char_count": 3190
        }
    """
    try:
        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        result = converter.get_hierarchy(tab)

        # Convert to response
        response = HierarchyResponse(
            success=True,
            headings=[
                HeadingInfo(
                    anchor_id=h.anchor_id,
                    level=h.level,
                    text=h.text,
                    word_count=h.word_count,
                    char_count=h.char_count,
                )
                for h in result.headings
            ],
            markdown=result.markdown,
            total_word_count=result.total_word_count,
            total_char_count=result.total_char_count,
        )

        return asdict(response)

    except Exception as e:
        # Map converter exceptions to MCP errors
        error_response = _handle_navigation_error(e, document_id, tab_id)
        return asdict(error_response)


def _handle_navigation_error(
    error: Exception, document_id: str, tab_id: str
) -> Any:
    """Convert converter exceptions to MCP error responses."""
    return (
        map_converter_error(error, document_id)
        or create_error_response(error)
    )


@mcp.tool()
def list_documents(
    max_results: Annotated[int, Field(description="Maximum number of documents to return (default 25)")] = 25,
    query: Annotated[str | None, Field(description="Optional search query to filter documents by name")] = None,
) -> dict[str, Any]:
    """List Google Docs accessible to the current user.

    Use this tool to discover what documents are available before
    working with a specific document. Returns documents sorted by
    most recently modified.

    Args:
        max_results: Maximum documents to return (default 25, max 100).
        query: Optional search term to filter documents by name.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - documents: List of document summaries with document_id, title,
                     last_modified, and owner fields
        - total_count: Number of documents returned

    Example response:
        {
            "success": true,
            "documents": [
                {
                    "document_id": "1ABC...",
                    "title": "My Document",
                    "last_modified": "2026-01-10T12:00:00.000Z",
                    "owner": "user@example.com"
                }
            ],
            "total_count": 1
        }
    """
    try:
        converter = get_converter()
        docs = converter.list_documents(max_results=max_results, query=query)

        response = ListDocumentsResponse(
            success=True,
            documents=[
                DocumentSummary(
                    document_id=d["document_id"],
                    title=d["title"],
                    last_modified=d["last_modified"],
                    owner=d["owner"],
                )
                for d in docs
            ],
            total_count=len(docs),
        )

        return asdict(response)

    except Exception as e:
        return asdict(create_error_response(e))


@mcp.tool()
def get_metadata(
    document_id: Annotated[str, Field(description="Google Doc ID (from the document URL)")],
) -> dict[str, Any]:
    """Get metadata for a document including available tabs.

    Call this tool BEFORE working with a multi-tab document to discover
    available tab IDs. Single-tab documents don't require tab_id.

    Args:
        document_id: Google Doc ID (the long string after '/d/' in the URL).

    Returns:
        dict containing:
        - success: True if operation succeeded
        - document_id: Echo back the document ID
        - title: Document title
        - tabs: List of tabs with tab_id, title, and index
        - can_edit: Whether you have edit permission
        - can_comment: Whether you have comment permission

    Example response:
        {
            "success": true,
            "document_id": "1ABC...",
            "title": "My Document",
            "tabs": [
                {"tab_id": "t.0", "title": "Overview", "index": 0},
                {"tab_id": "t.1", "title": "Details", "index": 1}
            ],
            "can_edit": true,
            "can_comment": true
        }
    """
    try:
        converter = get_converter()
        meta = converter.get_metadata(document_id)

        response = DocumentMetadata(
            success=True,
            document_id=meta["document_id"],
            title=meta["title"],
            tabs=[
                TabInfo(
                    tab_id=t["tab_id"],
                    title=t["title"],
                    index=t["index"],
                )
                for t in meta["tabs"]
            ],
            can_edit=meta["can_edit"],
            can_comment=meta["can_comment"],
        )

        return asdict(response)

    except Exception as e:
        return asdict(create_error_response(e))
