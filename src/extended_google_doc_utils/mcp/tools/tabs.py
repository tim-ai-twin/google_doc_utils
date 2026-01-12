"""Tab tools for Google Docs MCP server.

Tools:
- export_tab: Export entire tab to MEBDF markdown
- import_tab: Replace entire tab with MEBDF markdown

These tools operate on entire tabs. For targeted section editing,
use export_section and import_section instead.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from pydantic import Field

from extended_google_doc_utils.converter.types import TabReference
from extended_google_doc_utils.mcp.errors import (
    FontValidationError as FontValidationMcpError,
    MebdfParseError,
    MultipleTabsError,
    create_error_response,
)
from extended_google_doc_utils.mcp.schemas import (
    ExportTabResponse,
    ImportTabResponse,
)
from extended_google_doc_utils.mcp.server import get_converter, mcp


@mcp.tool()
def export_tab(
    document_id: Annotated[str, Field(description="Google Doc ID (from the document URL)")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Leave empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Export an entire document tab to MEBDF markdown.

    Use this tool to read the FULL content of a document tab.
    For reading just one section, use export_section instead.

    Args:
        document_id: Google Doc ID (from the document URL).
        tab_id: Tab ID for multi-tab documents. Leave empty for single-tab docs.
                Call get_metadata to find available tab IDs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - content: Full MEBDF markdown content of the tab
        - tab_id: The resolved tab ID (useful if you passed empty string)
        - warnings: List of any non-fatal issues
    """
    try:
        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        result = converter.export_tab(tab)

        response = ExportTabResponse(
            success=True,
            content=result.content,
            tab_id=tab_id,
            warnings=result.warnings,
        )

        return asdict(response)

    except Exception as e:
        error_response = _handle_tab_error(e, document_id, tab_id)
        return asdict(error_response)


@mcp.tool()
def import_tab(
    document_id: Annotated[str, Field(description="Google Doc ID (from the document URL)")],
    content: Annotated[str, Field(description="MEBDF markdown content to write to the tab")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Replace entire tab content with MEBDF markdown.

    WARNING: This replaces ALL content in the tab. For targeted edits
    that preserve other sections, use import_section instead.

    Use MEBDF format for formatting:
    - Standard markdown: # headings, **bold**, *italic*, [links](url), - bullets, 1. numbered
    - Inline code: `code` renders in monospace font

    Text formatting (inline):
    - {!underline}underlined text{/!}
    - {!color:#FF0000}red text{/!} or {!color:red}red{/!}
    - {!highlight:yellow}highlighted{/!} - background color
    - {!mono}monospace{/!} or {!font:Roboto}custom font{/!}
    - {!font:Roboto, weight:300}light weight{/!} (100-900 or: thin, light, bold, etc.)
    - {!size:14pt}larger text{/!}

    Paragraph formatting:
    - {!align:center}centered text{/!} (left, center, right, justify)
    - {!line-spacing:1.5}spaced text{/!} (single, 1.15, 1.5, double)
    - {!space-before:12pt, space-after:6pt}with spacing{/!}
    - {!indent-left:0.5in}indented{/!}

    Combine properties: {!color:#0000FF, size:16pt, align:center}styled{/!}
    Preserve images: Include {^= objectId image} placeholders

    Available fonts (default Google Docs):
    - Sans-serif: Arial, Roboto, Lato, Montserrat, Open Sans, Raleway, Work Sans,
      Noto Sans, Nunito, Oswald, PT Sans, Ubuntu, Verdana, Comfortaa, Trebuchet MS
    - Serif: Georgia, Times New Roman, Merriweather, Playfair Display, PT Serif, Spectral
    - Monospace: Courier New, Roboto Mono, Source Code Pro, Ubuntu Mono
    - Handwriting: Caveat, Dancing Script, Pacifico, Lobster, Comic Sans MS

    Common weights: 100 (thin), 300 (light), 400 (normal), 500 (medium), 700 (bold), 900 (black)
    Note: Not all fonts support all weights. The system will error if an unsupported weight is used.

    IMPORTANT: Use font family and weight separately:
    - Correct: {!font:Roboto, weight:300}light text{/!}
    - Wrong: {!font:Roboto Light}text{/!} (will error - use weight property instead)

    Args:
        document_id: Google Doc ID (from the document URL).
        content: MEBDF markdown content to write to the tab.
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - tab_id: The target tab ID
        - preserved_objects: List of embedded object IDs that were preserved
        - warnings: List of any non-fatal issues
    """
    try:
        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        result = converter.import_tab(tab, content)

        response = ImportTabResponse(
            success=result.success,
            tab_id=tab_id,
            preserved_objects=result.preserved_objects,
            warnings=result.warnings,
        )

        return asdict(response)

    except Exception as e:
        error_response = _handle_tab_error(e, document_id, tab_id)
        return asdict(error_response)


def _handle_tab_error(error: Exception, document_id: str, tab_id: str) -> Any:
    """Convert converter exceptions to MCP error responses."""
    from extended_google_doc_utils.converter import exceptions as conv_exc

    if isinstance(error, conv_exc.MultipleTabsError):
        return MultipleTabsError(document_id, error.tab_count).to_error_response()
    elif isinstance(error, conv_exc.MebdfParseError):
        return MebdfParseError(str(error)).to_error_response()
    elif isinstance(error, conv_exc.FontValidationError):
        return FontValidationMcpError(
            error.error_code,
            str(error),
            error.font_name,
            error.weight,
            error.suggestions,
        ).to_error_response()
    else:
        return create_error_response(error)
