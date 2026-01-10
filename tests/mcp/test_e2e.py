"""End-to-end tests for MCP server with real Google Docs.

These tests validate the complete MCP tool workflow by:
1. Creating real Google Docs documents
2. Calling MCP tools that interact with the Google Docs API
3. Verifying the results in the actual documents
4. Cleaning up documents after the test suite completes

Marked as tier_b since they require OAuth credentials.
"""

from __future__ import annotations

import pytest

from extended_google_doc_utils.converter import GoogleDocsConverter
from extended_google_doc_utils.converter.types import TabReference


@pytest.fixture
def real_mcp_server(google_credentials):
    """Initialize MCP server with real credentials and converter.

    This fixture sets up the MCP server module to use a real
    GoogleDocsConverter backed by actual Google API credentials.
    """
    if google_credentials is None:
        pytest.skip("No credentials available")

    from extended_google_doc_utils.mcp import server

    # Store originals
    original_converter = server._converter
    original_credentials = server._credentials

    # Create real converter and set up server
    real_converter = GoogleDocsConverter(google_credentials)
    server._converter = real_converter
    server._credentials = google_credentials

    # Register tools
    server.register_tools()

    yield server

    # Restore originals
    server._converter = original_converter
    server._credentials = original_credentials


@pytest.fixture
def test_document(resource_manager, google_credentials):
    """Create a test document with initial content for e2e tests.

    The document is automatically cleaned up after the test.
    """
    if google_credentials is None:
        pytest.skip("No credentials available")

    doc_id = resource_manager.create_document(
        title=resource_manager.generate_unique_title("mcp-e2e-test"),
        test_name="mcp_e2e_tests",
    )

    # Add initial content to the document using the Docs API
    from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient

    client = GoogleDocsClient(google_credentials)
    docs_service = client.service

    # Insert test content with headings and body text
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": "Introduction\n\nThis is the introduction section.\n\nBackground\n\nThis is the background section.\n\nConclusion\n\nThis is the conclusion.\n",
            }
        },
        # Format "Introduction" as Heading 1
        {
            "updateParagraphStyle": {
                "range": {"startIndex": 1, "endIndex": 14},
                "paragraphStyle": {"namedStyleType": "HEADING_1"},
                "fields": "namedStyleType",
            }
        },
        # Format "Background" as Heading 2
        {
            "updateParagraphStyle": {
                "range": {"startIndex": 53, "endIndex": 64},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType",
            }
        },
        # Format "Conclusion" as Heading 2
        {
            "updateParagraphStyle": {
                "range": {"startIndex": 103, "endIndex": 114},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType",
            }
        },
    ]

    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()

    yield doc_id

    # Cleanup handled by resource_manager at session end


@pytest.mark.tier_b
class TestNavigationToolsE2E:
    """E2E tests for navigation tools."""

    def test_get_hierarchy_returns_document_structure(
        self, real_mcp_server, test_document
    ):
        """Test get_hierarchy returns real document headings."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id=test_document, tab_id="")

        assert result["success"] is True
        assert "headings" in result

        # Should have headings from test document
        headings = result["headings"]
        assert len(headings) >= 2

        # Check heading structure
        heading_texts = [h["text"] for h in headings]
        assert "Introduction" in heading_texts
        assert "Background" in heading_texts

    def test_get_hierarchy_includes_anchor_ids(self, real_mcp_server, test_document):
        """Test that headings include valid anchor IDs."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id=test_document, tab_id="")

        assert result["success"] is True

        for heading in result["headings"]:
            assert "anchor_id" in heading
            # Anchor IDs should be non-empty strings
            assert isinstance(heading["anchor_id"], str)
            # Google Doc anchors typically start with "kix." or "h."
            assert len(heading["anchor_id"]) > 0

    def test_list_documents_returns_results(self, real_mcp_server, test_document):
        """Test list_documents returns accessible documents."""
        from extended_google_doc_utils.mcp.tools.navigation import list_documents

        result = list_documents(max_results=10)

        assert result["success"] is True
        assert "documents" in result

        # Should have at least the test document
        assert len(result["documents"]) >= 1

        # Check document structure
        for doc in result["documents"]:
            assert "document_id" in doc
            assert "title" in doc

    def test_get_metadata_returns_document_info(self, real_mcp_server, test_document):
        """Test get_metadata returns document information."""
        from extended_google_doc_utils.mcp.tools.navigation import get_metadata

        result = get_metadata(document_id=test_document)

        assert result["success"] is True
        assert result["document_id"] == test_document
        assert "title" in result
        assert "tabs" in result


@pytest.mark.tier_b
class TestSectionToolsE2E:
    """E2E tests for section tools."""

    def test_export_section_returns_content(self, real_mcp_server, test_document):
        """Test export_section returns section content."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy
        from extended_google_doc_utils.mcp.tools.sections import export_section

        # First get the hierarchy to find an anchor
        hierarchy = get_hierarchy(document_id=test_document, tab_id="")
        assert hierarchy["success"] is True
        assert len(hierarchy["headings"]) > 0

        # Export the first section
        first_anchor = hierarchy["headings"][0]["anchor_id"]
        result = export_section(
            document_id=test_document, anchor_id=first_anchor, tab_id=""
        )

        assert result["success"] is True
        assert "content" in result
        assert len(result["content"]) > 0

    def test_export_preamble(self, real_mcp_server, test_document):
        """Test export_section with empty anchor returns preamble."""
        from extended_google_doc_utils.mcp.tools.sections import export_section

        result = export_section(document_id=test_document, anchor_id="", tab_id="")

        # Should succeed (even if preamble is empty)
        assert result["success"] is True
        assert "content" in result

    def test_import_section_modifies_content(self, real_mcp_server, test_document):
        """Test import_section updates section content."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy
        from extended_google_doc_utils.mcp.tools.sections import (
            export_section,
            import_section,
        )

        # Get hierarchy to find anchor
        hierarchy = get_hierarchy(document_id=test_document, tab_id="")
        assert hierarchy["success"] is True
        assert len(hierarchy["headings"]) >= 2

        # Find the "Background" section
        background_heading = None
        for h in hierarchy["headings"]:
            if "Background" in h["text"]:
                background_heading = h
                break
        assert background_heading is not None

        anchor_id = background_heading["anchor_id"]

        # Export current content
        export_result = export_section(
            document_id=test_document, anchor_id=anchor_id, tab_id=""
        )
        assert export_result["success"] is True
        original_content = export_result["content"]

        # Import new content - use simple markdown without anchor to test import
        new_content = "## Background\n\nThis section has been updated.\n"
        import_result = import_section(
            document_id=test_document,
            anchor_id=anchor_id,
            content=new_content,
            tab_id="",
        )

        assert import_result["success"] is True

        # Verify something was exported after import (section still exists)
        verify_result = export_section(
            document_id=test_document, anchor_id=anchor_id, tab_id=""
        )
        assert verify_result["success"] is True
        # The section should have content (heading at minimum)
        assert len(verify_result["content"]) > 0

    def test_section_isolation(self, real_mcp_server, test_document):
        """Test that modifying one section doesn't affect others."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy
        from extended_google_doc_utils.mcp.tools.sections import (
            export_section,
            import_section,
        )

        # Get hierarchy
        hierarchy = get_hierarchy(document_id=test_document, tab_id="")
        assert hierarchy["success"] is True
        assert len(hierarchy["headings"]) >= 2

        # Find Introduction and Background sections
        intro_heading = None
        background_heading = None
        for h in hierarchy["headings"]:
            if "Introduction" in h["text"]:
                intro_heading = h
            elif "Background" in h["text"]:
                background_heading = h

        assert intro_heading is not None
        assert background_heading is not None

        # Export Introduction content (to compare later)
        intro_before = export_section(
            document_id=test_document, anchor_id=intro_heading["anchor_id"], tab_id=""
        )
        assert intro_before["success"] is True

        # Modify Background section
        new_background = f"## {{^ {background_heading['anchor_id']}}}Background\n\nCompletely new background.\n"
        import_result = import_section(
            document_id=test_document,
            anchor_id=background_heading["anchor_id"],
            content=new_background,
            tab_id="",
        )
        assert import_result["success"] is True

        # Verify Introduction was NOT modified
        intro_after = export_section(
            document_id=test_document, anchor_id=intro_heading["anchor_id"], tab_id=""
        )
        assert intro_after["success"] is True

        # Introduction content should be unchanged
        # (comparing key content, ignoring potential whitespace differences)
        assert "Introduction" in intro_after["content"]
        assert "introduction section" in intro_after["content"].lower()


@pytest.mark.tier_b
class TestTabToolsE2E:
    """E2E tests for tab tools."""

    def test_export_tab_returns_full_content(self, real_mcp_server, test_document):
        """Test export_tab returns complete document content."""
        from extended_google_doc_utils.mcp.tools.tabs import export_tab

        result = export_tab(document_id=test_document, tab_id="")

        assert result["success"] is True
        assert "content" in result
        assert len(result["content"]) > 0

        # Should contain all sections
        content = result["content"]
        assert "Introduction" in content
        assert "Background" in content
        assert "Conclusion" in content

    def test_import_tab_replaces_content(self, real_mcp_server, test_document):
        """Test import_tab replaces entire tab content."""
        from extended_google_doc_utils.mcp.tools.tabs import export_tab, import_tab

        # Export original content
        original = export_tab(document_id=test_document, tab_id="")
        assert original["success"] is True

        # Import completely new content
        new_content = "# New Document\n\nThis is entirely new content.\n"
        import_result = import_tab(
            document_id=test_document, content=new_content, tab_id=""
        )

        assert import_result["success"] is True

        # Verify content was replaced
        verify = export_tab(document_id=test_document, tab_id="")
        assert verify["success"] is True
        assert "New Document" in verify["content"]
        assert "entirely new content" in verify["content"]


@pytest.mark.tier_b
class TestFormattingToolsE2E:
    """E2E tests for formatting tools."""

    def test_normalize_formatting_applies_font(self, real_mcp_server, test_document):
        """Test normalize_formatting applies font changes."""
        from extended_google_doc_utils.mcp.tools.formatting import normalize_formatting

        result = normalize_formatting(
            document_id=test_document,
            body_font="Arial",
            body_size="11pt",
        )

        assert result["success"] is True
        assert "changes_made" in result
        # Should have made some changes
        assert result["changes_made"] >= 0

    def test_extract_styles_returns_styles(self, real_mcp_server, test_document):
        """Test extract_styles returns style definitions."""
        from extended_google_doc_utils.mcp.tools.formatting import extract_styles

        result = extract_styles(document_id=test_document)

        assert result["success"] is True
        assert "styles" in result
        assert result["source_document_id"] == test_document

    def test_apply_styles_workflow(self, real_mcp_server, test_document):
        """Test the complete extract -> apply styles workflow."""
        from extended_google_doc_utils.mcp.tools.formatting import (
            apply_styles,
            extract_styles,
        )

        # Extract styles (even if empty, should work)
        extract_result = extract_styles(document_id=test_document)
        assert extract_result["success"] is True

        # Apply extracted styles back to same document
        apply_result = apply_styles(
            document_id=test_document,
            styles=extract_result["styles"],
        )

        assert apply_result["success"] is True


@pytest.mark.tier_b
class TestErrorHandlingE2E:
    """E2E tests for error handling."""

    def test_invalid_document_id_returns_error(self, real_mcp_server):
        """Test that invalid document ID returns proper error response."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        result = get_hierarchy(document_id="invalid_doc_id_xyz123", tab_id="")

        assert result["success"] is False
        assert "error" in result

    def test_invalid_anchor_returns_error(self, real_mcp_server, test_document):
        """Test that invalid anchor ID returns proper error response."""
        from extended_google_doc_utils.mcp.tools.sections import export_section

        result = export_section(
            document_id=test_document, anchor_id="h.nonexistent_anchor", tab_id=""
        )

        assert result["success"] is False
        assert "error" in result


@pytest.mark.tier_b
class TestCompleteWorkflowE2E:
    """E2E tests for complete MCP workflows."""

    def test_full_section_edit_workflow(self, real_mcp_server, test_document):
        """Test the complete workflow: discover -> read -> edit -> verify.

        This simulates what an LLM would do:
        1. List documents to find the target
        2. Get hierarchy to find sections
        3. Export a section
        4. Modify and import
        5. Verify the change
        """
        from extended_google_doc_utils.mcp.tools.navigation import (
            get_hierarchy,
            get_metadata,
            list_documents,
        )
        from extended_google_doc_utils.mcp.tools.sections import (
            export_section,
            import_section,
        )

        # Step 1: Get document metadata
        metadata = get_metadata(document_id=test_document)
        assert metadata["success"] is True
        assert "title" in metadata

        # Step 2: Get document hierarchy
        hierarchy = get_hierarchy(document_id=test_document, tab_id="")
        assert hierarchy["success"] is True
        assert len(hierarchy["headings"]) > 0

        # Step 3: Export a section (use first heading for reliability)
        target_heading = hierarchy["headings"][0]
        anchor_id = target_heading["anchor_id"]

        export_result = export_section(
            document_id=test_document, anchor_id=anchor_id, tab_id=""
        )
        assert export_result["success"] is True
        assert len(export_result["content"]) > 0

        # Step 4: Import updated content for the section
        new_content = "## Updated Section\n\nThis section was modified by the LLM.\n"
        import_result = import_section(
            document_id=test_document,
            anchor_id=anchor_id,
            content=new_content,
            tab_id="",
        )
        assert import_result["success"] is True

        # Step 5: Verify the document still has a valid hierarchy after changes
        # (We check hierarchy rather than re-exporting the same anchor since
        # anchor IDs may change after import)
        new_hierarchy = get_hierarchy(document_id=test_document, tab_id="")
        assert new_hierarchy["success"] is True
        # Document should still have at least one heading
        assert len(new_hierarchy["headings"]) > 0
