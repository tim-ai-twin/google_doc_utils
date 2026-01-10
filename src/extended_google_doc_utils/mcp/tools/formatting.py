"""Formatting tools for Google Docs MCP server.

Tools:
- normalize_formatting: Apply consistent formatting throughout a document
- extract_styles: Extract formatting patterns from a source document
- apply_styles: Apply extracted styles to a target document

These tools enable document formatting cleanup and style matching between
documents while preserving content and embedded objects.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from pydantic import Field

from extended_google_doc_utils.mcp.errors import (
    MultipleTabsError,
    create_error_response,
)
from extended_google_doc_utils.mcp.schemas import (
    ApplyStylesResponse,
    ExtractStylesResponse,
    NormalizeFormattingResponse,
    StyleDefinition,
)
from extended_google_doc_utils.mcp.server import get_converter, mcp


@mcp.tool()
def normalize_formatting(
    document_id: Annotated[str, Field(description="Google Doc ID (from the document URL)")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")] = "",
    body_font: Annotated[str | None, Field(description="Font family for body text (e.g., 'Arial', 'Times New Roman')")] = None,
    body_size: Annotated[str | None, Field(description="Font size for body text (e.g., '11pt', '12pt')")] = None,
    heading_font: Annotated[str | None, Field(description="Font family for all headings")] = None,
    line_spacing: Annotated[str | None, Field(description="Line spacing ('single', '1.5', 'double')")] = None,
    space_after: Annotated[str | None, Field(description="Space after paragraphs (e.g., '6pt', '12pt')")] = None,
) -> dict[str, Any]:
    """Apply consistent formatting throughout a document.

    Use this tool to clean up documents with mixed fonts and styles.
    Only specified parameters are changed; others are left as-is.

    IMPORTANT: Embedded objects (images, charts) are preserved unchanged.

    Args:
        document_id: Google Doc ID (from the document URL).
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.
        body_font: Font family for body text (e.g., "Arial", "Times New Roman").
        body_size: Font size for body text (e.g., "11pt", "12pt").
        heading_font: Font family for all headings.
        line_spacing: Line spacing ("single", "1.5", "double").
        space_after: Space after paragraphs (e.g., "6pt", "12pt").

    Returns:
        dict containing:
        - success: True if operation succeeded
        - changes_made: Number of formatting changes applied
        - warnings: List of any issues (e.g., unsupported formatting preserved)

    Example:
        normalize_formatting(
            document_id="abc123",
            body_font="Arial",
            body_size="11pt",
            line_spacing="1.5"
        )
    """
    try:
        from extended_google_doc_utils.converter.types import TabReference

        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        # 1. Export document to MEBDF
        export_result = converter.export_tab(tab)
        content = export_result.content
        warnings = list(export_result.warnings)

        # 2. Transform MEBDF with new formatting
        transformed_content, changes_made = _transform_formatting(
            content,
            body_font=body_font,
            body_size=body_size,
            heading_font=heading_font,
            line_spacing=line_spacing,
            space_after=space_after,
        )

        # 3. Import back to Google Doc
        import_result = converter.import_tab(tab, transformed_content)
        warnings.extend(import_result.warnings)

        response = NormalizeFormattingResponse(
            success=True,
            changes_made=changes_made,
            warnings=warnings,
        )
        return asdict(response)

    except Exception as e:
        return asdict(create_error_response(e))


def _transform_formatting(
    content: str,
    body_font: str | None = None,
    body_size: str | None = None,
    heading_font: str | None = None,
    line_spacing: str | None = None,
    space_after: str | None = None,
) -> tuple[str, int]:
    """Transform MEBDF content with new formatting.

    This function applies formatting directives to the MEBDF content.
    Returns the transformed content and count of changes made.
    """
    import re

    changes_made = 0
    lines = content.split("\n")
    transformed_lines = []

    # Build formatting props string for body text
    body_props = []
    if body_font:
        body_props.append(f"font:{body_font}")
    if body_size:
        body_props.append(f"size:{body_size}")

    # Build formatting props string for headings
    heading_props = []
    if heading_font:
        heading_props.append(f"font:{heading_font}")

    for line in lines:
        # Check if line is a heading (starts with #)
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)

        if heading_match and heading_props:
            # Apply heading formatting
            hashes = heading_match.group(1)
            heading_text = heading_match.group(2)
            props_str = ",".join(heading_props)
            transformed_lines.append(f"{hashes} {{!{props_str}}}{heading_text}{{/!}}")
            changes_made += 1
        elif body_props and line.strip() and not heading_match:
            # Apply body formatting to non-empty, non-heading lines
            # Skip lines that are embedded objects, anchors, or already formatted
            if not line.strip().startswith("{^") and not line.strip().startswith("{!"):
                props_str = ",".join(body_props)
                transformed_lines.append(f"{{!{props_str}}}{line}{{/!}}")
                changes_made += 1
            else:
                transformed_lines.append(line)
        else:
            transformed_lines.append(line)

    return "\n".join(transformed_lines), changes_made


@mcp.tool()
def extract_styles(
    document_id: Annotated[str, Field(description="Source document ID to extract styles from")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Extract formatting patterns from a source document.

    Use this tool with apply_styles to match formatting between documents.
    For example, extract styles from a company template and apply them
    to a new document.

    Args:
        document_id: Source document ID to extract styles from.
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - styles: List of style definitions for body text and headings
        - source_document_id: Echo back the source document ID

    Example:
        styles = extract_styles(document_id="template123")
        apply_styles(document_id="newdoc456", styles=styles["styles"])
    """
    try:
        from extended_google_doc_utils.converter.types import TabReference

        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        # Export document to MEBDF
        export_result = converter.export_tab(tab)
        content = export_result.content

        # Extract styles from the MEBDF content
        styles = _extract_styles_from_mebdf(content)

        response = ExtractStylesResponse(
            success=True,
            styles=[
                StyleDefinition(
                    element_type=s["element_type"],
                    font_family=s.get("font_family"),
                    font_size=s.get("font_size"),
                    font_weight=s.get("font_weight"),
                    text_color=s.get("text_color"),
                    line_spacing=s.get("line_spacing"),
                    space_before=s.get("space_before"),
                    space_after=s.get("space_after"),
                )
                for s in styles
            ],
            source_document_id=document_id,
        )
        return asdict(response)

    except Exception as e:
        return asdict(create_error_response(e))


def _extract_styles_from_mebdf(content: str) -> list[dict[str, Any]]:
    """Extract formatting styles from MEBDF content.

    Analyzes the document to identify formatting patterns for body text
    and headings.
    """
    import re

    styles = []
    lines = content.split("\n")

    # Track found formatting
    body_formatting: dict[str, str] = {}
    heading_formatting: dict[int, dict[str, str]] = {}

    for line in lines:
        # Check for heading with formatting
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)

        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2)

            # Check for inline formatting in heading
            format_match = re.search(r"\{!([^}]+)\}.*\{/!\}", heading_text)
            if format_match:
                props = _parse_format_props(format_match.group(1))
                if level not in heading_formatting:
                    heading_formatting[level] = props
        else:
            # Check for body formatting
            format_match = re.search(r"\{!([^}]+)\}.*\{/!\}", line)
            if format_match and not body_formatting:
                body_formatting = _parse_format_props(format_match.group(1))

    # Build style definitions
    if body_formatting:
        styles.append({
            "element_type": "body",
            "font_family": body_formatting.get("font"),
            "font_size": body_formatting.get("size"),
        })

    for level in sorted(heading_formatting.keys()):
        props = heading_formatting[level]
        styles.append({
            "element_type": f"heading{level}",
            "font_family": props.get("font"),
            "font_size": props.get("size"),
        })

    return styles


def _parse_format_props(props_str: str) -> dict[str, str]:
    """Parse MEBDF formatting properties string into a dict."""
    props = {}
    for part in props_str.split(","):
        if ":" in part:
            key, value = part.split(":", 1)
            props[key.strip()] = value.strip()
    return props


@mcp.tool()
def apply_styles(
    document_id: Annotated[str, Field(description="Target document ID to apply styles to")],
    styles: Annotated[list[dict[str, Any]], Field(description="List of style definitions from extract_styles")],
    tab_id: Annotated[str, Field(description="Tab ID for multi-tab documents. Empty for single-tab docs.")] = "",
) -> dict[str, Any]:
    """Apply extracted styles to a target document.

    Use styles from extract_styles to match formatting from another document.
    Content and structure are preserved; only formatting changes.

    IMPORTANT: Embedded objects (images, charts) are preserved unchanged.

    Args:
        document_id: Target document ID to apply styles to.
        styles: List of style definitions from extract_styles.
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs.

    Returns:
        dict containing:
        - success: True if operation succeeded
        - changes_made: Number of formatting changes applied
        - warnings: List of any issues encountered

    Example:
        styles = extract_styles(document_id="template123")
        apply_styles(document_id="newdoc456", styles=styles["styles"])
    """
    try:
        from extended_google_doc_utils.converter.types import TabReference

        converter = get_converter()
        tab = TabReference(document_id=document_id, tab_id=tab_id)

        # Export document to MEBDF
        export_result = converter.export_tab(tab)
        content = export_result.content
        warnings = list(export_result.warnings)

        # Convert styles list to formatting parameters
        body_font = None
        body_size = None
        heading_font = None

        for style in styles:
            element_type = style.get("element_type", "")
            if element_type == "body":
                body_font = style.get("font_family")
                body_size = style.get("font_size")
            elif element_type.startswith("heading"):
                # Use first heading style as heading font
                if not heading_font:
                    heading_font = style.get("font_family")

        # Transform content with extracted styles
        transformed_content, changes_made = _transform_formatting(
            content,
            body_font=body_font,
            body_size=body_size,
            heading_font=heading_font,
        )

        # Import back to Google Doc
        import_result = converter.import_tab(tab, transformed_content)
        warnings.extend(import_result.warnings)

        response = ApplyStylesResponse(
            success=True,
            changes_made=changes_made,
            warnings=warnings,
        )
        return asdict(response)

    except Exception as e:
        return asdict(create_error_response(e))
