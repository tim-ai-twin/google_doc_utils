"""MCP-layer tests for multi-tab error handling.

Tests that converter-layer TabNotFoundError and MultipleTabsError
are correctly caught and mapped to structured MCP error responses
by all tool modules: tabs, sections, navigation, formatting.
"""

from __future__ import annotations

import pytest

from extended_google_doc_utils.converter.exceptions import (
    MultipleTabsError,
    TabNotFoundError,
)

AVAILABLE_TABS = [
    ("t.0", "Alabama", 0),
    ("t.1", "Britain", 1),
    ("t.2", "California", 2),
]


def _call_tool(tool_path: str, mock_converter, error, mock_attr: str):
    """Import and call a tool, after setting side_effect on the mock."""
    import importlib

    module_path, func_name = tool_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)

    getattr(mock_converter, mock_attr).side_effect = error

    # Build kwargs based on which tool we're calling
    kwargs = {"document_id": "doc1"}
    if func_name in ("read_tab", "write_tab"):
        kwargs["tab_id"] = "t.bogus"
    if func_name == "write_tab":
        kwargs["content"] = "# Test"
    if func_name in ("read_section", "write_section"):
        kwargs["anchor_id"] = "h.abc"
        kwargs["tab_id"] = "t.bogus"
    if func_name == "write_section":
        kwargs["content"] = "## Test"
    if func_name == "get_hierarchy":
        kwargs["tab_id"] = "t.bogus"
    if func_name in (
        "normalize_formatting", "extract_styles",
    ):
        kwargs["tab_id"] = "t.bogus"

    return func(**kwargs)


# (tool_path, mock_attribute, description)
TAB_NOT_FOUND_CASES = [
    (
        "extended_google_doc_utils.mcp.tools.tabs.read_tab",
        "read_tab",
        "read_tab",
    ),
    (
        "extended_google_doc_utils.mcp.tools.tabs.write_tab",
        "write_tab",
        "write_tab",
    ),
    (
        "extended_google_doc_utils.mcp.tools.sections.read_section",
        "read_section",
        "read_section",
    ),
    (
        "extended_google_doc_utils.mcp.tools.sections.write_section",
        "write_section",
        "write_section",
    ),
    (
        "extended_google_doc_utils.mcp.tools.navigation.get_hierarchy",
        "get_hierarchy",
        "get_hierarchy",
    ),
    (
        "extended_google_doc_utils.mcp.tools.formatting.normalize_formatting",
        "read_tab",
        "normalize_formatting",
    ),
    (
        "extended_google_doc_utils.mcp.tools.formatting.extract_styles",
        "read_tab",
        "extract_styles",
    ),
]


@pytest.mark.tier_b
class TestTabNotFoundError:
    @pytest.mark.parametrize(
        "tool_path,mock_attr,desc",
        TAB_NOT_FOUND_CASES,
        ids=[c[2] for c in TAB_NOT_FOUND_CASES],
    )
    def test_returns_structured_error(
        self,
        initialized_mcp_server,
        mock_converter,
        tool_path,
        mock_attr,
        desc,
    ):
        error = TabNotFoundError("t.bogus", AVAILABLE_TABS)
        result = _call_tool(
            tool_path, mock_converter, error, mock_attr
        )

        assert result["success"] is False
        assert "TabNotFoundError" in result["error"]["type"]
        assert "t.bogus" in result["error"]["message"]


MULTIPLE_TABS_CASES = [
    (
        "extended_google_doc_utils.mcp.tools.tabs.read_tab",
        "read_tab",
        "read_tab",
    ),
    (
        "extended_google_doc_utils.mcp.tools.tabs.write_tab",
        "write_tab",
        "write_tab",
    ),
    (
        "extended_google_doc_utils.mcp.tools.sections.read_section",
        "read_section",
        "read_section",
    ),
    (
        "extended_google_doc_utils.mcp.tools.navigation.get_hierarchy",
        "get_hierarchy",
        "get_hierarchy",
    ),
    (
        "extended_google_doc_utils.mcp.tools.formatting.normalize_formatting",
        "read_tab",
        "normalize_formatting",
    ),
]


@pytest.mark.tier_b
class TestMultipleTabsError:
    @pytest.mark.parametrize(
        "tool_path,mock_attr,desc",
        MULTIPLE_TABS_CASES,
        ids=[c[2] for c in MULTIPLE_TABS_CASES],
    )
    def test_returns_structured_error(
        self,
        initialized_mcp_server,
        mock_converter,
        tool_path,
        mock_attr,
        desc,
    ):
        error = MultipleTabsError(3, AVAILABLE_TABS)
        result = _call_tool(
            tool_path, mock_converter, error, mock_attr
        )

        assert result["success"] is False
        assert "MultipleTabsError" in result["error"]["type"]
        assert "3 tabs" in result["error"]["message"]
