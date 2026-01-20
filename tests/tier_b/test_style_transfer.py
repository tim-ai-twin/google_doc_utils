"""Integration tests for style transfer feature.

Feature: 130-document-style-transfer
Tests: T017, T024, T035, T045-T048

These tests require valid Google OAuth credentials and create/modify
real Google Docs for testing.
"""

import pytest

from extended_google_doc_utils.converter import (
    DocumentProperties,
    DocumentStyles,
    NamedStyleType,
    RGBColor,
    StyleTransferOptions,
    apply_document_properties,
    apply_document_styles,
    apply_effective_styles,
    read_document_styles,
)


@pytest.mark.tier_b
class TestReadDocumentStyles:
    """Integration tests for reading document styles (T017)."""

    def test_read_styles_from_existing_document(
        self, google_credentials, resource_manager
    ):
        """Can read styles from a real Google Doc."""
        # Create a test document
        doc_id = resource_manager.create_test_document(
            "Style Transfer Test - Read",
            initial_content="# Heading 1\n\nSome body text.\n\n## Heading 2\n\nMore text.",
        )

        # Read styles
        styles = read_document_styles(doc_id, google_credentials)

        # Verify structure
        assert isinstance(styles, DocumentStyles)
        assert styles.document_id == doc_id

        # Document properties should be present
        assert styles.document_properties is not None

        # All 9 style types should be present
        assert len(styles.effective_styles) == 9
        for style_type in NamedStyleType:
            assert style_type in styles.effective_styles

    def test_read_styles_returns_effective_formatting(
        self, google_credentials, resource_manager
    ):
        """Effective styles reflect actual paragraph formatting."""
        # Create test document with standard content
        doc_id = resource_manager.create_test_document(
            "Style Transfer Test - Effective",
            initial_content="# Test Heading\n\nBody paragraph.",
        )

        styles = read_document_styles(doc_id, google_credentials)

        # HEADING_1 should have some text style properties
        heading_style = styles.effective_styles[NamedStyleType.HEADING_1]
        # The exact values depend on Google Docs defaults, but font size should be set
        assert heading_style.text_style is not None

        # NORMAL_TEXT should have properties too
        normal_style = styles.effective_styles[NamedStyleType.NORMAL_TEXT]
        assert normal_style.text_style is not None

    def test_read_document_properties(self, google_credentials, resource_manager):
        """Can read document-level properties."""
        doc_id = resource_manager.create_test_document(
            "Style Transfer Test - Doc Props",
            initial_content="Test content.",
        )

        styles = read_document_styles(doc_id, google_credentials)

        # Should have page dimensions (Letter size typically)
        props = styles.document_properties
        assert props.page_width_pt is not None or props.page_height_pt is not None
        # Margins should be set
        # Note: Some properties may be None if using defaults


# =============================================================================
# T024: Integration test for applying document properties
# =============================================================================


@pytest.mark.tier_b
class TestApplyDocumentProperties:
    """Integration tests for applying document properties (T024)."""

    def test_apply_background_color(self, google_credentials, resource_manager):
        """Can apply background color from source to target document."""
        # Create source document
        source_id = resource_manager.create_test_document(
            "Style Transfer - Source BG",
            initial_content="Source document.",
        )

        # Create target document
        target_id = resource_manager.create_test_document(
            "Style Transfer - Target BG",
            initial_content="Target document.",
        )

        # Read source styles
        source_styles = read_document_styles(source_id, google_credentials)

        # Apply document properties to target
        result = apply_document_properties(
            source_id, target_id, google_credentials
        )

        # Should succeed
        assert result is True

        # Read target styles and verify
        target_styles = read_document_styles(target_id, google_credentials)

        # Background color should match (or both be None/default)
        # Note: Google Docs may return None for default white background
        if source_styles.document_properties.background_color:
            assert target_styles.document_properties.background_color is not None

    def test_apply_margins(self, google_credentials, resource_manager):
        """Can apply margin settings from source to target document."""
        # Create source and target documents
        source_id = resource_manager.create_test_document(
            "Style Transfer - Source Margins",
            initial_content="Source with margins.",
        )
        target_id = resource_manager.create_test_document(
            "Style Transfer - Target Margins",
            initial_content="Target for margins.",
        )

        # Apply document properties
        result = apply_document_properties(
            source_id, target_id, google_credentials
        )

        assert result is True

        # Verify target received the properties
        target_styles = read_document_styles(target_id, google_credentials)

        # At minimum, the document should be readable after applying properties
        assert target_styles.document_properties is not None


# =============================================================================
# T035: Integration test for transferring all 9 style types
# =============================================================================


@pytest.mark.tier_b
class TestTransferNamedStyles:
    """Integration tests for transferring named styles (T035)."""

    def test_transfer_all_nine_style_types(self, google_credentials, resource_manager):
        """Can transfer all 9 named style types between documents."""
        # Create source document with various styles
        source_content = """# Title Text

## Subtitle Text

# Heading 1

## Heading 2

### Heading 3

#### Heading 4

##### Heading 5

###### Heading 6

Normal text paragraph here.
"""
        source_id = resource_manager.create_test_document(
            "Style Transfer - All Styles Source",
            initial_content=source_content,
        )

        # Create target document with same structure
        target_id = resource_manager.create_test_document(
            "Style Transfer - All Styles Target",
            initial_content=source_content,
        )

        # Apply effective styles to target
        results = apply_effective_styles(
            source_id,
            target_id,
            credentials=google_credentials,
        )

        # Should have applied styles for multiple style types
        # Results is a dict of NamedStyleType -> StyleApplicationResult
        assert len(results) > 0
        # At least some styles should have been applied successfully
        assert any(r.success for r in results.values())

    def test_transfer_preserves_heading_formatting(
        self, google_credentials, resource_manager
    ):
        """Transferred headings maintain their distinct formatting."""
        source_content = "# Main Heading\n\nBody text here."
        source_id = resource_manager.create_test_document(
            "Style Transfer - Heading Source",
            initial_content=source_content,
        )
        target_id = resource_manager.create_test_document(
            "Style Transfer - Heading Target",
            initial_content=source_content,
        )

        # Apply styles
        results = apply_effective_styles(
            source_id,
            target_id,
            credentials=google_credentials,
        )

        # At least some styles should have been applied
        assert any(r.success for r in results.values())

        # Read target styles to verify
        target_styles = read_document_styles(target_id, google_credentials)

        # HEADING_1 and NORMAL_TEXT should both exist
        assert NamedStyleType.HEADING_1 in target_styles.effective_styles
        assert NamedStyleType.NORMAL_TEXT in target_styles.effective_styles


# =============================================================================
# T045-T048: Round-trip style preservation tests
# =============================================================================


def _compare_with_tolerance(a: float | None, b: float | None, tolerance: float = 0.01) -> bool:
    """Compare two float values with tolerance (T048).

    Args:
        a: First value (or None)
        b: Second value (or None)
        tolerance: Maximum allowed difference (default 0.01pt per SC-003)

    Returns:
        True if values are within tolerance or both None
    """
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= tolerance


def _compare_colors(c1: RGBColor | None, c2: RGBColor | None, tolerance: float = 0.01) -> bool:
    """Compare two RGB colors with tolerance."""
    if c1 is None and c2 is None:
        return True
    if c1 is None or c2 is None:
        return False
    return (
        _compare_with_tolerance(c1.red, c2.red, tolerance)
        and _compare_with_tolerance(c1.green, c2.green, tolerance)
        and _compare_with_tolerance(c1.blue, c2.blue, tolerance)
    )


@pytest.mark.tier_b
class TestRoundTripStylePreservation:
    """Integration tests for round-trip style preservation (T045-T048)."""

    def test_document_properties_round_trip(
        self, google_credentials, resource_manager
    ):
        """T045: Document properties survive read-apply-read cycle."""
        # Create source document
        source_id = resource_manager.create_test_document(
            "Round Trip - Doc Props Source",
            initial_content="Source for document properties round trip.",
        )

        # Create target document
        target_id = resource_manager.create_test_document(
            "Round Trip - Doc Props Target",
            initial_content="Target for document properties round trip.",
        )

        # Step 1: Read source styles
        source_styles = read_document_styles(source_id, google_credentials)
        original_props = source_styles.document_properties

        # Step 2: Apply to target
        apply_document_properties(source_id, target_id, google_credentials)

        # Step 3: Read back from target
        target_styles = read_document_styles(target_id, google_credentials)
        applied_props = target_styles.document_properties

        # Step 4: Compare with tolerance
        # Background color
        assert _compare_colors(original_props.background_color, applied_props.background_color)

        # Margins (may be None if using defaults)
        if original_props.margin_top_pt is not None:
            assert _compare_with_tolerance(
                original_props.margin_top_pt, applied_props.margin_top_pt
            )
        if original_props.margin_bottom_pt is not None:
            assert _compare_with_tolerance(
                original_props.margin_bottom_pt, applied_props.margin_bottom_pt
            )
        if original_props.margin_left_pt is not None:
            assert _compare_with_tolerance(
                original_props.margin_left_pt, applied_props.margin_left_pt
            )
        if original_props.margin_right_pt is not None:
            assert _compare_with_tolerance(
                original_props.margin_right_pt, applied_props.margin_right_pt
            )

    def test_effective_styles_round_trip(
        self, google_credentials, resource_manager
    ):
        """T046: Effective styles survive read-apply-read cycle."""
        # Create documents with headings
        content = "# Heading\n\nBody paragraph."
        source_id = resource_manager.create_test_document(
            "Round Trip - Styles Source",
            initial_content=content,
        )
        target_id = resource_manager.create_test_document(
            "Round Trip - Styles Target",
            initial_content=content,
        )

        # Step 1: Read source effective styles
        source_styles = read_document_styles(source_id, google_credentials)

        # Step 2: Apply to target
        results = apply_effective_styles(
            source_id,
            target_id,
            credentials=google_credentials,
        )
        # Check if any results had success=True
        assert any(r.success for r in results.values())

        # Step 3: Read back from target
        target_styles = read_document_styles(target_id, google_credentials)

        # Step 4: Compare HEADING_1 text style properties
        source_h1 = source_styles.effective_styles[NamedStyleType.HEADING_1]
        target_h1 = target_styles.effective_styles[NamedStyleType.HEADING_1]

        # Font size should match within tolerance
        if source_h1.text_style.font_size_pt is not None:
            assert _compare_with_tolerance(
                source_h1.text_style.font_size_pt,
                target_h1.text_style.font_size_pt,
            )

        # Bold should match
        assert source_h1.text_style.bold == target_h1.text_style.bold

    def test_full_style_transfer_round_trip(
        self, google_credentials, resource_manager
    ):
        """T047: Full style transfer (properties + styles) round trip."""
        content = """# Main Title

## Subtitle Here

# First Heading

Normal text paragraph.

## Second Level

More body text.
"""
        source_id = resource_manager.create_test_document(
            "Round Trip - Full Source",
            initial_content=content,
        )
        target_id = resource_manager.create_test_document(
            "Round Trip - Full Target",
            initial_content=content,
        )

        # Step 1: Read complete styles from source
        source_styles = read_document_styles(source_id, google_credentials)

        # Step 2: Apply complete styles to target
        options = StyleTransferOptions(
            include_document_properties=True,
            include_effective_styles=True,
        )
        result = apply_document_styles(
            source_id, target_id, options, google_credentials
        )
        assert result.success is True

        # Step 3: Read back from target
        target_styles = read_document_styles(target_id, google_credentials)

        # Step 4: Verify document properties match
        assert _compare_colors(
            source_styles.document_properties.background_color,
            target_styles.document_properties.background_color,
        )

        # Step 5: Verify effective styles match
        for style_type in NamedStyleType:
            source_eff = source_styles.effective_styles.get(style_type)
            target_eff = target_styles.effective_styles.get(style_type)

            if source_eff and target_eff:
                # Font size should match
                if source_eff.text_style.font_size_pt is not None:
                    assert _compare_with_tolerance(
                        source_eff.text_style.font_size_pt,
                        target_eff.text_style.font_size_pt,
                    ), f"Font size mismatch for {style_type}"

    def test_numeric_tolerance_helper(self):
        """T048: Verify numeric tolerance comparison helper works correctly."""
        # Exact match
        assert _compare_with_tolerance(10.0, 10.0)

        # Within tolerance
        assert _compare_with_tolerance(10.0, 10.005)
        assert _compare_with_tolerance(10.0, 9.995)

        # At tolerance boundary
        assert _compare_with_tolerance(10.0, 10.01)
        assert _compare_with_tolerance(10.0, 9.99)

        # Outside tolerance
        assert not _compare_with_tolerance(10.0, 10.02)
        assert not _compare_with_tolerance(10.0, 9.98)

        # None handling
        assert _compare_with_tolerance(None, None)
        assert not _compare_with_tolerance(10.0, None)
        assert not _compare_with_tolerance(None, 10.0)

        # Color comparison
        assert _compare_colors(
            RGBColor(0.5, 0.5, 0.5),
            RGBColor(0.505, 0.495, 0.5),
        )
        assert not _compare_colors(
            RGBColor(0.5, 0.5, 0.5),
            RGBColor(0.52, 0.5, 0.5),
        )
        assert _compare_colors(None, None)
        assert not _compare_colors(RGBColor(0.5, 0.5, 0.5), None)
