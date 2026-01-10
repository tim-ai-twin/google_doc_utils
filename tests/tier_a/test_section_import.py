"""Unit tests for section import functionality.

Tests cover:
- Section replacement strategy
- Preamble replacement
- Boundary preservation
"""


from extended_google_doc_utils.converter.mebdf_parser import (
    DocumentNode,
    HeadingNode,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.mebdf_to_gdoc import (
    build_section_import_requests,
)
from extended_google_doc_utils.converter.types import Section


class TestBuildSectionImportRequests:
    """Tests for section import request building."""

    def test_section_delete_range(self):
        """Section import deletes the section content."""
        document = {}
        body = {"content": []}
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=50)
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New content")])]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Should have delete request for section range
        delete_requests = [r for r in requests if "deleteContentRange" in r]
        assert len(delete_requests) == 1

        delete_range = delete_requests[0]["deleteContentRange"]["range"]
        assert delete_range["startIndex"] == 10
        assert delete_range["endIndex"] == 49  # end - 1 to preserve newline

    def test_section_insert_at_start(self):
        """Section import inserts at section start."""
        document = {}
        body = {"content": []}
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=50)
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New content")])]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Should have insert request at section start
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) == 1
        assert insert_requests[0]["insertText"]["location"]["index"] == 10

    def test_preamble_replacement(self):
        """Preamble replacement works correctly."""
        document = {}
        body = {"content": []}
        section = Section(anchor_id="", level=0, start_index=1, end_index=20)
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New preamble")])]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Should have delete and insert requests
        assert any("deleteContentRange" in r for r in requests)
        assert any("insertText" in r for r in requests)

    def test_preserves_embedded_objects(self):
        """Section import preserves embedded objects in available list."""
        document = {
            "inlineObjects": {
                "img_001": {
                    "inlineObjectProperties": {
                        "embeddedObject": {"imageProperties": {}}
                    }
                }
            }
        }
        body = {"content": []}
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=50)

        from extended_google_doc_utils.converter.mebdf_parser import EmbeddedObjectNode

        ast = DocumentNode(
            children=[
                ParagraphNode(content=[TextNode("Text with image:")]),
                EmbeddedObjectNode(object_id="img_001", object_type="image"),
            ]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        assert "img_001" in preserved

    def test_heading_style_preserved(self):
        """Section import applies heading styles."""
        document = {}
        body = {"content": []}
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=50)
        ast = DocumentNode(
            children=[
                HeadingNode(level=2, anchor_id="h.test", content=[TextNode("Heading")])
            ]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Should have paragraph style request for heading
        style_requests = [r for r in requests if "updateParagraphStyle" in r]
        assert len(style_requests) >= 1

    def test_empty_section(self):
        """Handle empty section (start == end - 1)."""
        document = {}
        body = {"content": []}
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=11)
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New content")])]
        )

        # Should not crash
        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Should still have insert request
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) == 1


class TestSectionBoundaryPreservation:
    """Tests verifying surrounding content is preserved."""

    def test_content_before_preserved(self):
        """Content before section is not deleted."""
        document = {}
        body = {
            "content": [
                {"startIndex": 1, "endIndex": 10},  # Before section
                {"startIndex": 10, "endIndex": 50},  # Section content
            ]
        }
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=50)
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New")])]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Delete range should start at section start, not document start
        delete_requests = [r for r in requests if "deleteContentRange" in r]
        if delete_requests:
            delete_range = delete_requests[0]["deleteContentRange"]["range"]
            assert delete_range["startIndex"] >= 10

    def test_content_after_preserved(self):
        """Content after section is not deleted."""
        document = {}
        body = {
            "content": [
                {"startIndex": 10, "endIndex": 50},  # Section content
                {"startIndex": 50, "endIndex": 100},  # After section
            ]
        }
        section = Section(anchor_id="h.test", level=1, start_index=10, end_index=50)
        ast = DocumentNode(
            children=[ParagraphNode(content=[TextNode("New")])]
        )

        requests, preserved, warnings = build_section_import_requests(
            document, body, "", section, ast
        )

        # Delete range should end at section end, not document end
        delete_requests = [r for r in requests if "deleteContentRange" in r]
        if delete_requests:
            delete_range = delete_requests[0]["deleteContentRange"]["range"]
            assert delete_range["endIndex"] <= 50
