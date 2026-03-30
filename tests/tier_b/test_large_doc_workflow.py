"""End-to-end tests for the large-document editing workflow (T019).

Validates that the converter pipeline handles a very large Google Doc
correctly: metadata retrieval, hierarchy extraction with word/char counts,
plain-text export (no MEBDF markers), temp-file grep, and section read.

Test document: 19lqJVCK9W3Cu5A20ZfKGvV66C8TmSQRigwsS3iE7A3M
"""

import re

import pytest

from extended_google_doc_utils.converter import GoogleDocsConverter
from extended_google_doc_utils.converter.types import TabReference

LARGE_DOC_ID = "19lqJVCK9W3Cu5A20ZfKGvV66C8TmSQRigwsS3iE7A3M"
# Single-tab doc with proper headingIds — used for read_section test
SINGLE_TAB_DOC_ID = "19LesxcFk6C72A6L5V8MCfOmf7RK975p5kuO4WM7kDmI"

pytestmark = pytest.mark.tier_b

# -- fixtures ----------------------------------------------------------------


@pytest.fixture(scope="module")
def converter(google_credentials):
    """Create a GoogleDocsConverter for large-doc testing."""
    if google_credentials is None:
        pytest.skip("Google credentials not available")
    return GoogleDocsConverter(credentials=google_credentials)


@pytest.fixture(scope="module")
def doc_metadata(converter):
    """Fetch metadata once for the module."""
    return converter.get_metadata(LARGE_DOC_ID)


@pytest.fixture(scope="module")
def first_tab_id(doc_metadata):
    """Return the tab_id of the first tab."""
    tabs = doc_metadata["tabs"]
    assert len(tabs) > 0, "Document has no tabs"
    return tabs[0]["tab_id"]


@pytest.fixture(scope="module")
def hierarchy(converter, first_tab_id):
    """Fetch hierarchy for the first tab."""
    tab_ref = TabReference(document_id=LARGE_DOC_ID, tab_id=first_tab_id)
    return converter.get_hierarchy(tab_ref)


@pytest.fixture(scope="module")
def plain_content(converter, first_tab_id):
    """Read the first tab in plain format."""
    tab_ref = TabReference(document_id=LARGE_DOC_ID, tab_id=first_tab_id)
    return converter.read_tab(tab_ref, format="plain")


# -- Step 1: get_metadata returns tabs ---------------------------------------


class TestGetMetadata:
    def test_tabs_are_returned(self, doc_metadata):
        """get_metadata returns at least one tab."""
        tabs = doc_metadata["tabs"]
        assert isinstance(tabs, list)
        assert len(tabs) >= 1

    def test_tabs_have_ids(self, doc_metadata):
        """Each tab has a non-empty tab_id."""
        for tab in doc_metadata["tabs"]:
            assert tab.get("tab_id"), f"Tab '{tab.get('title')}' missing tab_id"


# -- Step 2: get_hierarchy with word/char counts -----------------------------


class TestGetHierarchy:
    def test_headings_returned(self, hierarchy):
        """Hierarchy contains at least one heading."""
        assert len(hierarchy.headings) > 0

    def test_headings_have_word_count(self, hierarchy):
        """Every heading has word_count > 0."""
        for h in hierarchy.headings:
            assert h.word_count > 0, (
                f"Heading '{h.text}' (anchor={h.anchor_id}) has word_count=0"
            )

    def test_headings_have_char_count(self, hierarchy):
        """Every heading has char_count > 0."""
        for h in hierarchy.headings:
            assert h.char_count > 0, (
                f"Heading '{h.text}' (anchor={h.anchor_id}) has char_count=0"
            )

    def test_total_word_count(self, hierarchy):
        """Total word count across the document is positive."""
        assert hierarchy.total_word_count > 0

    def test_total_char_count(self, hierarchy):
        """Total char count across the document is positive."""
        assert hierarchy.total_char_count > 0


# -- Step 3: read_tab plain format (no MEBDF markers) ------------------------

# MEBDF marker patterns: {! (inline format), {/!} (close), {^ (anchor)
_MEBDF_PATTERN = re.compile(r"\{!|\{/!\}|\{\^")


class TestReadTabPlain:
    def test_content_is_nonempty(self, plain_content):
        """Plain export produces non-empty content."""
        assert plain_content.content

    def test_no_mebdf_markers(self, plain_content):
        """Plain format must not contain MEBDF markers."""
        match = _MEBDF_PATTERN.search(plain_content.content)
        assert match is None, (
            f"Found MEBDF marker at position {match.start()}: "
            f"'{plain_content.content[match.start():match.start()+20]}...'"
        )


# -- Step 4: write to temp file and grep for known term ----------------------


class TestTempFileGrep:
    def test_grep_known_term(self, plain_content, tmp_path):
        """Write plain content to a temp file and verify a known term exists.

        We search for 'the' -- a word virtually guaranteed to appear in any
        large English-language document.
        """
        md_file = tmp_path / "doc.md"
        md_file.write_text(plain_content.content)

        text = md_file.read_text()
        assert "the" in text.lower(), (
            "Expected the word 'the' to appear in the large document"
        )


# -- Step 5: read_section returns MEBDF content ------------------------------


class TestReadSection:
    def test_read_section_returns_mebdf(self, converter):
        """read_section for a heading returns MEBDF-formatted content.

        Uses the single-tab test doc which has proper headingIds assigned.
        """
        tab_ref = TabReference(document_id=SINGLE_TAB_DOC_ID)
        hier = converter.get_hierarchy(tab_ref)
        assert len(hier.headings) > 0, "No headings in single-tab test doc"

        heading = hier.headings[0]
        assert heading.anchor_id, "First heading has no anchor_id"

        result = converter.read_section(tab_ref, heading.anchor_id)

        assert result.content, "read_section returned empty content"
        assert heading.anchor_id in result.content, (
            f"Anchor '{heading.anchor_id}' not found in section content"
        )
