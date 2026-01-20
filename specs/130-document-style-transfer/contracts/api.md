# API Contracts: Document Style Transfer

**Feature**: 130-document-style-transfer
**Date**: 2026-01-19

## Python API

### Module: `extended_google_doc_utils.converter.style_reader`

#### `read_document_styles`

Read complete style information from a Google Doc.

```python
def read_document_styles(
    document_id: str,
    credentials: OAuthCredentials | None = None,
) -> DocumentStyles:
    """Read document-level properties and effective styles from a Google Doc.

    Args:
        document_id: The Google Doc ID (from URL or API).
        credentials: OAuth credentials. If None, uses default credential manager.

    Returns:
        DocumentStyles containing:
        - document_properties: Background, margins, page size
        - effective_styles: Dict of NamedStyleType → EffectiveStyle for all 9 types

    Raises:
        GoogleDocsApiError: If API call fails (permissions, invalid ID, etc.)
        ValueError: If document_id is empty or invalid format

    Example:
        >>> styles = read_document_styles("1abc...xyz")
        >>> styles.document_properties.background_color
        RGBColor(red=0.95, green=0.95, blue=0.95)
        >>> styles.effective_styles[NamedStyleType.HEADING_1].text_style.font_family
        "Roboto"
    """
```

#### `read_effective_style`

Read effective style for a single named style type.

```python
def read_effective_style(
    document_id: str,
    style_type: NamedStyleType,
    credentials: OAuthCredentials | None = None,
) -> EffectiveStyle:
    """Read the effective/visible style for a specific named style type.

    Analyzes actual paragraphs in the document to determine what the user sees.
    Falls back to style definition if no paragraphs of that type exist.

    Args:
        document_id: The Google Doc ID.
        style_type: Which named style to read (e.g., NamedStyleType.HEADING_1).
        credentials: OAuth credentials. If None, uses default credential manager.

    Returns:
        EffectiveStyle with text and paragraph properties, plus source indicator.

    Raises:
        GoogleDocsApiError: If API call fails.

    Example:
        >>> style = read_effective_style("1abc...xyz", NamedStyleType.HEADING_1)
        >>> style.text_style.font_size_pt
        24.0
        >>> style.source
        StyleSource.PARAGRAPH_SAMPLE
    """
```

### Module: `extended_google_doc_utils.converter.style_writer`

#### `apply_document_styles`

Transfer styles from source to target document.

```python
def apply_document_styles(
    source_document_id: str,
    target_document_id: str,
    options: StyleTransferOptions | None = None,
    credentials: OAuthCredentials | None = None,
) -> StyleTransferResult:
    """Apply styles from source document to target document.

    Reads effective styles from source and applies them to all matching
    paragraphs in target. Uses "style flattening" - applies formatting inline
    since Google Docs API doesn't support updating named style definitions.

    Args:
        source_document_id: Document to read styles from.
        target_document_id: Document to apply styles to.
        options: Control what gets transferred. Default: all properties and styles.
        credentials: OAuth credentials. If None, uses default credential manager.

    Returns:
        StyleTransferResult with:
        - success: True if all operations completed
        - document_properties_applied: Whether doc properties were updated
        - styles_applied: Dict of style type → paragraphs updated
        - total_paragraphs_updated: Sum of all paragraph updates
        - errors: List of any error messages

    Raises:
        GoogleDocsApiError: If API call fails (permissions, invalid ID, etc.)
        ValueError: If source and target IDs are invalid

    Example:
        >>> result = apply_document_styles("source_id", "target_id")
        >>> result.success
        True
        >>> result.styles_applied[NamedStyleType.HEADING_1].paragraphs_updated
        5
    """
```

#### `apply_document_properties`

Apply only document-level properties (not named styles).

```python
def apply_document_properties(
    source_document_id: str,
    target_document_id: str,
    credentials: OAuthCredentials | None = None,
) -> bool:
    """Apply document-level properties from source to target.

    Transfers: background color, margins, page size.
    Does NOT transfer named styles.

    Args:
        source_document_id: Document to read properties from.
        target_document_id: Document to apply properties to.
        credentials: OAuth credentials.

    Returns:
        True if properties were applied successfully.

    Raises:
        GoogleDocsApiError: If API call fails.
    """
```

#### `apply_effective_styles`

Apply only effective named styles (not document properties).

```python
def apply_effective_styles(
    source_document_id: str,
    target_document_id: str,
    style_types: list[NamedStyleType] | None = None,
    credentials: OAuthCredentials | None = None,
) -> dict[NamedStyleType, StyleApplicationResult]:
    """Apply effective styles from source to target paragraphs.

    For each style type, finds all paragraphs of that type in target
    and applies the source's effective style formatting inline.

    Args:
        source_document_id: Document to read effective styles from.
        target_document_id: Document to apply styles to.
        style_types: Which styles to transfer. None = all 9 types.
        credentials: OAuth credentials.

    Returns:
        Dict mapping style type to application result (paragraphs updated).

    Raises:
        GoogleDocsApiError: If API call fails.
    """
```

## MCP Tools

### Module: `extended_google_doc_utils.mcp.tools.styles`

#### Tool: `get_document_styles`

```python
@mcp.tool()
async def get_document_styles(
    document_id: str,
) -> dict:
    """Get document-level properties and effective styles from a Google Doc.

    Returns complete style information including:
    - Document properties: background color, margins, page size
    - Effective styles: What the user actually sees for all 9 style types
      (NORMAL_TEXT, TITLE, SUBTITLE, HEADING_1-6)

    The "effective" style captures what's visible - if paragraphs have inline
    overrides that differ from the style definition, those overrides are returned.

    Args:
        document_id: The Google Doc ID (from URL or sharing link)

    Returns:
        {
            "document_properties": {
                "background_color": "#f5f5f5" | null,
                "margin_top_pt": 72.0,
                "margin_bottom_pt": 72.0,
                "margin_left_pt": 72.0,
                "margin_right_pt": 72.0,
                "page_width_pt": 612.0,
                "page_height_pt": 792.0
            },
            "effective_styles": {
                "NORMAL_TEXT": {
                    "text": {
                        "font_family": "Arial",
                        "font_size_pt": 11.0,
                        "font_weight": 400,
                        "text_color": "#000000",
                        "highlight_color": null,
                        "bold": false,
                        "italic": false,
                        "underline": false
                    },
                    "paragraph": {
                        "alignment": "START",
                        "line_spacing": 1.15,
                        "space_before_pt": 0.0,
                        "space_after_pt": 0.0,
                        "indent_start_pt": 0.0,
                        "indent_end_pt": 0.0,
                        "first_line_indent_pt": 0.0
                    },
                    "source": "paragraph_sample"
                },
                "HEADING_1": { ... },
                // ... all 9 style types
            }
        }
    """
```

#### Tool: `apply_document_styles`

```python
@mcp.tool()
async def apply_document_styles(
    source_document_id: str,
    target_document_id: str,
    include_document_properties: bool = True,
    include_effective_styles: bool = True,
) -> dict:
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
        include_document_properties: Apply background, margins, page size (default: True)
        include_effective_styles: Apply named style formatting (default: True)

    Returns:
        {
            "success": true,
            "document_properties_applied": true,
            "styles_applied": {
                "HEADING_1": {"paragraphs_updated": 3},
                "HEADING_2": {"paragraphs_updated": 5},
                "NORMAL_TEXT": {"paragraphs_updated": 42}
            },
            "total_paragraphs_updated": 50,
            "errors": []
        }
    """
```

## Error Handling

### Custom Exceptions

```python
class StyleTransferError(Exception):
    """Base exception for style transfer operations."""
    pass

class DocumentAccessError(StyleTransferError):
    """Cannot access document (permissions, not found)."""
    pass

class StyleReadError(StyleTransferError):
    """Error reading styles from document."""
    pass

class StyleWriteError(StyleTransferError):
    """Error applying styles to document."""
    pass
```

### Error Response Format (MCP)

```json
{
    "error": true,
    "error_type": "DocumentAccessError",
    "message": "Cannot access document: permission denied",
    "document_id": "1abc...xyz"
}
```

## Type Exports

### From `extended_google_doc_utils.converter.types`

```python
__all__ = [
    # Existing exports...

    # New for style transfer
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
]
```

### From `extended_google_doc_utils.converter`

```python
__all__ = [
    # Existing exports...

    # New for style transfer
    "read_document_styles",
    "read_effective_style",
    "apply_document_styles",
    "apply_document_properties",
    "apply_effective_styles",
]
```
