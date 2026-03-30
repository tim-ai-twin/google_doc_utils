"""End-to-end tests for multi-tab document support.

All tests require Google OAuth credentials (tier_b) and use the shared
multi-tab test document with tabs: Alabama, Britain, California.

Document ID: 1iRhQ21xWUJ9GIrn-G_67_gBth5e4s_tBA2Vp8hOb0a0
"""

import pytest

from tests.conftest import MULTI_TAB_DOCUMENT_ID

pytestmark = pytest.mark.tier_b


@pytest.fixture(scope="module")
def converter(google_credentials):
    """Create a GoogleDocsConverter for multi-tab testing."""
    if google_credentials is None:
        pytest.skip("Google credentials not available")

    from extended_google_doc_utils.converter.converter import GoogleDocsConverter

    return GoogleDocsConverter(credentials=google_credentials)


@pytest.fixture(scope="module")
def doc_metadata(converter):
    """Fetch metadata once for the module — gives us tab IDs."""
    return converter.get_metadata(MULTI_TAB_DOCUMENT_ID)


@pytest.fixture(scope="module")
def tab_ids(doc_metadata):
    """Extract tab IDs from metadata."""
    return {t["title"]: t["tab_id"] for t in doc_metadata["tabs"]}


# ---------------------------------------------------------------------------
# US1: get_metadata lists all tabs
# ---------------------------------------------------------------------------


class TestGetMetadata:
    def test_returns_three_tabs(self, doc_metadata):
        tabs = doc_metadata["tabs"]
        assert len(tabs) == 3

    def test_tab_titles(self, doc_metadata):
        titles = [t["title"] for t in doc_metadata["tabs"]]
        assert "Alabama" in titles
        assert "Britain" in titles
        assert "California" in titles

    def test_tabs_have_ids(self, doc_metadata):
        for tab in doc_metadata["tabs"]:
            assert tab["tab_id"], f"Tab '{tab['title']}' has no tab_id"

    def test_tabs_have_indices(self, doc_metadata):
        indices = [t["index"] for t in doc_metadata["tabs"]]
        assert sorted(indices) == [0, 1, 2]


# ---------------------------------------------------------------------------
# US1: read_tab returns correct content per tab
# ---------------------------------------------------------------------------


class TestReadTab:
    def test_read_each_tab_returns_distinct_content(self, converter, tab_ids):
        from extended_google_doc_utils.converter.types import TabReference

        contents = {}
        for title, tid in tab_ids.items():
            tab = TabReference(document_id=MULTI_TAB_DOCUMENT_ID, tab_id=tid)
            result = converter.read_tab(tab)
            contents[title] = result.content

        # Each tab should have unique content
        assert len(set(contents.values())) == 3, "All three tabs should have distinct content"

    def test_empty_tab_id_raises_multiple_tabs_error(self, converter):
        from extended_google_doc_utils.converter.exceptions import MultipleTabsError
        from extended_google_doc_utils.converter.types import TabReference

        tab = TabReference(document_id=MULTI_TAB_DOCUMENT_ID, tab_id="")
        with pytest.raises(MultipleTabsError) as exc_info:
            converter.read_tab(tab)
        assert exc_info.value.tab_count == 3
        assert len(exc_info.value.available_tabs) == 3

    def test_invalid_tab_id_raises_not_found(self, converter):
        from extended_google_doc_utils.converter.exceptions import TabNotFoundError
        from extended_google_doc_utils.converter.types import TabReference

        tab = TabReference(document_id=MULTI_TAB_DOCUMENT_ID, tab_id="t.nonexistent")
        with pytest.raises(TabNotFoundError) as exc_info:
            converter.read_tab(tab)
        assert exc_info.value.tab_id == "t.nonexistent"
        assert len(exc_info.value.available_tabs) == 3


# ---------------------------------------------------------------------------
# US2: write_tab modifies only target tab (tab isolation)
# ---------------------------------------------------------------------------


class TestWriteTab:
    def test_write_preserves_other_tabs(self, converter, tab_ids, resource_manager):
        """Write to one tab, verify other tabs unchanged."""
        from extended_google_doc_utils.converter.types import TabReference

        # We can't add tabs programmatically, so we test on the shared doc
        # by reading, writing the same content back, and verifying others unchanged.
        # Read all tabs before
        before = {}
        for title, tid in tab_ids.items():
            tab = TabReference(document_id=MULTI_TAB_DOCUMENT_ID, tab_id=tid)
            before[title] = converter.read_tab(tab).content

        # Write the same content back to Alabama tab (idempotent)
        alabama_tab = TabReference(
            document_id=MULTI_TAB_DOCUMENT_ID,
            tab_id=tab_ids["Alabama"],
        )
        converter.write_tab(alabama_tab, before["Alabama"])

        # Read all tabs after
        after = {}
        for title, tid in tab_ids.items():
            tab = TabReference(document_id=MULTI_TAB_DOCUMENT_ID, tab_id=tid)
            after[title] = converter.read_tab(tab).content

        # Other tabs should be unchanged
        assert after["Britain"] == before["Britain"]
        assert after["California"] == before["California"]


# ---------------------------------------------------------------------------
# US3: Style extraction per tab
# ---------------------------------------------------------------------------


class TestStyleExtraction:
    def test_get_document_styles_per_tab(self, converter, google_credentials, tab_ids):
        """Each tab should return styles (may be same or different)."""
        from extended_google_doc_utils.converter.style_reader import (
            read_document_styles,
        )

        styles = {}
        for title, tid in tab_ids.items():
            result = read_document_styles(
                MULTI_TAB_DOCUMENT_ID, google_credentials, tid
            )
            styles[title] = result
            # Basic validation: should have document_properties and effective_styles
            assert result.document_properties is not None
            assert len(result.effective_styles) > 0

    def test_empty_tab_id_raises_error(self, converter, google_credentials):
        from extended_google_doc_utils.converter.exceptions import MultipleTabsError
        from extended_google_doc_utils.converter.style_reader import (
            read_document_styles,
        )

        with pytest.raises(MultipleTabsError):
            read_document_styles(MULTI_TAB_DOCUMENT_ID, google_credentials, "")


# ---------------------------------------------------------------------------
# US4: get_hierarchy per tab
# ---------------------------------------------------------------------------


class TestGetHierarchy:
    def test_hierarchy_per_tab(self, converter, tab_ids):
        """Each tab should return its own heading hierarchy."""
        from extended_google_doc_utils.converter.types import TabReference

        hierarchies = {}
        for title, tid in tab_ids.items():
            tab = TabReference(document_id=MULTI_TAB_DOCUMENT_ID, tab_id=tid)
            result = converter.get_hierarchy(tab)
            hierarchies[title] = result

        # Each tab should have at least some structure
        for title, hierarchy in hierarchies.items():
            # May or may not have headings depending on doc content
            assert hierarchy is not None, f"Hierarchy for {title} is None"
