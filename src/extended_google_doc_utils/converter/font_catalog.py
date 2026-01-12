"""Google Docs font catalog and validation.

This module provides:
- GOOGLE_DOCS_FONTS: Catalog of available fonts and weights
- validate_font_family(): Validate font names
- validate_font_weight(): Validate weight for a font
- normalize_font_name(): Case-insensitive name lookup
- suggest_similar_fonts(): Suggest alternatives for invalid fonts
"""

from __future__ import annotations

from dataclasses import dataclass, field


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FontCatalogEntry:
    """A font available in Google Docs with its supported weights.

    Attributes:
        canonical_name: Exact casing for Google Docs API (e.g., "Roboto")
        weights: Supported weights (100-900), e.g., [100, 300, 400, 500, 700, 900]
        category: Font category: "sans-serif", "serif", "monospace", "handwriting"
    """

    canonical_name: str
    weights: list[int]
    category: str


@dataclass
class FontValidationResult:
    """Result of validating a font family and/or weight.

    Attributes:
        is_valid: True if validation passed
        canonical_name: Normalized font name if valid
        normalized_weight: Validated weight if valid
        error_code: Error type if invalid
        error_message: Human-readable error if invalid
        suggestions: Alternative fonts/weights if invalid
    """

    is_valid: bool
    canonical_name: str | None = None
    normalized_weight: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    suggestions: list[str] = field(default_factory=list)


# =============================================================================
# Font Catalog Data
# =============================================================================

# Default Google Docs fonts with their supported weights
GOOGLE_DOCS_FONTS: dict[str, FontCatalogEntry] = {
    # Sans-serif fonts
    "arial": FontCatalogEntry("Arial", [400, 700], "sans-serif"),
    "arial black": FontCatalogEntry("Arial Black", [900], "sans-serif"),
    "comfortaa": FontCatalogEntry("Comfortaa", [300, 400, 500, 600, 700], "sans-serif"),
    "impact": FontCatalogEntry("Impact", [400], "sans-serif"),
    "lato": FontCatalogEntry("Lato", [100, 300, 400, 700, 900], "sans-serif"),
    "montserrat": FontCatalogEntry(
        "Montserrat", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"
    ),
    "noto sans": FontCatalogEntry(
        "Noto Sans", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"
    ),
    "nunito": FontCatalogEntry(
        "Nunito", [200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"
    ),
    "open sans": FontCatalogEntry(
        "Open Sans", [300, 400, 500, 600, 700, 800], "sans-serif"
    ),
    "oswald": FontCatalogEntry("Oswald", [200, 300, 400, 500, 600, 700], "sans-serif"),
    "pt sans": FontCatalogEntry("PT Sans", [400, 700], "sans-serif"),
    "raleway": FontCatalogEntry(
        "Raleway", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"
    ),
    "roboto": FontCatalogEntry("Roboto", [100, 300, 400, 500, 700, 900], "sans-serif"),
    "trebuchet ms": FontCatalogEntry("Trebuchet MS", [400, 700], "sans-serif"),
    "ubuntu": FontCatalogEntry("Ubuntu", [300, 400, 500, 700], "sans-serif"),
    "verdana": FontCatalogEntry("Verdana", [400, 700], "sans-serif"),
    "work sans": FontCatalogEntry(
        "Work Sans", [100, 200, 300, 400, 500, 600, 700, 800, 900], "sans-serif"
    ),
    # Serif fonts
    "georgia": FontCatalogEntry("Georgia", [400, 700], "serif"),
    "merriweather": FontCatalogEntry("Merriweather", [300, 400, 700, 900], "serif"),
    "playfair display": FontCatalogEntry(
        "Playfair Display", [400, 500, 600, 700, 800, 900], "serif"
    ),
    "pt serif": FontCatalogEntry("PT Serif", [400, 700], "serif"),
    "spectral": FontCatalogEntry(
        "Spectral", [200, 300, 400, 500, 600, 700, 800], "serif"
    ),
    "times new roman": FontCatalogEntry("Times New Roman", [400, 700], "serif"),
    # Monospace fonts
    "courier new": FontCatalogEntry("Courier New", [400, 700], "monospace"),
    "roboto mono": FontCatalogEntry("Roboto Mono", [100, 300, 400, 500, 700], "monospace"),
    "source code pro": FontCatalogEntry(
        "Source Code Pro", [200, 300, 400, 500, 600, 700, 900], "monospace"
    ),
    "ubuntu mono": FontCatalogEntry("Ubuntu Mono", [400, 700], "monospace"),
    # Handwriting fonts
    "caveat": FontCatalogEntry("Caveat", [400, 500, 600, 700], "handwriting"),
    "comic sans ms": FontCatalogEntry("Comic Sans MS", [400, 700], "handwriting"),
    "dancing script": FontCatalogEntry(
        "Dancing Script", [400, 500, 600, 700], "handwriting"
    ),
    "lobster": FontCatalogEntry("Lobster", [400], "handwriting"),
    "pacifico": FontCatalogEntry("Pacifico", [400], "handwriting"),
}

# Named weight mapping (used by parse_font_weight in mebdf_to_gdoc.py)
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

# Variant suffixes that indicate user tried variant name as font family
VARIANT_SUFFIXES = [
    "thin",
    "hairline",
    "extra light",
    "extralight",
    "ultra light",
    "ultralight",
    "light",
    "regular",
    "normal",
    "book",
    "medium",
    "semi bold",
    "semibold",
    "demi bold",
    "demibold",
    "bold",
    "extra bold",
    "extrabold",
    "ultra bold",
    "ultrabold",
    "black",
    "heavy",
    "italic",
    "oblique",
]


# =============================================================================
# Helper Functions
# =============================================================================


def normalize_font_name(name: str) -> str | None:
    """Normalize font name to canonical casing.

    Args:
        name: Font name in any casing

    Returns:
        Canonical font name, or None if not found
    """
    entry = GOOGLE_DOCS_FONTS.get(name.lower())
    return entry.canonical_name if entry else None


def detect_variant_name(name: str) -> bool:
    """Check if a font name looks like a variant name (e.g., "Roboto Light").

    Args:
        name: Font name to check

    Returns:
        True if it appears to be a variant name
    """
    name_lower = name.lower()
    for suffix in VARIANT_SUFFIXES:
        if name_lower.endswith(" " + suffix):
            return True
    return False


def extract_base_family(variant_name: str) -> tuple[str | None, int | None]:
    """Extract base font family and weight from a variant name.

    Args:
        variant_name: A variant name like "Roboto Light"

    Returns:
        Tuple of (base_family_canonical, weight) or (None, None) if not recognized
    """
    name_lower = variant_name.lower()

    for suffix in VARIANT_SUFFIXES:
        if name_lower.endswith(" " + suffix):
            base = variant_name[: -(len(suffix) + 1)]  # Remove " suffix"
            # Try to find the base family
            canonical = normalize_font_name(base)
            if canonical:
                # Map suffix to weight
                weight = NAMED_FONT_WEIGHTS.get(suffix.replace(" ", ""))
                return canonical, weight

    return None, None


def suggest_similar_fonts(invalid_name: str, limit: int = 3) -> list[str]:
    """Suggest similar valid fonts for an invalid font name.

    Uses prefix matching and common character overlap to find similar fonts.

    Args:
        invalid_name: The invalid font name
        limit: Maximum suggestions to return

    Returns:
        List of valid font names sorted by similarity
    """
    invalid_lower = invalid_name.lower()
    suggestions = []

    # First, try prefix matching
    for key, entry in GOOGLE_DOCS_FONTS.items():
        if key.startswith(invalid_lower) or invalid_lower.startswith(key):
            suggestions.append((entry.canonical_name, 0))  # High priority

    # Then, try partial word matching
    invalid_words = set(invalid_lower.split())
    for key, entry in GOOGLE_DOCS_FONTS.items():
        if entry.canonical_name in [s[0] for s in suggestions]:
            continue
        key_words = set(key.split())
        overlap = len(invalid_words & key_words)
        if overlap > 0:
            suggestions.append((entry.canonical_name, 1))  # Medium priority

    # If still no suggestions, return some common defaults
    if not suggestions:
        return ["Arial", "Roboto", "Open Sans"][:limit]

    # Sort by priority and return unique names
    suggestions.sort(key=lambda x: x[1])
    seen = set()
    result = []
    for name, _ in suggestions:
        if name not in seen:
            seen.add(name)
            result.append(name)
        if len(result) >= limit:
            break

    return result


# =============================================================================
# Validation Functions
# =============================================================================


def validate_font_family(name: str) -> FontValidationResult:
    """Validate a font family name against the Google Docs font catalog.

    Args:
        name: Font family name to validate (case-insensitive)

    Returns:
        FontValidationResult with validation status and details
    """
    # Case-insensitive lookup
    entry = GOOGLE_DOCS_FONTS.get(name.lower())

    if entry:
        return FontValidationResult(
            is_valid=True,
            canonical_name=entry.canonical_name,
        )

    # Check if it looks like a variant name (e.g., "Roboto Light")
    if detect_variant_name(name):
        base_family, weight = extract_base_family(name)
        if base_family:
            weight_hint = f" with weight:{weight}" if weight else ""
            return FontValidationResult(
                is_valid=False,
                error_code="INVALID_FONT_VARIANT",
                error_message=(
                    f"'{name}' appears to be a variant name. "
                    f"Use font family '{base_family}'{weight_hint} instead."
                ),
                suggestions=[base_family],
            )
        else:
            # Variant pattern but base not recognized
            return FontValidationResult(
                is_valid=False,
                error_code="INVALID_FONT_VARIANT",
                error_message=(
                    f"'{name}' appears to be a variant name. "
                    "Specify font family and weight separately: {!font:FontName, weight:300}"
                ),
                suggestions=suggest_similar_fonts(name),
            )

    # Unknown font
    return FontValidationResult(
        is_valid=False,
        error_code="INVALID_FONT_FAMILY",
        error_message=f"Font '{name}' is not available in Google Docs.",
        suggestions=suggest_similar_fonts(name),
    )


def validate_font_weight(family: str, weight: int | str) -> FontValidationResult:
    """Validate a font weight for a given font family.

    Args:
        family: Font family name (will be normalized)
        weight: Weight as int (100-900) or named string ("bold", "light")

    Returns:
        FontValidationResult with validation status and details
    """
    # Normalize weight to int
    if isinstance(weight, str):
        weight_int = NAMED_FONT_WEIGHTS.get(weight.lower().replace(" ", ""))
        if weight_int is None:
            # Try parsing as int
            try:
                weight_int = int(weight)
            except ValueError:
                return FontValidationResult(
                    is_valid=False,
                    error_code="INVALID_FONT_WEIGHT",
                    error_message=(
                        f"'{weight}' is not a valid weight. "
                        "Use 100-900 or: thin, light, normal, medium, bold, black"
                    ),
                    suggestions=["400", "700"],
                )
    else:
        weight_int = weight

    # Validate weight is in valid range
    if not (100 <= weight_int <= 900):
        return FontValidationResult(
            is_valid=False,
            error_code="INVALID_FONT_WEIGHT",
            error_message=f"Weight {weight_int} is out of range. Valid range is 100-900.",
            suggestions=["400", "700"],
        )

    # Validate weight is multiple of 100
    if weight_int % 100 != 0:
        nearest = round(weight_int / 100) * 100
        return FontValidationResult(
            is_valid=False,
            error_code="INVALID_FONT_WEIGHT",
            error_message=(
                f"Weight {weight_int} is not valid. "
                f"Font weights must be multiples of 100. Did you mean {nearest}?"
            ),
            suggestions=[str(nearest)],
        )

    # Look up font family
    entry = GOOGLE_DOCS_FONTS.get(family.lower())

    if not entry:
        return FontValidationResult(
            is_valid=False,
            error_code="INVALID_FONT_FAMILY",
            error_message=f"Font '{family}' is not available in Google Docs.",
            suggestions=suggest_similar_fonts(family),
        )

    # Check if weight is supported
    if weight_int in entry.weights:
        return FontValidationResult(
            is_valid=True,
            canonical_name=entry.canonical_name,
            normalized_weight=weight_int,
        )

    # Weight not supported for this font
    weight_names = {
        100: "thin",
        200: "extra-light",
        300: "light",
        400: "normal",
        500: "medium",
        600: "semi-bold",
        700: "bold",
        800: "extra-bold",
        900: "black",
    }
    supported_desc = ", ".join(
        f"{w} ({weight_names.get(w, '')})" for w in entry.weights
    )

    return FontValidationResult(
        is_valid=False,
        canonical_name=entry.canonical_name,
        error_code="INVALID_FONT_WEIGHT",
        error_message=(
            f"Font '{entry.canonical_name}' does not support weight {weight_int}. "
            f"Supported weights: {supported_desc}"
        ),
        suggestions=[str(w) for w in entry.weights],
    )
