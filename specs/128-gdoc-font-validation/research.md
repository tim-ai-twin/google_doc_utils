# Research: Google Docs Font Validation

**Feature**: 128-gdoc-font-validation
**Date**: 2026-01-12

## Key Research Questions

### 1. Why do fonts silently fail and render as Arial?

**Finding**: The Google Docs API accepts ANY string as a font family name without error. When the font doesn't exist or the font family name is incorrectly specified, Google Docs silently falls back to Arial.

**Root Cause Identified**: In our previous implementation, tier_b tests passed because:
- Tests verified the API request was correctly structured
- Tests verified the API call succeeded (no error)
- Tests did NOT verify the rendered font in the resulting document
- The API returned success even when fonts fell back to Arial

**Key Insight**: The Google Docs API behavior is:
1. Accept request with any font family name
2. If font exists → render with that font
3. If font doesn't exist → render as Arial, return success (no error)

### 2. How must fonts be specified in the Google Docs API?

**Decision**: Font family and weight MUST be specified separately.

**Correct Usage**:
```python
'weightedFontFamily': {
    'fontFamily': 'Roboto',  # Just the base family name
    'weight': 300            # Weight as numeric value
}
```

**Incorrect Usage** (causes Arial fallback):
```python
'weightedFontFamily': {
    'fontFamily': 'Roboto Light',  # WRONG - variant name as family
    'weight': 400
}
```

**Rationale**: Google Docs API uses `weightedFontFamily` which separates:
- `fontFamily`: Base typeface name (e.g., "Roboto")
- `weight`: Numeric thickness (100-900)

Variant names like "Roboto Light" are NOT valid font family names.

**Alternatives Considered**: None - this is the only correct API usage pattern.

### 3. What fonts are available in a default Google Doc?

**Decision**: Use a curated catalog of commonly available fonts rather than attempting dynamic discovery.

**Rationale**:
- Google Docs includes ~40 fonts in the default dropdown menu
- Users can add more via "More fonts" but the base set is consistent
- Dynamic font discovery would require:
  - Additional API call (adds latency)
  - Google Fonts API key
  - Complex caching logic
- The default fonts are stable and documented

**Default Google Docs Font Catalog** (based on Google Docs dropdown menu):

| Font Family | Weights Available | Category |
|-------------|-------------------|----------|
| Arial | 400, 700 | Sans-serif |
| Arial Black | 900 | Sans-serif |
| Comic Sans MS | 400, 700 | Handwriting |
| Courier New | 400, 700 | Monospace |
| Georgia | 400, 700 | Serif |
| Impact | 400 | Sans-serif |
| Roboto | 100, 300, 400, 500, 700, 900 | Sans-serif |
| Roboto Mono | 100, 300, 400, 500, 700 | Monospace |
| Times New Roman | 400, 700 | Serif |
| Trebuchet MS | 400, 700 | Sans-serif |
| Verdana | 400, 700 | Sans-serif |
| Lato | 100, 300, 400, 700, 900 | Sans-serif |
| Montserrat | 100, 200, 300, 400, 500, 600, 700, 800, 900 | Sans-serif |
| Open Sans | 300, 400, 500, 600, 700, 800 | Sans-serif |
| Oswald | 200, 300, 400, 500, 600, 700 | Sans-serif |
| Playfair Display | 400, 500, 600, 700, 800, 900 | Serif |
| PT Sans | 400, 700 | Sans-serif |
| PT Serif | 400, 700 | Serif |
| Raleway | 100, 200, 300, 400, 500, 600, 700, 800, 900 | Sans-serif |
| Source Code Pro | 200, 300, 400, 500, 600, 700, 900 | Monospace |
| Ubuntu | 300, 400, 500, 700 | Sans-serif |
| Ubuntu Mono | 400, 700 | Monospace |
| Merriweather | 300, 400, 700, 900 | Serif |
| Noto Sans | 100, 200, 300, 400, 500, 600, 700, 800, 900 | Sans-serif |
| Nunito | 200, 300, 400, 500, 600, 700, 800, 900 | Sans-serif |
| Caveat | 400, 500, 600, 700 | Handwriting |
| Comfortaa | 300, 400, 500, 600, 700 | Sans-serif |
| Dancing Script | 400, 500, 600, 700 | Handwriting |
| Lobster | 400 | Handwriting |
| Pacifico | 400 | Handwriting |
| Spectral | 200, 300, 400, 500, 600, 700, 800 | Serif |
| Work Sans | 100, 200, 300, 400, 500, 600, 700, 800, 900 | Sans-serif |

**Alternatives Considered**:
1. Dynamic Google Fonts API query - rejected (adds complexity, API key requirement)
2. Accept any font name - rejected (defeats the purpose of validation)
3. Very minimal list (Arial, Times, Courier only) - rejected (too restrictive)

### 4. How should validation errors be handled?

**Decision**: Return clear error messages identifying the invalid font/weight and suggesting alternatives.

**Error Response Format**:
```python
{
    "success": False,
    "error": "INVALID_FONT",
    "message": "Font 'FakeFont' is not available in Google Docs. Did you mean: Arial, Roboto, Georgia?",
    "invalid_font": "FakeFont",
    "suggestions": ["Arial", "Roboto", "Georgia"]
}
```

**For invalid weight**:
```python
{
    "success": False,
    "error": "INVALID_FONT_WEIGHT",
    "message": "Font 'Arial' does not support weight 300 (light). Supported weights: 400 (normal), 700 (bold)",
    "font": "Arial",
    "requested_weight": 300,
    "supported_weights": [400, 700]
}
```

**Rationale**: LLMs can self-correct when given clear error messages with alternatives.

**Alternatives Considered**:
1. Auto-correct to nearest valid value - rejected (hides potential issues, LLM doesn't learn)
2. Warning but proceed anyway - rejected (defeats the purpose, still renders as Arial)
3. Generic "invalid font" message - rejected (not actionable for LLMs)

### 5. Where should validation occur?

**Decision**: Validate in the MEBDF import layer BEFORE constructing Google Docs API requests.

**Location**: `mebdf_to_gdoc.py` in the `serialize_node()` function where font properties are processed (around lines 559-594).

**Validation Flow**:
```
MEBDF Content → Parse → Validate Fonts → Build API Requests → Send to Google Docs
                              ↓
                       (Early exit with error if invalid)
```

**Rationale**:
- Early validation prevents wasted API calls
- Clear error attribution (user's MEBDF input vs API failure)
- Single validation point for all import operations (tab and section)

**Alternatives Considered**:
1. Validate at API response level - rejected (too late, font already rendered as Arial)
2. Validate in MCP tool layer - rejected (duplicates logic for tab/section tools)
3. Separate validation pass before import - rejected (adds complexity, less efficient)

### 6. How should case-insensitivity be handled?

**Decision**: Accept font names case-insensitively, normalize to canonical casing.

**Implementation**:
```python
FONT_CATALOG = {
    "arial": {"canonical": "Arial", "weights": [400, 700]},
    "roboto": {"canonical": "Roboto", "weights": [100, 300, 400, 500, 700, 900]},
    # ...
}

def normalize_font_name(input_name: str) -> str | None:
    """Return canonical font name or None if not found."""
    entry = FONT_CATALOG.get(input_name.lower())
    return entry["canonical"] if entry else None
```

**Rationale**:
- LLMs may generate "roboto" instead of "Roboto"
- Improves usability without ambiguity
- Google Docs API itself is somewhat case-tolerant

### 7. How should the font catalog be exposed to LLMs?

**Decision**: Embed font catalog summary in tool descriptions for `import_section` and `import_tab`.

**Tool Description Addition**:
```text
Available fonts and weights:
- Monospace: Courier New, Roboto Mono, Source Code Pro, Ubuntu Mono
- Sans-serif: Arial, Roboto, Lato, Montserrat, Open Sans, Raleway
- Serif: Georgia, Times New Roman, Playfair Display, Merriweather
- Handwriting: Caveat, Dancing Script, Pacifico

Common weight values: 100 (thin), 300 (light), 400 (normal), 500 (medium), 700 (bold), 900 (black)
Note: Not all fonts support all weights. Use {!font:Roboto, weight:300} syntax.
```

**Rationale**: Per spec requirement SC-005, no new MCP tools. Tool descriptions are visible to LLMs at tool call time.

## Implementation Architecture

### New Components

1. **Font Catalog Module** (`font_catalog.py`):
   - `GOOGLE_DOCS_FONTS`: Dictionary mapping lowercase font names to canonical names and weights
   - `validate_font_family(name: str) -> ValidationResult`
   - `validate_font_weight(family: str, weight: int) -> ValidationResult`
   - `suggest_similar_fonts(invalid_name: str) -> list[str]`

2. **Validation Integration**:
   - Add validation in `mebdf_to_gdoc.py` after font property extraction
   - Raise `FontValidationError` with structured error info
   - MCP error handlers convert to user-friendly response

3. **Updated Tool Descriptions**:
   - Add font catalog summary to `import_section` and `import_tab` docstrings

### Testing Strategy

Per user input, we need tests that verify fonts **actually render correctly**:

1. **Contract Tests** (tier_a):
   - `test_valid_font_accepted`: Verify valid fonts pass validation
   - `test_invalid_font_rejected`: Verify made-up fonts produce errors
   - `test_invalid_weight_rejected`: Verify unsupported weights produce errors
   - `test_font_case_insensitive`: Verify "roboto" normalizes to "Roboto"
   - `test_variant_name_rejected`: Verify "Roboto Light" produces helpful error

2. **Integration Tests** (tier_b):
   - `test_font_renders_correctly`: Apply font, export document, verify font in export
   - `test_weight_renders_correctly`: Apply weight, verify weight in export
   - This is the KEY test - ensures round-trip preservation

3. **Validation Approach**:
   - Instead of just checking API success, export the document and verify the font/weight matches what was requested
   - Use `gdoc_to_mebdf.py` export to validate fonts rendered correctly

## Summary

| Question | Decision | Rationale |
|----------|----------|-----------|
| Silent fallback cause | API accepts any font, silently falls back | Documented API behavior |
| Font specification | Family + weight separately | API requirement |
| Font catalog | Curated ~35 fonts | Balance coverage vs complexity |
| Error handling | Structured errors with suggestions | Enable LLM self-correction |
| Validation location | MEBDF import layer | Early exit, single point |
| Case handling | Case-insensitive, normalize | Improve usability |
| LLM exposure | Tool descriptions | No new tools per spec |
