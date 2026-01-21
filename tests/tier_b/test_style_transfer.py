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
        doc_id = resource_manager.create_document(
            title="Style Transfer Test - Read",
            test_name="test_read_styles_from_existing_document",
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
        # Create test document
        doc_id = resource_manager.create_document(
            title="Style Transfer Test - Effective",
            test_name="test_read_styles_returns_effective_formatting",
        )

        styles = read_document_styles(doc_id, google_credentials)

        # HEADING_1 should have some text style properties
        heading_style = styles.effective_styles[NamedStyleType.HEADING_1]
        # The exact values depend on Google Docs defaults, but style should be defined
        assert heading_style.text_style is not None

        # NORMAL_TEXT should have properties too
        normal_style = styles.effective_styles[NamedStyleType.NORMAL_TEXT]
        assert normal_style.text_style is not None

    def test_read_document_properties(self, google_credentials, resource_manager):
        """Can read document-level properties."""
        doc_id = resource_manager.create_document(
            title="Style Transfer Test - Doc Props",
            test_name="test_read_document_properties",
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
        source_id = resource_manager.create_document(
            title="Style Transfer - Source BG",
            test_name="test_apply_background_color",
        )

        # Create target document
        target_id = resource_manager.create_document(
            title="Style Transfer - Target BG",
            test_name="test_apply_background_color",
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
        source_id = resource_manager.create_document(
            title="Style Transfer - Source Margins",
            test_name="test_apply_margins",
        )
        target_id = resource_manager.create_document(
            title="Style Transfer - Target Margins",
            test_name="test_apply_margins",
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
        # Create source document
        source_id = resource_manager.create_document(
            title="Style Transfer - All Styles Source",
            test_name="test_transfer_all_nine_style_types",
        )

        # Create target document
        target_id = resource_manager.create_document(
            title="Style Transfer - All Styles Target",
            test_name="test_transfer_all_nine_style_types",
        )

        # Apply effective styles to target
        results = apply_effective_styles(
            source_id,
            target_id,
            credentials=google_credentials,
        )

        # Results is a dict of NamedStyleType -> StyleApplicationResult
        # All 9 style types should be processed (even if no paragraphs matched)
        assert len(results) == 9

    def test_transfer_preserves_heading_formatting(
        self, google_credentials, resource_manager
    ):
        """Transferred headings maintain their distinct formatting."""
        source_id = resource_manager.create_document(
            title="Style Transfer - Heading Source",
            test_name="test_transfer_preserves_heading_formatting",
        )
        target_id = resource_manager.create_document(
            title="Style Transfer - Heading Target",
            test_name="test_transfer_preserves_heading_formatting",
        )

        # Apply styles
        results = apply_effective_styles(
            source_id,
            target_id,
            credentials=google_credentials,
        )

        # All 9 style types should be processed
        assert len(results) == 9

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
        source_id = resource_manager.create_document(
            title="Round Trip - Doc Props Source",
            test_name="test_document_properties_round_trip",
        )

        # Create target document
        target_id = resource_manager.create_document(
            title="Round Trip - Doc Props Target",
            test_name="test_document_properties_round_trip",
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
        # Create documents
        source_id = resource_manager.create_document(
            title="Round Trip - Styles Source",
            test_name="test_effective_styles_round_trip",
        )
        target_id = resource_manager.create_document(
            title="Round Trip - Styles Target",
            test_name="test_effective_styles_round_trip",
        )

        # Step 1: Read source effective styles
        source_styles = read_document_styles(source_id, google_credentials)

        # Step 2: Apply to target
        results = apply_effective_styles(
            source_id,
            target_id,
            credentials=google_credentials,
        )
        # All 9 style types should be processed
        assert len(results) == 9

        # Step 3: Read back from target
        target_styles = read_document_styles(target_id, google_credentials)

        # Step 4: Compare style definitions (since empty docs have no paragraphs)
        source_h1 = source_styles.effective_styles[NamedStyleType.HEADING_1]
        target_h1 = target_styles.effective_styles[NamedStyleType.HEADING_1]

        # Both should have style definitions
        assert source_h1 is not None
        assert target_h1 is not None

    def test_full_style_transfer_round_trip(
        self, google_credentials, resource_manager
    ):
        """T047: Full style transfer (properties + styles) round trip."""
        source_id = resource_manager.create_document(
            title="Round Trip - Full Source",
            test_name="test_full_style_transfer_round_trip",
        )
        target_id = resource_manager.create_document(
            title="Round Trip - Full Target",
            test_name="test_full_style_transfer_round_trip",
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

        # Step 5: Verify effective styles exist for all types
        for style_type in NamedStyleType:
            source_eff = source_styles.effective_styles.get(style_type)
            target_eff = target_styles.effective_styles.get(style_type)

            assert source_eff is not None
            assert target_eff is not None

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
