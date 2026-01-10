"""Unit tests for document hierarchy extraction.

Tests cover:
- Heading extraction from document body
- Hierarchy formatting to markdown
- Tab resolution
"""

import pytest

from extended_google_doc_utils.converter.exceptions import MultipleTabsError
from extended_google_doc_utils.converter.hierarchy import (
    extract_headings,
    extract_paragraph_text,
    format_hierarchy,
    get_hierarchy,
)
from extended_google_doc_utils.converter.tab_utils import (
    get_tab_content,
    resolve_tab_id,
)
from extended_google_doc_utils.converter.types import HeadingAnchor, TabReference


class TestExtractHeadings:
    """Tests for heading extraction."""

    def test_empty_body(self):
        """Extract from empty body."""
        body = {"content": []}
        headings = extract_headings(body)
        assert headings == []

    def test_no_headings(self):
        """Extract from body with no headings."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Regular paragraph"}}],
                    },
                    "startIndex": 1,
                }
            ]
        }
        headings = extract_headings(body)
        assert headings == []

    def test_single_heading(self):
        """Extract single heading."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.abc123",
                        },
                        "elements": [{"textRun": {"content": "My Heading\n"}}],
                    },
                    "startIndex": 1,
                }
            ]
        }
        headings = extract_headings(body)

        assert len(headings) == 1
        assert headings[0].level == 1
        assert headings[0].anchor_id == "h.abc123"
        assert headings[0].text == "My Heading"

    def test_multiple_heading_levels(self):
        """Extract headings of different levels."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.1",
                        },
                        "elements": [{"textRun": {"content": "H1\n"}}],
                    },
                    "startIndex": 1,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.2",
                        },
                        "elements": [{"textRun": {"content": "H2\n"}}],
                    },
                    "startIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_3",
                            "headingId": "h.3",
                        },
                        "elements": [{"textRun": {"content": "H3\n"}}],
                    },
                    "startIndex": 20,
                },
            ]
        }
        headings = extract_headings(body)

        assert len(headings) == 3
        assert headings[0].level == 1
        assert headings[1].level == 2
        assert headings[2].level == 3

    def test_heading_without_id(self):
        """Extract heading without headingId."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "elements": [{"textRun": {"content": "No ID Heading\n"}}],
                    },
                    "startIndex": 1,
                }
            ]
        }
        headings = extract_headings(body)

        assert len(headings) == 1
        assert headings[0].anchor_id == ""

    def test_mixed_content(self):
        """Extract headings mixed with regular paragraphs."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Intro\n"}}],
                    },
                    "startIndex": 1,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.1",
                        },
                        "elements": [{"textRun": {"content": "Section 1\n"}}],
                    },
                    "startIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Content\n"}}],
                    },
                    "startIndex": 25,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.2",
                        },
                        "elements": [{"textRun": {"content": "Subsection\n"}}],
                    },
                    "startIndex": 35,
                },
            ]
        }
        headings = extract_headings(body)

        assert len(headings) == 2


class TestExtractParagraphText:
    """Tests for paragraph text extraction."""

    def test_simple_text(self):
        """Extract simple text."""
        paragraph = {"elements": [{"textRun": {"content": "Hello world\n"}}]}
        text = extract_paragraph_text(paragraph)
        assert text == "Hello world"

    def test_multiple_runs(self):
        """Extract from multiple text runs."""
        paragraph = {
            "elements": [
                {"textRun": {"content": "Hello "}},
                {"textRun": {"content": "world\n"}},
            ]
        }
        text = extract_paragraph_text(paragraph)
        assert text == "Hello world"

    def test_empty_paragraph(self):
        """Extract from empty paragraph."""
        paragraph = {"elements": []}
        text = extract_paragraph_text(paragraph)
        assert text == ""

    def test_non_text_elements(self):
        """Handle non-text elements."""
        paragraph = {
            "elements": [
                {"textRun": {"content": "Before "}},
                {"inlineObjectElement": {"inlineObjectId": "img1"}},
                {"textRun": {"content": " after\n"}},
            ]
        }
        text = extract_paragraph_text(paragraph)
        assert text == "Before  after"


class TestFormatHierarchy:
    """Tests for hierarchy formatting."""

    def test_empty_list(self):
        """Format empty heading list."""
        markdown = format_hierarchy([])
        assert markdown == ""

    def test_single_heading(self):
        """Format single heading."""
        headings = [HeadingAnchor("h.abc", 1, "Title", 0)]
        markdown = format_hierarchy(headings)
        assert markdown == "# {^ h.abc}Title"

    def test_multiple_levels(self):
        """Format multiple heading levels."""
        headings = [
            HeadingAnchor("h.1", 1, "One", 0),
            HeadingAnchor("h.2", 2, "Two", 10),
            HeadingAnchor("h.3", 3, "Three", 20),
        ]
        markdown = format_hierarchy(headings)

        lines = markdown.split("\n")
        assert len(lines) == 3
        assert lines[0] == "# {^ h.1}One"
        assert lines[1] == "## {^ h.2}Two"
        assert lines[2] == "### {^ h.3}Three"

    def test_heading_without_anchor(self):
        """Format heading without anchor ID."""
        headings = [HeadingAnchor("", 1, "No Anchor", 0)]
        markdown = format_hierarchy(headings)
        assert markdown == "# No Anchor"


class TestGetHierarchy:
    """Tests for full hierarchy extraction."""

    def test_full_hierarchy(self):
        """Get complete hierarchy result."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.intro",
                        },
                        "elements": [{"textRun": {"content": "Introduction\n"}}],
                    },
                    "startIndex": 1,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.bg",
                        },
                        "elements": [{"textRun": {"content": "Background\n"}}],
                    },
                    "startIndex": 15,
                },
            ]
        }
        result = get_hierarchy(body)

        assert len(result.headings) == 2
        assert "# {^ h.intro}Introduction" in result.markdown
        assert "## {^ h.bg}Background" in result.markdown


class TestTabUtils:
    """Tests for tab resolution utilities."""

    def test_single_tab_empty_id(self):
        """Single tab with empty tab_id."""
        document = {
            "tabs": [
                {
                    "tabProperties": {"tabId": "t.123"},
                    "documentTab": {"body": {"content": []}},
                }
            ]
        }
        tab_ref = TabReference("doc123", "")
        tab_id = resolve_tab_id(document, tab_ref)
        assert tab_id == "t.123"

    def test_single_tab_specific_id(self):
        """Single tab with specific tab_id."""
        document = {
            "tabs": [
                {
                    "tabProperties": {"tabId": "t.123"},
                    "documentTab": {"body": {"content": []}},
                }
            ]
        }
        tab_ref = TabReference("doc123", "t.123")
        tab_id = resolve_tab_id(document, tab_ref)
        assert tab_id == "t.123"

    def test_multiple_tabs_empty_id_raises(self):
        """Multiple tabs with empty tab_id raises error."""
        document = {
            "tabs": [
                {"tabProperties": {"tabId": "t.1"}},
                {"tabProperties": {"tabId": "t.2"}},
            ]
        }
        tab_ref = TabReference("doc123", "")

        with pytest.raises(MultipleTabsError) as exc_info:
            resolve_tab_id(document, tab_ref)

        assert exc_info.value.tab_count == 2

    def test_multiple_tabs_specific_id(self):
        """Multiple tabs with specific tab_id."""
        document = {
            "tabs": [
                {"tabProperties": {"tabId": "t.1"}},
                {"tabProperties": {"tabId": "t.2"}},
            ]
        }
        tab_ref = TabReference("doc123", "t.2")
        tab_id = resolve_tab_id(document, tab_ref)
        assert tab_id == "t.2"

    def test_no_tabs_info(self):
        """Document without tabs info (legacy single-tab)."""
        document = {"body": {"content": []}}
        tab_ref = TabReference("doc123", "")
        tab_id = resolve_tab_id(document, tab_ref)
        assert tab_id == ""

    def test_get_tab_content_single_tab(self):
        """Get content from single-tab document."""
        document = {
            "tabs": [
                {
                    "tabProperties": {"tabId": "t.1"},
                    "documentTab": {"body": {"content": [{"type": "paragraph"}]}},
                }
            ]
        }
        body = get_tab_content(document, "t.1")
        assert body == {"content": [{"type": "paragraph"}]}

    def test_get_tab_content_no_tabs(self):
        """Get content from legacy document."""
        document = {"body": {"content": [{"type": "paragraph"}]}}
        body = get_tab_content(document, "")
        assert body == {"content": [{"type": "paragraph"}]}


class TestTabReference:
    """Tests for TabReference validation."""

    def test_valid_reference(self):
        """Create valid tab reference."""
        ref = TabReference("doc123", "tab456")
        assert ref.document_id == "doc123"
        assert ref.tab_id == "tab456"

    def test_empty_tab_id(self):
        """Create reference with empty tab_id."""
        ref = TabReference("doc123")
        assert ref.document_id == "doc123"
        assert ref.tab_id == ""

    def test_empty_document_id_raises(self):
        """Empty document_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TabReference("")

        assert "document_id is required" in str(exc_info.value)

    def test_frozen(self):
        """TabReference is immutable."""
        ref = TabReference("doc123", "tab456")

        with pytest.raises(Exception):  # FrozenInstanceError
            ref.document_id = "other"
