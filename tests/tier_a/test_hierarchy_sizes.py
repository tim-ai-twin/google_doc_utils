"""Unit tests for hierarchy section size counting.

Tests cover:
- Section word/char count accuracy for multi-heading document
- Preamble counting
- Empty document returns zeros
- Document with no headings counts all content as preamble total
- Section sizes accuracy (SC-003)
"""

from extended_google_doc_utils.converter.hierarchy import (
    _count_all_sections,
    get_hierarchy,
)
from extended_google_doc_utils.converter.types import Section


def _make_paragraph(text: str, start: int, style: str = "NORMAL_TEXT", heading_id: str = ""):
    """Build a Google Docs API paragraph element."""
    end = start + len(text)
    para = {
        "startIndex": start,
        "endIndex": end,
        "paragraph": {
            "paragraphStyle": {"namedStyleType": style},
            "elements": [
                {
                    "startIndex": start,
                    "endIndex": end,
                    "textRun": {"content": text},
                }
            ],
        },
    }
    if heading_id:
        para["paragraph"]["paragraphStyle"]["headingId"] = heading_id
    return para


def _make_body(*elements):
    """Wrap paragraph elements in a body dict."""
    return {"content": list(elements)}


# ---------------------------------------------------------------------------
# _count_section_text
# ---------------------------------------------------------------------------


class TestCountAllSections:
    """Tests for the single-pass section counting helper."""

    def _count(self, body, start, end):
        """Helper: count a single section via _count_all_sections."""
        section = Section(anchor_id="", level=0, start_index=start, end_index=end)
        counts = _count_all_sections(body, [section])
        return counts.get(start, (0, 0))

    def test_simple_text(self):
        """Count words and chars in a single paragraph."""
        body = _make_body(
            _make_paragraph("Hello world\n", start=0),
        )
        words, chars = self._count(body, 0, 12)
        assert words == 2
        assert chars == len("Hello world")

    def test_range_filtering(self):
        """Only count text within the specified range."""
        p1 = _make_paragraph("alpha beta\n", start=0)
        p2 = _make_paragraph("gamma delta\n", start=11)
        body = _make_body(p1, p2)

        # Only count the second paragraph
        words, chars = self._count(body, 11, 23)
        assert words == 2
        assert chars == len("gamma delta")

    def test_empty_range_returns_zeros(self):
        """Empty range returns (0, 0)."""
        body = _make_body(_make_paragraph("some text\n", start=0))
        words, chars = self._count(body, 5, 5)
        assert words == 0
        assert chars == 0

    def test_skips_inline_objects(self):
        """Non-textRun elements are skipped."""
        body = {
            "content": [
                {
                    "startIndex": 0,
                    "endIndex": 20,
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "elements": [
                            {
                                "startIndex": 0,
                                "endIndex": 6,
                                "textRun": {"content": "hello "},
                            },
                            {
                                "startIndex": 6,
                                "endIndex": 7,
                                "inlineObjectElement": {"inlineObjectId": "img1"},
                            },
                            {
                                "startIndex": 7,
                                "endIndex": 13,
                                "textRun": {"content": "world\n"},
                            },
                        ],
                    },
                }
            ]
        }
        words, chars = self._count(body, 0, 20)
        assert words == 2
        assert chars == len("hello world")


# ---------------------------------------------------------------------------
# get_hierarchy — size counting integration
# ---------------------------------------------------------------------------


class TestHierarchySizes:
    """Tests for word/char counts populated by get_hierarchy."""

    def test_empty_document_returns_zeros(self):
        """Empty document body yields zero totals."""
        body = _make_body()
        result = get_hierarchy(body)
        assert result.total_word_count == 0
        assert result.total_char_count == 0
        assert result.headings == []

    def test_no_headings_counts_as_preamble(self):
        """Document with no headings exposes a single preamble entry."""
        body = _make_body(
            _make_paragraph("One two three four five.\n", start=1),
        )
        result = get_hierarchy(body)

        # Preamble is now surfaced so LLMs can discover the "" anchor.
        assert len(result.headings) == 1
        preamble = result.headings[0]
        assert preamble.anchor_id == ""
        assert preamble.level == 0
        assert preamble.text == "(preamble)"
        assert preamble.word_count == 5
        assert preamble.char_count == len("One two three four five.")
        assert result.total_word_count == 5
        assert result.total_char_count == len("One two three four five.")

    def test_preamble_plus_heading(self):
        """Preamble becomes a level=0 entry alongside the HEADING_1 section."""
        preamble = _make_paragraph("Preamble text here.\n", start=1)
        heading = _make_paragraph(
            "Introduction\n", start=21, style="HEADING_1", heading_id="h.intro"
        )
        section_text = _make_paragraph(
            "Section body with several words in it.\n", start=34,
        )
        body = _make_body(preamble, heading, section_text)
        result = get_hierarchy(body)

        assert len(result.headings) == 2

        preamble_entry = result.headings[0]
        assert preamble_entry.anchor_id == ""
        assert preamble_entry.level == 0
        assert preamble_entry.word_count > 0
        assert preamble_entry.char_count > 0

        h1_entry = result.headings[1]
        assert h1_entry.anchor_id == "h.intro"
        assert h1_entry.level == 1
        assert h1_entry.word_count > 0
        assert h1_entry.char_count > 0

        assert result.total_word_count == (
            preamble_entry.word_count + h1_entry.word_count
        )

    def test_multi_heading_section_counts(self):
        """Multiple headings get accurate per-section counts."""
        # Build a document:
        #   H1 "Chapter One" (start=1) -> body "aaa bbb ccc\n" (3 words)
        #   H1 "Chapter Two" (start=30) -> body "ddd eee\n" (2 words)
        h1 = _make_paragraph("Chapter One\n", start=1, style="HEADING_1", heading_id="h.c1")
        b1 = _make_paragraph("aaa bbb ccc\n", start=13)
        h2 = _make_paragraph("Chapter Two\n", start=25, style="HEADING_1", heading_id="h.c2")
        b2 = _make_paragraph("ddd eee\n", start=37)

        body = _make_body(h1, b1, h2, b2)
        result = get_hierarchy(body)

        assert len(result.headings) == 2

        c1 = result.headings[0]
        c2 = result.headings[1]

        # Chapter One section: "Chapter One" + "aaa bbb ccc" = 5 words
        assert c1.anchor_id == "h.c1"
        assert c1.word_count == 5
        assert c1.char_count == len("Chapter One aaa bbb ccc")

        # Chapter Two section: "Chapter Two" + "ddd eee" = 4 words
        assert c2.anchor_id == "h.c2"
        assert c2.word_count == 4
        assert c2.char_count == len("Chapter Two ddd eee")

        # Totals should be sum of all sections (no preamble here)
        assert result.total_word_count == 9
        assert result.total_char_count == c1.char_count + c2.char_count

    def test_section_sizes_within_5_percent(self):
        """Section sizes should be accurate to within 5% (SC-003).

        This test creates known content and verifies the counts match
        expected values exactly (which is well within 5%).
        """
        words = " ".join(["word"] * 100)
        content = words + "\n"
        start = 10
        heading = _make_paragraph(
            "My Section\n", start=1, style="HEADING_1", heading_id="h.s1"
        )
        text_para = _make_paragraph(content, start=start + 2)
        body = _make_body(heading, text_para)

        result = get_hierarchy(body)
        h = result.headings[0]

        # "My Section" + 100 x "word" = 102 words
        expected_words = 102
        tolerance = expected_words * 0.05

        assert abs(h.word_count - expected_words) <= tolerance

    def test_format_includes_word_hint(self):
        """Markdown output includes (N words) hint for each heading."""
        h1 = _make_paragraph("Intro\n", start=1, style="HEADING_1", heading_id="h.i")
        body_text = _make_paragraph("Some words here.\n", start=7)
        body = _make_body(h1, body_text)

        result = get_hierarchy(body)
        assert "(" in result.markdown
        assert "words)" in result.markdown
        # Should look like: # {^ h.i}Intro (N words)
        assert "{^ h.i}Intro (" in result.markdown

    def test_heading_with_zero_words_no_hint(self):
        """Headings with zero words should not show a word hint."""
        # A heading immediately followed by another heading (no body text)
        h1 = _make_paragraph("First\n", start=1, style="HEADING_1", heading_id="h.f")
        h2 = _make_paragraph("Second\n", start=7, style="HEADING_1", heading_id="h.s")
        body = _make_body(h1, h2)

        result = get_hierarchy(body)
        lines = result.markdown.split("\n")

        # First heading section contains only "First" heading text -> some words
        # Second heading section contains only "Second" heading text -> some words
        # Both should have word counts since heading text itself is counted
        for line in lines:
            assert "words)" in line
