# Font Validation Contract

**Feature**: 128-gdoc-font-validation
**Date**: 2026-01-12

## Overview

This contract defines the internal API for font validation in the MEBDF import layer. These are internal Python functions, not MCP tools (per spec requirement SC-005).

## Functions

### validate_font_family

Validates a font family name against the Google Docs font catalog.

```python
def validate_font_family(name: str) -> FontValidationResult:
    """
    Validate a font family name.

    Args:
        name: Font family name to validate (case-insensitive)

    Returns:
        FontValidationResult with:
        - is_valid: True if font exists
        - canonical_name: Properly-cased font name (if valid)
        - error_code: Error type (if invalid)
        - error_message: Human-readable error (if invalid)
        - suggestions: Alternative fonts to try (if invalid)
    """
```

**Example - Valid Font**:
```python
>>> validate_font_family("roboto")
FontValidationResult(
    is_valid=True,
    canonical_name="Roboto",
    normalized_weight=None,
    error_code=None,
    error_message=None,
    suggestions=[]
)
```

**Example - Invalid Font**:
```python
>>> validate_font_family("Helvetica")
FontValidationResult(
    is_valid=False,
    canonical_name=None,
    normalized_weight=None,
    error_code="INVALID_FONT_FAMILY",
    error_message="Font 'Helvetica' is not available in Google Docs.",
    suggestions=["Arial", "Roboto", "Open Sans"]
)
```

**Example - Variant Name Detected**:
```python
>>> validate_font_family("Roboto Light")
FontValidationResult(
    is_valid=False,
    canonical_name=None,
    normalized_weight=None,
    error_code="INVALID_FONT_VARIANT",
    error_message="'Roboto Light' appears to be a variant name. Use font family 'Roboto' with weight:300 instead.",
    suggestions=["Roboto"]
)
```

### validate_font_weight

Validates a font weight for a specific font family.

```python
def validate_font_weight(
    family: str,
    weight: int | str
) -> FontValidationResult:
    """
    Validate a font weight for a given family.

    Args:
        family: Font family name (must be valid)
        weight: Weight as int (100-900) or named string ("bold", "light")

    Returns:
        FontValidationResult with:
        - is_valid: True if weight is supported
        - canonical_name: Properly-cased font name
        - normalized_weight: Numeric weight value (if valid)
        - error_code: Error type (if invalid)
        - error_message: Human-readable error (if invalid)
        - suggestions: Supported weights for this font (if invalid)
    """
```

**Example - Valid Weight**:
```python
>>> validate_font_weight("Roboto", 300)
FontValidationResult(
    is_valid=True,
    canonical_name="Roboto",
    normalized_weight=300,
    error_code=None,
    error_message=None,
    suggestions=[]
)

>>> validate_font_weight("Roboto", "light")
FontValidationResult(
    is_valid=True,
    canonical_name="Roboto",
    normalized_weight=300,
    error_code=None,
    error_message=None,
    suggestions=[]
)
```

**Example - Invalid Weight for Font**:
```python
>>> validate_font_weight("Arial", 300)
FontValidationResult(
    is_valid=False,
    canonical_name="Arial",
    normalized_weight=None,
    error_code="INVALID_FONT_WEIGHT",
    error_message="Font 'Arial' does not support weight 300 (light). Supported weights: 400 (normal), 700 (bold)",
    suggestions=["400", "700"]
)
```

### normalize_font_name

Converts a font name to canonical casing.

```python
def normalize_font_name(name: str) -> str | None:
    """
    Normalize font name to canonical casing.

    Args:
        name: Font name in any casing

    Returns:
        Canonical font name, or None if not found
    """
```

**Examples**:
```python
>>> normalize_font_name("roboto")
"Roboto"

>>> normalize_font_name("ARIAL")
"Arial"

>>> normalize_font_name("times new roman")
"Times New Roman"

>>> normalize_font_name("Helvetica")
None
```

### suggest_similar_fonts

Suggests similar font names when an invalid name is provided.

```python
def suggest_similar_fonts(invalid_name: str, limit: int = 3) -> list[str]:
    """
    Suggest similar valid fonts for an invalid font name.

    Uses simple string similarity (Levenshtein distance or prefix matching)
    to find the most similar valid font names.

    Args:
        invalid_name: The invalid font name
        limit: Maximum suggestions to return

    Returns:
        List of valid font names sorted by similarity
    """
```

**Examples**:
```python
>>> suggest_similar_fonts("Robota")
["Roboto"]

>>> suggest_similar_fonts("Open")
["Open Sans"]

>>> suggest_similar_fonts("Sans")
["Open Sans", "PT Sans", "Noto Sans"]
```

## Error Response Contract

When font validation fails during MEBDF import, the MCP error response format:

```python
{
    "success": False,
    "error": {
        "code": "FONT_VALIDATION_ERROR",
        "type": "<INVALID_FONT_FAMILY|INVALID_FONT_WEIGHT|INVALID_FONT_VARIANT>",
        "message": "<human-readable error message>",
        "details": {
            "font_name": "<provided font name>",
            "weight": <provided weight if applicable>,
            "suggestions": ["<alternative 1>", "<alternative 2>", ...]
        }
    }
}
```

**Example Error Response**:
```json
{
    "success": false,
    "error": {
        "code": "FONT_VALIDATION_ERROR",
        "type": "INVALID_FONT_WEIGHT",
        "message": "Font 'Arial' does not support weight 300 (light). Supported weights: 400 (normal), 700 (bold)",
        "details": {
            "font_name": "Arial",
            "weight": 300,
            "suggestions": ["400", "700"]
        }
    }
}
```

## Integration Points

### MEBDF Import Layer

Validation is called in `mebdf_to_gdoc.py` during `serialize_node()` for `FormattingNode`:

```python
# In serialize_node(), FormattingNode handling
if "font" in props:
    font_value = props["font"]
    result = validate_font_family(font_value)
    if not result.is_valid:
        raise FontValidationError(
            error_code=result.error_code,
            message=result.error_message,
            font_name=font_value,
            suggestions=result.suggestions,
        )
    font_family = result.canonical_name

if "weight" in props and font_family:
    weight_value = props["weight"]
    result = validate_font_weight(font_family, weight_value)
    if not result.is_valid:
        raise FontValidationError(
            error_code=result.error_code,
            message=result.error_message,
            font_name=font_family,
            weight=weight_value,
            suggestions=result.suggestions,
        )
    font_weight = result.normalized_weight
```

### MCP Error Handler

`_handle_tab_error()` and `_handle_section_error()` convert `FontValidationError` to MCP response:

```python
elif isinstance(error, FontValidationError):
    return FontValidationMcpError(
        error.error_code,
        error.message,
        error.font_name,
        error.weight,
        error.suggestions,
    ).to_error_response()
```
