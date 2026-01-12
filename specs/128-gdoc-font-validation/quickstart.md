# Quickstart: Google Docs Font Validation

**Feature**: 128-gdoc-font-validation
**Date**: 2026-01-12

## Overview

This feature adds font validation to the MEBDF import layer to prevent silent font fallback to Arial when invalid fonts are specified.

## Key Files to Modify

### 1. New File: `src/extended_google_doc_utils/converter/font_catalog.py`

Create the font catalog and validation functions.

```python
"""Google Docs font catalog and validation.

This module provides:
- GOOGLE_DOCS_FONTS: Catalog of available fonts and weights
- validate_font_family(): Validate font names
- validate_font_weight(): Validate weight for a font
- normalize_font_name(): Case-insensitive name lookup
"""
```

### 2. Modify: `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py`

Add validation calls in `serialize_node()` for FormattingNode handling (~line 565):

**Before**:
```python
elif "font" in props:
    font_value = props["font"]
    if isinstance(font_value, str):
        font_family = font_value
```

**After**:
```python
elif "font" in props:
    font_value = props["font"]
    if isinstance(font_value, str):
        result = validate_font_family(font_value)
        if not result.is_valid:
            raise FontValidationError(
                error_code=result.error_code,
                message=result.error_message,
                font_name=font_value,
                suggestions=result.suggestions,
            )
        font_family = result.canonical_name
```

### 3. Modify: `src/extended_google_doc_utils/converter/exceptions.py`

Add new exception class:

```python
class FontValidationError(ConverterException):
    """Raised when MEBDF contains invalid font specification."""

    def __init__(
        self,
        error_code: str,
        message: str,
        font_name: str | None = None,
        weight: int | None = None,
        suggestions: list[str] | None = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.font_name = font_name
        self.weight = weight
        self.suggestions = suggestions or []
```

### 4. Modify: `src/extended_google_doc_utils/mcp/errors.py`

Add MCP error class for font validation:

```python
@dataclass
class FontValidationMcpError(McpError):
    """Font validation failure."""

    error_code: str
    message: str
    font_name: str | None
    weight: int | None
    suggestions: list[str]

    def to_error_response(self) -> dict:
        return {
            "success": False,
            "error": {
                "code": "FONT_VALIDATION_ERROR",
                "type": self.error_code,
                "message": self.message,
                "details": {
                    "font_name": self.font_name,
                    "weight": self.weight,
                    "suggestions": self.suggestions,
                },
            },
        }
```

### 5. Modify: `src/extended_google_doc_utils/mcp/tools/tabs.py` and `sections.py`

Update tool descriptions to include font catalog. Add after the formatting examples:

```python
"""
...existing docstring...

Available fonts (default Google Docs):
- Sans-serif: Arial, Roboto, Lato, Montserrat, Open Sans, Raleway, Work Sans
- Serif: Georgia, Times New Roman, Merriweather, Playfair Display
- Monospace: Courier New, Roboto Mono, Source Code Pro, Ubuntu Mono
- Handwriting: Caveat, Dancing Script, Pacifico

Common weights: 100 (thin), 300 (light), 400 (normal), 500 (medium), 700 (bold), 900 (black)
Note: Not all fonts support all weights. The system will error if an unsupported weight is used.

IMPORTANT: Use font family name and weight separately:
- Correct: {!font:Roboto, weight:300}light text{/!}
- Wrong: {!font:Roboto Light}text{/!} (will error)
"""
```

## Testing Strategy

### Tier A (Unit Tests)

Create `tests/tier_a/test_font_catalog.py`:

```python
def test_valid_font_accepted():
    """Verify valid fonts pass validation."""
    result = validate_font_family("Roboto")
    assert result.is_valid
    assert result.canonical_name == "Roboto"

def test_invalid_font_rejected():
    """Verify unknown fonts are rejected with suggestions."""
    result = validate_font_family("Helvetica")
    assert not result.is_valid
    assert result.error_code == "INVALID_FONT_FAMILY"
    assert len(result.suggestions) > 0

def test_font_case_insensitive():
    """Verify fonts are matched case-insensitively."""
    result = validate_font_family("roboto")
    assert result.is_valid
    assert result.canonical_name == "Roboto"

def test_variant_name_detected():
    """Verify variant names produce helpful errors."""
    result = validate_font_family("Roboto Light")
    assert not result.is_valid
    assert result.error_code == "INVALID_FONT_VARIANT"
    assert "Roboto" in result.suggestions

def test_valid_weight_accepted():
    """Verify supported weights pass."""
    result = validate_font_weight("Roboto", 300)
    assert result.is_valid
    assert result.normalized_weight == 300

def test_invalid_weight_rejected():
    """Verify unsupported weights are rejected."""
    result = validate_font_weight("Arial", 300)
    assert not result.is_valid
    assert result.error_code == "INVALID_FONT_WEIGHT"
    assert "400" in result.suggestions
```

Add to `tests/tier_a/test_mebdf_to_gdoc.py`:

```python
def test_invalid_font_raises_error():
    """Verify invalid fonts raise FontValidationError."""
    node = FormattingNode(
        properties={"font": "InvalidFont"},
        children=[TextNode(text="test")]
    )
    with pytest.raises(FontValidationError) as exc_info:
        serialize_node(node, 1, [])
    assert exc_info.value.error_code == "INVALID_FONT_FAMILY"

def test_invalid_weight_raises_error():
    """Verify invalid weights raise FontValidationError."""
    node = FormattingNode(
        properties={"font": "Arial", "weight": "300"},
        children=[TextNode(text="test")]
    )
    with pytest.raises(FontValidationError) as exc_info:
        serialize_node(node, 1, [])
    assert exc_info.value.error_code == "INVALID_FONT_WEIGHT"
```

### Tier B (Integration Tests)

**Critical**: This is where previous testing failed. We need to verify fonts **actually render correctly**.

Create `tests/tier_b/test_font_rendering.py`:

```python
def test_font_renders_correctly():
    """Verify font is actually applied in Google Doc (not falling back to Arial)."""
    # 1. Import content with Roboto font
    mebdf_content = "{!font:Roboto}Roboto text{/!}"
    result = converter.import_tab(tab, mebdf_content)
    assert result.success

    # 2. Export the document back
    exported = converter.export_tab(tab)

    # 3. Verify the exported content shows Roboto, not Arial
    # This is the KEY test - ensures round-trip preservation
    assert "Roboto" in exported.content or "{!font:Roboto}" in exported.content

def test_weight_renders_correctly():
    """Verify font weight is actually applied."""
    mebdf_content = "{!font:Roboto, weight:300}Light text{/!}"
    result = converter.import_tab(tab, mebdf_content)
    assert result.success

    exported = converter.export_tab(tab)
    # Verify weight is preserved in round-trip
    assert "weight:300" in exported.content or "light" in exported.content.lower()
```

## Implementation Order

1. **Create `font_catalog.py`** - Core validation logic and font data
2. **Add `FontValidationError`** - Exception class in exceptions.py
3. **Integrate validation** - Update mebdf_to_gdoc.py serialize_node()
4. **Add MCP error handling** - Update errors.py and tool error handlers
5. **Update tool descriptions** - Add font catalog to docstrings
6. **Write tier_a tests** - Unit tests for validation functions
7. **Write tier_b tests** - Integration tests for font rendering

## Validation Checklist

- [ ] Invalid font names produce clear errors (not silent Arial fallback)
- [ ] Invalid font weights produce clear errors with supported alternatives
- [ ] Variant names like "Roboto Light" are detected and explained
- [ ] Case-insensitive font matching works
- [ ] Named weights (thin, light, bold) work correctly
- [ ] Tool descriptions list available fonts
- [ ] Round-trip test verifies fonts actually render (not fall back to Arial)
