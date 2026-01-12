"""Tests for font catalog validation functions."""

import pytest

from extended_google_doc_utils.converter.font_catalog import (
    GOOGLE_DOCS_FONTS,
    detect_variant_name,
    extract_base_family,
    normalize_font_name,
    suggest_similar_fonts,
    validate_font_family,
    validate_font_weight,
)


class TestValidateFontFamily:
    """Tests for validate_font_family()."""

    def test_valid_font_accepted(self):
        """Valid font family is accepted."""
        result = validate_font_family("Roboto")
        assert result.is_valid
        assert result.canonical_name == "Roboto"
        assert result.error_code is None

    def test_font_case_insensitive(self):
        """Font names are matched case-insensitively."""
        result = validate_font_family("roboto")
        assert result.is_valid
        assert result.canonical_name == "Roboto"

        result = validate_font_family("ARIAL")
        assert result.is_valid
        assert result.canonical_name == "Arial"

        result = validate_font_family("times new roman")
        assert result.is_valid
        assert result.canonical_name == "Times New Roman"

    def test_invalid_font_rejected(self):
        """Invalid font family is rejected with suggestions."""
        result = validate_font_family("Helvetica")
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_FAMILY"
        assert "Helvetica" in result.error_message
        assert len(result.suggestions) > 0

    def test_variant_name_detected(self):
        """Variant names like 'Roboto Light' are detected."""
        result = validate_font_family("Roboto Light")
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_VARIANT"
        assert "Roboto" in result.suggestions
        assert "weight" in result.error_message.lower()

    def test_variant_name_bold(self):
        """Variant names with 'Bold' are detected."""
        result = validate_font_family("Roboto Bold")
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_VARIANT"
        assert "Roboto" in result.suggestions

    def test_variant_name_italic(self):
        """Variant names with 'Italic' are detected."""
        result = validate_font_family("Roboto Italic")
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_VARIANT"

    def test_unknown_variant_pattern(self):
        """Unknown base with variant pattern still suggests alternatives."""
        result = validate_font_family("Unknown Light")
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_VARIANT"
        assert len(result.suggestions) > 0


class TestValidateFontWeight:
    """Tests for validate_font_weight()."""

    def test_valid_weight_accepted(self):
        """Valid numeric weight is accepted."""
        result = validate_font_weight("Roboto", 300)
        assert result.is_valid
        assert result.canonical_name == "Roboto"
        assert result.normalized_weight == 300

    def test_named_weight_converted(self):
        """Named weights are converted to numeric values."""
        result = validate_font_weight("Roboto", "light")
        assert result.is_valid
        assert result.normalized_weight == 300

        result = validate_font_weight("Roboto", "bold")
        assert result.is_valid
        assert result.normalized_weight == 700

        result = validate_font_weight("Roboto", "thin")
        assert result.is_valid
        assert result.normalized_weight == 100

    def test_invalid_weight_rejected(self):
        """Unsupported weight for font is rejected."""
        # Arial only supports 400 and 700
        result = validate_font_weight("Arial", 300)
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_WEIGHT"
        assert "400" in result.suggestions
        assert "700" in result.suggestions

    def test_invalid_weight_number(self):
        """Weight not a multiple of 100 is rejected."""
        result = validate_font_weight("Roboto", 350)
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_WEIGHT"
        assert "300" in result.suggestions or "400" in result.suggestions

    def test_weight_out_of_range(self):
        """Weight outside 100-900 is rejected."""
        result = validate_font_weight("Roboto", 1000)
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_WEIGHT"

        result = validate_font_weight("Roboto", 50)
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_WEIGHT"

    def test_invalid_weight_name(self):
        """Unknown weight name is rejected."""
        result = validate_font_weight("Roboto", "ultrathick")
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_WEIGHT"

    def test_invalid_font_in_weight_validation(self):
        """Invalid font family is caught during weight validation."""
        result = validate_font_weight("FakeFont", 400)
        assert not result.is_valid
        assert result.error_code == "INVALID_FONT_FAMILY"


class TestNormalizeFontName:
    """Tests for normalize_font_name()."""

    def test_normalizes_lowercase(self):
        """Lowercase font name is normalized."""
        assert normalize_font_name("roboto") == "Roboto"
        assert normalize_font_name("arial") == "Arial"

    def test_normalizes_uppercase(self):
        """Uppercase font name is normalized."""
        assert normalize_font_name("ROBOTO") == "Roboto"

    def test_normalizes_multi_word(self):
        """Multi-word font names are normalized."""
        assert normalize_font_name("times new roman") == "Times New Roman"
        assert normalize_font_name("open sans") == "Open Sans"

    def test_returns_none_for_unknown(self):
        """Unknown font returns None."""
        assert normalize_font_name("Helvetica") is None
        assert normalize_font_name("FakeFont") is None


class TestSuggestSimilarFonts:
    """Tests for suggest_similar_fonts()."""

    def test_suggests_prefix_match(self):
        """Suggests fonts with matching prefix."""
        suggestions = suggest_similar_fonts("Rob")
        assert "Roboto" in suggestions or "Roboto Mono" in suggestions

    def test_suggests_partial_match(self):
        """Suggests fonts with partial word match."""
        suggestions = suggest_similar_fonts("Sans")
        assert any("Sans" in s for s in suggestions)

    def test_returns_defaults_for_no_match(self):
        """Returns default suggestions for completely unknown input."""
        suggestions = suggest_similar_fonts("ZZZZZ")
        assert len(suggestions) > 0
        assert "Arial" in suggestions

    def test_respects_limit(self):
        """Respects the limit parameter."""
        suggestions = suggest_similar_fonts("a", limit=2)
        assert len(suggestions) <= 2


class TestDetectVariantName:
    """Tests for detect_variant_name()."""

    def test_detects_light(self):
        """Detects 'Light' suffix."""
        assert detect_variant_name("Roboto Light") is True

    def test_detects_bold(self):
        """Detects 'Bold' suffix."""
        assert detect_variant_name("Arial Bold") is True

    def test_detects_italic(self):
        """Detects 'Italic' suffix."""
        assert detect_variant_name("Georgia Italic") is True

    def test_no_variant(self):
        """Returns False for plain font names."""
        assert detect_variant_name("Roboto") is False
        assert detect_variant_name("Arial") is False
        assert detect_variant_name("Open Sans") is False


class TestExtractBaseFamily:
    """Tests for extract_base_family()."""

    def test_extracts_roboto_light(self):
        """Extracts base family from 'Roboto Light'."""
        base, weight = extract_base_family("Roboto Light")
        assert base == "Roboto"
        assert weight == 300

    def test_extracts_arial_bold(self):
        """Extracts base family from 'Arial Bold'."""
        base, weight = extract_base_family("Arial Bold")
        assert base == "Arial"
        assert weight == 700

    def test_returns_none_for_unknown_base(self):
        """Returns None if base family is unknown."""
        base, weight = extract_base_family("FakeFont Light")
        assert base is None
        assert weight is None


class TestFontCatalogCoverage:
    """Tests for font catalog completeness."""

    def test_catalog_has_common_fonts(self):
        """Catalog includes commonly used fonts."""
        common_fonts = [
            "arial",
            "roboto",
            "times new roman",
            "georgia",
            "courier new",
            "open sans",
            "lato",
            "montserrat",
        ]
        for font in common_fonts:
            assert font in GOOGLE_DOCS_FONTS, f"Missing common font: {font}"

    def test_catalog_has_monospace_fonts(self):
        """Catalog includes monospace fonts."""
        monospace = [f for f in GOOGLE_DOCS_FONTS.values() if f.category == "monospace"]
        assert len(monospace) >= 3

    def test_catalog_entries_have_valid_weights(self):
        """All catalog entries have valid weight values."""
        for key, entry in GOOGLE_DOCS_FONTS.items():
            assert len(entry.weights) > 0, f"{key} has no weights"
            for w in entry.weights:
                assert 100 <= w <= 900, f"{key} has invalid weight {w}"
                assert w % 100 == 0, f"{key} has non-multiple weight {w}"

    def test_mono_shorthand_uses_courier_new(self):
        """The 'mono' shorthand uses Courier New (which is always valid)."""
        # This test validates our assumption that Courier New is in the catalog
        assert "courier new" in GOOGLE_DOCS_FONTS
        entry = GOOGLE_DOCS_FONTS["courier new"]
        assert entry.canonical_name == "Courier New"
        assert 400 in entry.weights
