"""Style transfer tools for Google Docs MCP server.

Tools:
- get_document_styles: Get document-level properties and effective styles
- apply_document_styles: Apply styles from one document to another

These tools enable "Apply the styles from document A to document B" workflows
for LLMs. The tools capture effective/visible styles (what the user sees)
and apply them via style flattening.

Feature: 130-document-style-transfer
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from pydantic import Field

from extended_google_doc_utils.mcp.errors import create_error_response
from extended_google_doc_utils.mcp.server import mcp


def _get_credentials():
    """Get credentials from the MCP server state."""
    from extended_google_doc_utils.mcp.server import _credentials

    return _credentials


# =============================================================================
# T040: get_document_styles MCP tool
# =============================================================================


@mcp.tool()
def get_document_styles(
    document_id: Annotated[
        str, Field(description="Google Doc ID (from URL or sharing link)")
    ],
    tab_id: Annotated[
        str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")
    ] = "",
) -> dict[str, Any]:
    """Get document-level properties and effective styles from a Google Doc.

    Returns complete style information including:
    - Document properties: background color, margins, page size
    - Effective styles: What the user actually sees for all 9 style types
      (NORMAL_TEXT, TITLE, SUBTITLE, HEADING_1-6)

    The "effective" style captures what's visible - if paragraphs have inline
    overrides that differ from the style definition, those overrides are returned.

    Args:
        document_id: The Google Doc ID (from URL or sharing link)
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.

    Returns:
        dict containing:
        - document_properties: Background, margins, page size
        - effective_styles: Dict of style type to style properties
        - success: True if operation succeeded

    Example:
        styles = get_document_styles(document_id="abc123")
        # styles["effective_styles"]["HEADING_1"]["text"]["font_family"] -> "Arial"
    """
    try:
        from extended_google_doc_utils.converter.style_reader import (
            read_document_styles,
        )

        credentials = _get_credentials()
        styles = read_document_styles(document_id, credentials, tab_id)

        # Convert to JSON-serializable format
        return _document_styles_to_dict(styles)

    except Exception as e:
        return asdict(create_error_response(e))


def _document_styles_to_dict(styles) -> dict[str, Any]:
    """Convert DocumentStyles to JSON-serializable dict for MCP response."""
    from extended_google_doc_utils.converter.types import DocumentStyles

    # Document properties
    props = styles.document_properties
    doc_props = {
        "background_color": props.background_color.to_hex()
        if props.background_color
        else None,
        "margin_top_pt": props.margin_top_pt,
        "margin_bottom_pt": props.margin_bottom_pt,
        "margin_left_pt": props.margin_left_pt,
        "margin_right_pt": props.margin_right_pt,
        "page_width_pt": props.page_width_pt,
        "page_height_pt": props.page_height_pt,
    }

    # Effective styles
    effective = {}
    for style_type, eff_style in styles.effective_styles.items():
        text = eff_style.text_style
        para = eff_style.paragraph_style

        effective[style_type.value] = {
            "text": {
                "font_family": text.font_family,
                "font_size_pt": text.font_size_pt,
                "font_weight": text.font_weight,
                "text_color": text.text_color.to_hex() if text.text_color else None,
                "highlight_color": text.highlight_color.to_hex()
                if text.highlight_color
                else None,
                "bold": text.bold,
                "italic": text.italic,
                "underline": text.underline,
            },
            "paragraph": {
                "alignment": para.alignment,
                "line_spacing": para.line_spacing,
                "space_before_pt": para.space_before_pt,
                "space_after_pt": para.space_after_pt,
                "indent_start_pt": para.indent_start_pt,
                "indent_end_pt": para.indent_end_pt,
                "first_line_indent_pt": para.first_line_indent_pt,
            },
            "source": eff_style.source.value,
        }

    return {
        "success": True,
        "document_id": styles.document_id,
        "document_properties": doc_props,
        "effective_styles": effective,
    }


# =============================================================================
# T041: apply_document_styles MCP tool
# =============================================================================


@mcp.tool()
def apply_document_styles(
    source_document_id: Annotated[
        str, Field(description="Document ID to copy styles FROM")
    ],
    target_document_id: Annotated[
        str, Field(description="Document ID to apply styles TO")
    ],
    source_tab_id: Annotated[
        str, Field(description="Tab ID for source document. Empty for single-tab docs.")
    ] = "",
    target_tab_id: Annotated[
        str, Field(description="Tab ID for target document. Empty for single-tab docs.")
    ] = "",
    include_document_properties: Annotated[
        bool,
        Field(description="Apply background, margins, page size (default: True)"),
    ] = True,
    include_effective_styles: Annotated[
        bool, Field(description="Apply named style formatting (default: True)")
    ] = True,
) -> dict[str, Any]:
    """Apply styles from one Google Doc to another.

    Reads the effective (visible) styles from the source document and applies
    them to the target document. This enables requests like "Apply the styles
    from document A to document B."

    For named styles (headings, normal text, etc.), the source's effective
    formatting is applied inline to every matching paragraph in the target.
    Character-level overrides (like a bold word) in the target are preserved.

    Args:
        source_document_id: Document to copy styles FROM
        target_document_id: Document to apply styles TO
        source_tab_id: Tab ID for source document. Empty for single-tab docs.
        target_tab_id: Tab ID for target document. Empty for single-tab docs.
        include_document_properties: Apply background, margins, page size (default: True)
        include_effective_styles: Apply named style formatting (default: True)

    Returns:
        dict containing:
        - success: True if operation succeeded
        - document_properties_applied: Whether doc properties were updated
        - styles_applied: Dict of style type to paragraphs updated
        - total_paragraphs_updated: Sum of all paragraph updates
        - errors: List of any error messages

    Example:
        result = apply_document_styles(
            source_document_id="template123",
            target_document_id="newdoc456"
        )
        # result["total_paragraphs_updated"] -> 42
    """
    try:
        from extended_google_doc_utils.converter.style_writer import (
            apply_document_styles as _apply_document_styles,
        )
        from extended_google_doc_utils.converter.types import StyleTransferOptions

        credentials = _get_credentials()

        options = StyleTransferOptions(
            include_document_properties=include_document_properties,
            include_effective_styles=include_effective_styles,
            style_types=None,  # All 9 types
        )

        result = _apply_document_styles(
            source_document_id,
            target_document_id,
            options,
            credentials,
            source_tab_id,
            target_tab_id,
        )

        # Convert to JSON-serializable format
        return _transfer_result_to_dict(result)

    except Exception as e:
        return asdict(create_error_response(e))


def _transfer_result_to_dict(result) -> dict[str, Any]:
    """Convert StyleTransferResult to JSON-serializable dict."""
    styles_applied = {}
    for style_type, app_result in result.styles_applied.items():
        styles_applied[style_type.value] = {
            "paragraphs_updated": app_result.paragraphs_updated,
            "success": app_result.success,
            "error": app_result.error,
        }

    return {
        "success": result.success,
        "document_properties_applied": result.document_properties_applied,
        "styles_applied": styles_applied,
        "total_paragraphs_updated": result.total_paragraphs_updated,
        "errors": result.errors,
    }
