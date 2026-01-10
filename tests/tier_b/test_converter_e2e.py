"""End-to-end tests for Google Docs to MEBDF converter.

These tests validate the converter against real Google Docs using the API.
Test document: https://docs.google.com/document/d/19LesxcFk6C72A6L5V8MCfOmf7RK975p5kuO4WM7kDmI/edit
"""

import pytest
from googleapiclient.errors import HttpError

from extended_google_doc_utils.converter import GoogleDocsConverter
from extended_google_doc_utils.converter.types import TabReference

# Test document ID
TEST_DOCUMENT_ID = "19LesxcFk6C72A6L5V8MCfOmf7RK975p5kuO4WM7kDmI"


@pytest.mark.tier_b
class TestGetHierarchyE2E:
    """E2E tests for hierarchy extraction."""

    def test_get_hierarchy_returns_headings(self, google_credentials):
        """Verify hierarchy extraction returns expected headings."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.get_hierarchy(tab_ref)

        # Should have headings
        assert len(result.headings) > 0
        # Should have multiple heading levels
        levels = {h.level for h in result.headings}
        assert len(levels) > 1

    def test_get_hierarchy_formatted_output(self, google_credentials):
        """Verify formatted hierarchy uses MEBDF syntax."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.get_hierarchy(tab_ref)

        # Formatted output should use MEBDF heading syntax
        assert "#" in result.markdown
        # Should have anchor markers
        assert "{^" in result.markdown

    def test_get_hierarchy_heading_levels(self, google_credentials):
        """Verify all heading levels are correctly identified."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.get_hierarchy(tab_ref)

        # Should have H1, H2, H3, H4 based on test document structure
        levels = sorted({h.level for h in result.headings})
        assert 1 in levels
        assert 2 in levels


@pytest.mark.tier_b
class TestExportE2E:
    """E2E tests for document export."""

    def test_export_tab_full_document(self, google_credentials):
        """Export entire document to MEBDF."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.export_tab(tab_ref)

        # Should have content
        assert result.content
        assert len(result.content) > 100

        # Should have headings in MEBDF format
        assert "# {^" in result.content

        # Should have anchors
        assert len(result.anchors) > 0

    def test_export_tab_preserves_formatting(self, google_credentials):
        """Export preserves text formatting."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.export_tab(tab_ref)

        # Should have some formatting markers (bold, italic, etc.)
        # The test document contains formatted text
        has_bold = "**" in result.content
        has_italic = "*" in result.content.replace("**", "")
        has_formatting = "{!" in result.content

        assert has_bold or has_italic or has_formatting

    def test_export_section_by_anchor(self, google_credentials):
        """Export specific section by heading anchor."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        # First get hierarchy to find an anchor
        hierarchy = converter.get_hierarchy(tab_ref)
        if not hierarchy.headings:
            pytest.skip("No headings in test document")

        first_heading = hierarchy.headings[0]

        # Export that section
        result = converter.export_section(tab_ref, first_heading.anchor_id)

        # Should have content
        assert result.content
        # Should have the heading's anchor
        assert first_heading.anchor_id in result.content


@pytest.mark.tier_b
class TestSectionExportE2E:
    """E2E tests for section-level export."""

    def test_export_preamble(self, google_credentials):
        """Export document preamble (content before first heading)."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        # Export preamble using empty anchor
        result = converter.export_section(tab_ref, "")

        # Preamble may or may not have content depending on document
        # Just verify it doesn't crash
        assert result is not None
        assert hasattr(result, "content")

    def test_export_subsection(self, google_credentials):
        """Export a subsection (H2 or lower)."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        # Find a subsection (H2 or lower)
        hierarchy = converter.get_hierarchy(tab_ref)
        subsections = [h for h in hierarchy.headings if h.level >= 2]

        if not subsections:
            pytest.skip("No subsections in test document")

        subsection = subsections[0]
        result = converter.export_section(tab_ref, subsection.anchor_id)

        assert result.content
        assert subsection.anchor_id in result.content


@pytest.mark.tier_b
class TestRoundTripE2E:
    """E2E tests for export round-trip consistency."""

    def test_export_produces_parseable_mebdf(self, google_credentials):
        """Exported MEBDF can be parsed back to AST."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.export_tab(tab_ref)
        parser = MebdfParser()

        # Should parse without errors
        doc = parser.parse(result.content)

        # Should have children
        assert len(doc.children) > 0

    def test_export_serialize_roundtrip(self, google_credentials):
        """Export -> Parse -> Serialize produces consistent output."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.converter.mebdf_serializer import MebdfSerializer

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.export_tab(tab_ref)

        parser = MebdfParser()
        serializer = MebdfSerializer()

        # Parse and re-serialize
        doc = parser.parse(result.content)
        output1 = serializer.serialize(doc)

        # Parse and serialize again
        doc2 = parser.parse(output1)
        output2 = serializer.serialize(doc2)

        # Should be semantically equivalent
        assert output1 == output2


@pytest.mark.tier_b
class TestImportE2E:
    """E2E tests for document import (read-only verification)."""

    def test_import_requests_structure(self, google_credentials):
        """Verify import request building from MEBDF content."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.converter.mebdf_to_gdoc import (
            build_import_requests,
        )
        from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient

        # First export the document
        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        result = converter.export_tab(tab_ref)

        # Parse to AST
        parser = MebdfParser()
        ast = parser.parse(result.content)

        # Get document for building requests
        client = GoogleDocsClient(google_credentials)
        document = client.get_document(TEST_DOCUMENT_ID)

        # Build import requests (don't execute them)
        body = document.get("body", {})
        requests, preserved, warnings = build_import_requests(
            document, body, "", ast, replace_all=True
        )

        # Should generate requests
        assert len(requests) > 0

        # Should have insert text request
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) > 0


@pytest.mark.tier_b
class TestEdgeCasesE2E:
    """E2E tests for edge cases."""

    def test_invalid_document_id(self, google_credentials):
        """Invalid document ID raises appropriate error."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id="invalid_document_id_xyz", tab_id="")

        with pytest.raises(HttpError) as exc_info:
            converter.get_hierarchy(tab_ref)

        # Should be 404 not found
        assert exc_info.value.resp.status == 404

    def test_nonexistent_anchor(self, google_credentials):
        """Nonexistent anchor ID returns appropriate result."""
        if google_credentials is None:
            pytest.skip("No credentials available")

        from extended_google_doc_utils.converter.exceptions import AnchorNotFoundError

        converter = GoogleDocsConverter(google_credentials)
        tab_ref = TabReference(document_id=TEST_DOCUMENT_ID, tab_id="")

        with pytest.raises(AnchorNotFoundError):
            converter.export_section(tab_ref, "h.nonexistent_anchor_xyz")
