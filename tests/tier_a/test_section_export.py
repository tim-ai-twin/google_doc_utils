"""Unit tests for section export functionality.

Tests cover:
- Section boundary calculation
- Preamble extraction
- Various heading level scenarios
- Last section handling
"""


from extended_google_doc_utils.converter.section_utils import (
    find_section,
    get_all_sections,
)


class TestFindSection:
    """Tests for section boundary finding."""

    def test_preamble_with_headings(self):
        """Find preamble when document has headings."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Preamble text\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 15,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.first",
                        },
                        "elements": [{"textRun": {"content": "First Heading\n"}}],
                    },
                    "startIndex": 15,
                    "endIndex": 30,
                },
            ]
        }

        section = find_section(body, "")

        assert section is not None
        assert section.is_preamble
        assert section.anchor_id == ""
        assert section.level == 0
        assert section.start_index == 1
        assert section.end_index == 15

    def test_preamble_no_headings(self):
        """Find preamble when document has no headings."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "All content\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 15,
                }
            ]
        }

        section = find_section(body, "")

        assert section is not None
        assert section.is_preamble
        assert section.end_index == 15

    def test_find_heading_section(self):
        """Find section by heading anchor."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.first",
                        },
                        "elements": [{"textRun": {"content": "First\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Content\n"}}],
                    },
                    "startIndex": 10,
                    "endIndex": 20,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.second",
                        },
                        "elements": [{"textRun": {"content": "Second\n"}}],
                    },
                    "startIndex": 20,
                    "endIndex": 30,
                },
            ]
        }

        section = find_section(body, "h.first")

        assert section is not None
        assert section.anchor_id == "h.first"
        assert section.level == 1
        assert section.start_index == 1
        assert section.end_index == 20

    def test_find_subsection(self):
        """Find subsection (lower level heading)."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.parent",
                        },
                        "elements": [{"textRun": {"content": "Parent\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.child",
                        },
                        "elements": [{"textRun": {"content": "Child\n"}}],
                    },
                    "startIndex": 10,
                    "endIndex": 20,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Content\n"}}],
                    },
                    "startIndex": 20,
                    "endIndex": 30,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.sibling",
                        },
                        "elements": [{"textRun": {"content": "Sibling\n"}}],
                    },
                    "startIndex": 30,
                    "endIndex": 40,
                },
            ]
        }

        section = find_section(body, "h.child")

        assert section is not None
        assert section.anchor_id == "h.child"
        assert section.level == 2
        assert section.start_index == 10
        # Should end at sibling heading (same level)
        assert section.end_index == 30

    def test_section_includes_subsections(self):
        """Parent section includes subsections."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.parent",
                        },
                        "elements": [{"textRun": {"content": "Parent\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.child",
                        },
                        "elements": [{"textRun": {"content": "Child\n"}}],
                    },
                    "startIndex": 10,
                    "endIndex": 20,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.next",
                        },
                        "elements": [{"textRun": {"content": "Next\n"}}],
                    },
                    "startIndex": 20,
                    "endIndex": 30,
                },
            ]
        }

        section = find_section(body, "h.parent")

        assert section is not None
        assert section.start_index == 1
        # Parent section extends to next H1, including child H2
        assert section.end_index == 20

    def test_last_section(self):
        """Last section extends to document end."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.last",
                        },
                        "elements": [{"textRun": {"content": "Last\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Final content\n"}}],
                    },
                    "startIndex": 10,
                    "endIndex": 25,
                },
            ]
        }

        section = find_section(body, "h.last")

        assert section is not None
        assert section.end_index == 25

    def test_anchor_not_found(self):
        """Return None for non-existent anchor."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.exists",
                        },
                        "elements": [{"textRun": {"content": "Exists\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                }
            ]
        }

        section = find_section(body, "h.not_found")

        assert section is None


class TestGetAllSections:
    """Tests for getting all sections."""

    def test_all_sections(self):
        """Get all sections including preamble."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [{"textRun": {"content": "Preamble\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.1",
                        },
                        "elements": [{"textRun": {"content": "First\n"}}],
                    },
                    "startIndex": 10,
                    "endIndex": 20,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.2",
                        },
                        "elements": [{"textRun": {"content": "Second\n"}}],
                    },
                    "startIndex": 20,
                    "endIndex": 30,
                },
            ]
        }

        sections = get_all_sections(body)

        assert len(sections) == 3
        assert sections[0].is_preamble
        assert sections[1].anchor_id == "h.1"
        assert sections[2].anchor_id == "h.2"

    def test_no_preamble(self):
        """Document starting with heading has no preamble in result."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1",
                            "headingId": "h.1",
                        },
                        "elements": [{"textRun": {"content": "First\n"}}],
                    },
                    "startIndex": 1,
                    "endIndex": 10,
                }
            ]
        }

        sections = get_all_sections(body)

        # Preamble is included but has 0 length (start == end)
        # The actual heading section should be there
        heading_sections = [s for s in sections if not s.is_preamble]
        assert len(heading_sections) == 1

    def test_nested_headings(self):
        """Properly handle nested heading levels."""
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
                    "endIndex": 5,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "headingId": "h.2",
                        },
                        "elements": [{"textRun": {"content": "H2\n"}}],
                    },
                    "startIndex": 5,
                    "endIndex": 10,
                },
                {
                    "paragraph": {
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_3",
                            "headingId": "h.3",
                        },
                        "elements": [{"textRun": {"content": "H3\n"}}],
                    },
                    "startIndex": 10,
                    "endIndex": 15,
                },
            ]
        }

        sections = get_all_sections(body)

        heading_sections = [s for s in sections if not s.is_preamble]
        assert len(heading_sections) == 3
        assert heading_sections[0].level == 1
        assert heading_sections[1].level == 2
        assert heading_sections[2].level == 3
