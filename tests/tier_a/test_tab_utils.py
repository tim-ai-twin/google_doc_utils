"""Unit tests for tab_utils — multi-tab resolution and content extraction.

All tests are tier_a (no credentials needed) using mock document dicts.
"""

import pytest

from extended_google_doc_utils.converter.exceptions import (
    MultipleTabsError,
    TabNotFoundError,
)
from extended_google_doc_utils.converter.tab_utils import (
    get_inline_objects,
    get_positioned_objects,
    get_tab_content,
    get_tab_document_style,
    get_tab_named_styles,
    resolve_tab_id,
)
from extended_google_doc_utils.converter.types import TabReference

# ---------------------------------------------------------------------------
# Fixtures: mock document structures
# ---------------------------------------------------------------------------

def _make_body(text: str) -> dict:
    """Build a minimal Google Docs body dict with a single text run."""
    return {
        "content": [
            {"paragraph": {"elements": [{"textRun": {"content": text}}]}}
        ],
    }


def _make_doc_style(**rgb) -> dict:
    """Build a minimal documentStyle with an RGB background."""
    return {"background": {"color": {"rgbColor": rgb}}}


def _single_tab_doc():
    """Single-tab document with tabs array containing one entry."""
    return {
        "documentId": "single-doc",
        "tabs": [
            {
                "tabProperties": {
                    "tabId": "t.0",
                    "title": "Main",
                    "index": 0,
                },
                "documentTab": {
                    "body": _make_body("Single tab content"),
                    "documentStyle": _make_doc_style(
                        red=1, green=1, blue=1,
                    ),
                    "namedStyles": {
                        "styles": [{"namedStyleType": "NORMAL_TEXT"}],
                    },
                    "inlineObjects": {
                        "obj1": {"inlineObjectProperties": {}},
                    },
                    "positionedObjects": {
                        "pos1": {"positionedObjectProperties": {}},
                    },
                },
            }
        ],
    }


def _multi_tab_doc():
    """Multi-tab document with 3 tabs."""
    return {
        "documentId": "multi-doc",
        "tabs": [
            {
                "tabProperties": {
                    "tabId": "t.abc",
                    "title": "Alabama",
                    "index": 0,
                },
                "documentTab": {
                    "body": _make_body("Alabama content"),
                    "documentStyle": _make_doc_style(red=1),
                    "namedStyles": {
                        "styles": [{"namedStyleType": "HEADING_1"}],
                    },
                    "inlineObjects": {
                        "al_img": {"inlineObjectProperties": {}},
                    },
                    "positionedObjects": {},
                },
            },
            {
                "tabProperties": {
                    "tabId": "t.def",
                    "title": "Britain",
                    "index": 1,
                },
                "documentTab": {
                    "body": _make_body("Britain content"),
                    "documentStyle": _make_doc_style(blue=1),
                    "namedStyles": {
                        "styles": [{"namedStyleType": "HEADING_2"}],
                    },
                    "inlineObjects": {},
                    "positionedObjects": {
                        "br_pos": {"positionedObjectProperties": {}},
                    },
                },
            },
            {
                "tabProperties": {
                    "tabId": "t.ghi",
                    "title": "California",
                    "index": 2,
                },
                "documentTab": {
                    "body": _make_body("California content"),
                    "documentStyle": _make_doc_style(green=1),
                    "namedStyles": {
                        "styles": [{"namedStyleType": "HEADING_3"}],
                    },
                    "inlineObjects": {},
                    "positionedObjects": {},
                },
            },
        ],
    }


def _legacy_doc():
    """Legacy single-tab document with no tabs array (pre-tabs API)."""
    return {
        "documentId": "legacy-doc",
        "body": _make_body("Legacy"),
        "documentStyle": {"background": {}},
        "namedStyles": {"styles": []},
        "inlineObjects": {"legacy_obj": {}},
        "positionedObjects": {"legacy_pos": {}},
    }


# ---------------------------------------------------------------------------
# resolve_tab_id tests
# ---------------------------------------------------------------------------

class TestResolveTabId:
    def test_single_tab_empty_id(self):
        doc = _single_tab_doc()
        ref = TabReference(document_id="single-doc", tab_id="")
        assert resolve_tab_id(doc, ref) == "t.0"

    def test_single_tab_explicit_id(self):
        doc = _single_tab_doc()
        ref = TabReference(document_id="single-doc", tab_id="t.0")
        assert resolve_tab_id(doc, ref) == "t.0"

    def test_multi_tab_valid_id(self):
        doc = _multi_tab_doc()
        ref = TabReference(document_id="multi-doc", tab_id="t.def")
        assert resolve_tab_id(doc, ref) == "t.def"

    def test_multi_tab_empty_id_raises(self):
        doc = _multi_tab_doc()
        ref = TabReference(document_id="multi-doc", tab_id="")
        with pytest.raises(MultipleTabsError) as exc_info:
            resolve_tab_id(doc, ref)
        assert exc_info.value.tab_count == 3
        assert len(exc_info.value.available_tabs) == 3

    def test_multi_tab_invalid_id_raises(self):
        doc = _multi_tab_doc()
        ref = TabReference(document_id="multi-doc", tab_id="t.nonexistent")
        with pytest.raises(TabNotFoundError) as exc_info:
            resolve_tab_id(doc, ref)
        assert exc_info.value.tab_id == "t.nonexistent"
        assert len(exc_info.value.available_tabs) == 3

    def test_legacy_doc_empty_id(self):
        doc = _legacy_doc()
        ref = TabReference(document_id="legacy-doc", tab_id="")
        assert resolve_tab_id(doc, ref) == ""

    def test_legacy_doc_explicit_id(self):
        doc = _legacy_doc()
        ref = TabReference(document_id="legacy-doc", tab_id="t.0")
        assert resolve_tab_id(doc, ref) == "t.0"


# ---------------------------------------------------------------------------
# get_tab_content tests
# ---------------------------------------------------------------------------

class TestGetTabContent:
    def test_multi_tab_returns_correct_body(self):
        doc = _multi_tab_doc()
        body = get_tab_content(doc, "t.abc")
        text = body["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
        assert text == "Alabama content"

    def test_multi_tab_second_tab(self):
        doc = _multi_tab_doc()
        body = get_tab_content(doc, "t.def")
        text = body["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
        assert text == "Britain content"

    def test_multi_tab_third_tab(self):
        doc = _multi_tab_doc()
        body = get_tab_content(doc, "t.ghi")
        text = body["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
        assert text == "California content"

    def test_multi_tab_invalid_id_raises(self):
        doc = _multi_tab_doc()
        with pytest.raises(TabNotFoundError):
            get_tab_content(doc, "t.invalid")

    def test_single_tab(self):
        doc = _single_tab_doc()
        body = get_tab_content(doc, "t.0")
        text = body["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
        assert text == "Single tab content"

    def test_legacy_doc(self):
        doc = _legacy_doc()
        body = get_tab_content(doc, "")
        text = body["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
        assert text == "Legacy"


# ---------------------------------------------------------------------------
# get_tab_document_style tests
# ---------------------------------------------------------------------------

class TestGetTabDocumentStyle:
    def test_multi_tab_returns_correct_style(self):
        doc = _multi_tab_doc()
        style = get_tab_document_style(doc, "t.abc")
        assert style["background"]["color"]["rgbColor"]["red"] == 1

    def test_multi_tab_different_tab(self):
        doc = _multi_tab_doc()
        style = get_tab_document_style(doc, "t.def")
        assert style["background"]["color"]["rgbColor"]["blue"] == 1

    def test_multi_tab_invalid_id_raises(self):
        doc = _multi_tab_doc()
        with pytest.raises(TabNotFoundError):
            get_tab_document_style(doc, "t.invalid")

    def test_legacy_doc(self):
        doc = _legacy_doc()
        style = get_tab_document_style(doc, "")
        assert "background" in style


# ---------------------------------------------------------------------------
# get_tab_named_styles tests
# ---------------------------------------------------------------------------

class TestGetTabNamedStyles:
    def test_multi_tab_returns_correct_styles(self):
        doc = _multi_tab_doc()
        styles = get_tab_named_styles(doc, "t.abc")
        assert styles["styles"][0]["namedStyleType"] == "HEADING_1"

    def test_multi_tab_different_tab(self):
        doc = _multi_tab_doc()
        styles = get_tab_named_styles(doc, "t.def")
        assert styles["styles"][0]["namedStyleType"] == "HEADING_2"

    def test_multi_tab_invalid_id_raises(self):
        doc = _multi_tab_doc()
        with pytest.raises(TabNotFoundError):
            get_tab_named_styles(doc, "t.invalid")


# ---------------------------------------------------------------------------
# get_inline_objects tests
# ---------------------------------------------------------------------------

class TestGetInlineObjects:
    def test_multi_tab_returns_correct_objects(self):
        doc = _multi_tab_doc()
        objects = get_inline_objects(doc, "t.abc")
        assert "al_img" in objects

    def test_multi_tab_empty_objects(self):
        doc = _multi_tab_doc()
        objects = get_inline_objects(doc, "t.def")
        assert objects == {}

    def test_multi_tab_invalid_id_raises(self):
        doc = _multi_tab_doc()
        with pytest.raises(TabNotFoundError):
            get_inline_objects(doc, "t.invalid")

    def test_legacy_doc(self):
        doc = _legacy_doc()
        objects = get_inline_objects(doc, "")
        assert "legacy_obj" in objects


# ---------------------------------------------------------------------------
# get_positioned_objects tests
# ---------------------------------------------------------------------------

class TestGetPositionedObjects:
    def test_multi_tab_returns_correct_objects(self):
        doc = _multi_tab_doc()
        objects = get_positioned_objects(doc, "t.def")
        assert "br_pos" in objects

    def test_multi_tab_empty_objects(self):
        doc = _multi_tab_doc()
        objects = get_positioned_objects(doc, "t.abc")
        assert objects == {}

    def test_multi_tab_invalid_id_raises(self):
        doc = _multi_tab_doc()
        with pytest.raises(TabNotFoundError):
            get_positioned_objects(doc, "t.invalid")


# ---------------------------------------------------------------------------
# Error message content tests
# ---------------------------------------------------------------------------

class TestErrorMessages:
    def test_multiple_tabs_error_contains_tab_info(self):
        doc = _multi_tab_doc()
        ref = TabReference(document_id="multi-doc", tab_id="")
        with pytest.raises(MultipleTabsError) as exc_info:
            resolve_tab_id(doc, ref)
        msg = str(exc_info.value)
        assert "3 tabs" in msg
        assert 't.abc' in msg
        assert 'Alabama' in msg
        assert 't.def' in msg
        assert 'Britain' in msg
        assert 't.ghi' in msg
        assert 'California' in msg

    def test_tab_not_found_error_contains_tab_info(self):
        doc = _multi_tab_doc()
        ref = TabReference(document_id="multi-doc", tab_id="t.bogus")
        with pytest.raises(TabNotFoundError) as exc_info:
            resolve_tab_id(doc, ref)
        msg = str(exc_info.value)
        assert 't.bogus' in msg
        assert 't.abc' in msg
        assert 'Alabama' in msg
