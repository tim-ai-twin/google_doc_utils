# Data Model: Google Docs Font Validation

**Feature**: 128-gdoc-font-validation
**Date**: 2026-01-12

## Entity Definitions

### FontCatalogEntry

Represents a single font available in Google Docs.

```python
@dataclass
class FontCatalogEntry:
    """A font available in Google Docs with its supported weights."""

    canonical_name: str  # Exact casing for Google Docs API (e.g., "Roboto")
    weights: list[int]   # Supported weights (100-900), e.g., [100, 300, 400, 500, 700, 900]
    category: str        # Font category: "sans-serif", "serif", "monospace", "handwriting"
```

**Validation Rules**:
- `canonical_name`: Non-empty string
- `weights`: Non-empty list, all values in range 100-900, multiples of 100
- `category`: One of "sans-serif", "serif", "monospace", "handwriting"

### FontCatalog

The complete catalog of validated fonts.

```python
# Type alias
FontCatalog = dict[str, FontCatalogEntry]
# Keys are lowercase font names for case-insensitive lookup
# Example: {"roboto": FontCatalogEntry(canonical_name="Roboto", weights=[100,300,400,500,700,900], category="sans-serif")}
```

### FontValidationResult

Result of font/weight validation.

```python
@dataclass
class FontValidationResult:
    """Result of validating a font family and/or weight."""

    is_valid: bool
    canonical_name: str | None      # Normalized font name if valid
    normalized_weight: int | None   # Validated weight if valid
    error_code: str | None          # Error type if invalid
    error_message: str | None       # Human-readable error
    suggestions: list[str]          # Alternative fonts/weights if invalid
```

**Error Codes**:
- `INVALID_FONT_FAMILY`: Font name not in catalog
- `INVALID_FONT_WEIGHT`: Weight not supported by font
- `INVALID_FONT_VARIANT`: Variant name used as family (e.g., "Roboto Light")

### FontValidationError

Exception raised when font validation fails.

```python
class FontValidationError(Exception):
    """Raised when MEBDF content contains invalid font specification."""

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

## Font Catalog Data

### Default Google Docs Fonts

```python
GOOGLE_DOCS_FONTS: FontCatalog = {
    # Sans-serif fonts
    "arial": FontCatalogEntry("Arial", [400, 700], "sans-serif"),
    "arial black": FontCatalogEntry("Arial Black", [900], "sans-serif"),
    "comfortaa": FontCatalogEntry("Comfortaa", [300, 400, 500, 600, 700], "sans-serif"),
    "impact": FontCatalogEntry("Impact", [400], "sans-serif"),
    "lato": FontCatalogEntry("Lato", [100, 300, 400, 700, 900], "sans-serif"),
    "montserrat": FontCatalogEntry("Montserrat", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"),
    "noto sans": FontCatalogEntry("Noto Sans", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"),
    "nunito": FontCatalogEntry("Nunito", [200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"),
    "open sans": FontCatalogEntry("Open Sans", [300, 400, 500, 600, 700, 800], "sans-serif"),
    "oswald": FontCatalogEntry("Oswald", [200, 300, 400, 500, 600, 700], "sans-serif"),
    "pt sans": FontCatalogEntry("PT Sans", [400, 700], "sans-serif"),
    "raleway": FontCatalogEntry("Raleway", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"),
    "roboto": FontCatalogEntry("Roboto", [100, 300, 400, 500, 700, 900], "sans-serif"),
    "trebuchet ms": FontCatalogEntry("Trebuchet MS", [400, 700], "sans-serif"),
    "ubuntu": FontCatalogEntry("Ubuntu", [300, 400, 500, 700], "sans-serif"),
    "verdana": FontCatalogEntry("Verdana", [400, 700], "sans-serif"),
    "work sans": FontCatalogEntry("Work Sans", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"),

    # Serif fonts
    "georgia": FontCatalogEntry("Georgia", [400, 700], "serif"),
    "merriweather": FontCatalogEntry("Merriweather", [300, 400, 700, 900], "serif"),
    "playfair display": FontCatalogEntry("Playfair Display", [400, 500, 600, 700, 800, 900], "serif"),
    "pt serif": FontCatalogEntry("PT Serif", [400, 700], "serif"),
    "spectral": FontCatalogEntry("Spectral", [200, 300, 400, 500, 600, 700, 800], "serif"),
    "times new roman": FontCatalogEntry("Times New Roman", [400, 700], "serif"),

    # Monospace fonts
    "courier new": FontCatalogEntry("Courier New", [400, 700], "monospace"),
    "roboto mono": FontCatalogEntry("Roboto Mono", [100, 300, 400, 500, 700], "monospace"),
    "source code pro": FontCatalogEntry("Source Code Pro", [200, 300, 400, 500, 600, 700, 900], "monospace"),
    "ubuntu mono": FontCatalogEntry("Ubuntu Mono", [400, 700], "monospace"),

    # Handwriting fonts
    "caveat": FontCatalogEntry("Caveat", [400, 500, 600, 700], "handwriting"),
    "comic sans ms": FontCatalogEntry("Comic Sans MS", [400, 700], "handwriting"),
    "dancing script": FontCatalogEntry("Dancing Script", [400, 500, 600, 700], "handwriting"),
    "lobster": FontCatalogEntry("Lobster", [400], "handwriting"),
    "pacifico": FontCatalogEntry("Pacifico", [400], "handwriting"),
}
```

### Named Weight Mapping

```python
NAMED_FONT_WEIGHTS: dict[str, int] = {
    "thin": 100,
    "hairline": 100,
    "extralight": 200,
    "extra-light": 200,
    "ultralight": 200,
    "ultra-light": 200,
    "light": 300,
    "normal": 400,
    "regular": 400,
    "medium": 500,
    "semibold": 600,
    "semi-bold": 600,
    "demibold": 600,
    "demi-bold": 600,
    "bold": 700,
    "extrabold": 800,
    "extra-bold": 800,
    "ultrabold": 800,
    "ultra-bold": 800,
    "black": 900,
    "heavy": 900,
}
```

### Variant Name Detection

Common patterns that indicate a user tried to use a variant name as the font family:

```python
VARIANT_SUFFIXES = [
    "thin", "hairline",
    "extra light", "extralight", "ultra light", "ultralight",
    "light",
    "regular", "normal", "book",
    "medium",
    "semi bold", "semibold", "demi bold", "demibold",
    "bold",
    "extra bold", "extrabold", "ultra bold", "ultrabold",
    "black", "heavy",
    "italic", "oblique",
]
```

## State Transitions

N/A - Font validation is stateless. Each validation request is independent.

## Relationships

```
FontCatalog (1) ──contains──> (many) FontCatalogEntry
                                       │
                                       └──> weights: list[int]
                                       └──> category: str

FontValidationResult ──references──> FontCatalogEntry (if valid)
                     ──contains───> error details (if invalid)

FontValidationError ──raised by──> validate_font_family()
                                 ──> validate_font_weight()
```

## Usage Examples

### Validating a Font Family

```python
def validate_font_family(name: str) -> FontValidationResult:
    # Case-insensitive lookup
    entry = GOOGLE_DOCS_FONTS.get(name.lower())

    if entry:
        return FontValidationResult(
            is_valid=True,
            canonical_name=entry.canonical_name,
            normalized_weight=None,
            error_code=None,
            error_message=None,
            suggestions=[],
        )

    # Check if it looks like a variant name
    if detect_variant_name(name):
        base_family, _ = extract_base_family(name)
        return FontValidationResult(
            is_valid=False,
            error_code="INVALID_FONT_VARIANT",
            error_message=f"'{name}' appears to be a variant name. Use font family '{base_family}' with a weight property instead.",
            suggestions=[base_family],
        )

    # Unknown font
    return FontValidationResult(
        is_valid=False,
        error_code="INVALID_FONT_FAMILY",
        error_message=f"Font '{name}' is not available in Google Docs.",
        suggestions=suggest_similar_fonts(name),
    )
```

### Validating a Font Weight

```python
def validate_font_weight(family: str, weight: int) -> FontValidationResult:
    entry = GOOGLE_DOCS_FONTS.get(family.lower())

    if not entry:
        return FontValidationResult(
            is_valid=False,
            error_code="INVALID_FONT_FAMILY",
            error_message=f"Font '{family}' is not available.",
            suggestions=suggest_similar_fonts(family),
        )

    if weight in entry.weights:
        return FontValidationResult(
            is_valid=True,
            canonical_name=entry.canonical_name,
            normalized_weight=weight,
            error_code=None,
            error_message=None,
            suggestions=[],
        )

    # Weight not supported
    return FontValidationResult(
        is_valid=False,
        canonical_name=entry.canonical_name,
        error_code="INVALID_FONT_WEIGHT",
        error_message=f"Font '{entry.canonical_name}' does not support weight {weight}. Supported: {entry.weights}",
        suggestions=[str(w) for w in entry.weights],
    )
```
