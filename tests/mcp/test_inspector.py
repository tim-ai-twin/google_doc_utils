"""MCP Inspector-based tests for tool validation.

These tests simulate MCP inspector-style tool discovery and invocation
to validate the complete tool catalog.
"""

from __future__ import annotations

import pytest


class TestMCPInspector:
    """Tests that simulate MCP inspector tool discovery and invocation."""

    @pytest.mark.tier_b
    def test_list_all_tools(self, initialized_mcp_server):
        """Test that we can list all registered tools."""
        tools = initialized_mcp_server.mcp._tool_manager._tools

        # Should have at least 10 tools (all the ones we implemented)
        assert len(tools) >= 10

        # All tools should have names
        for name in tools:
            assert isinstance(name, str)
            assert len(name) > 0

    @pytest.mark.tier_b
    def test_all_tools_have_valid_schemas(self, initialized_mcp_server):
        """Test that all tools have valid JSON schemas for their parameters."""
        tools = initialized_mcp_server.mcp._tool_manager._tools

        for tool_name, tool in tools.items():
            # Each tool should have parameters defined
            assert hasattr(tool, 'parameters'), f"Tool {tool_name} has no parameters"

            if tool.parameters:
                # Schema should be a dict with 'properties'
                assert isinstance(tool.parameters, dict), f"Tool {tool_name} schema not a dict"
                assert 'properties' in tool.parameters or 'type' in tool.parameters, (
                    f"Tool {tool_name} schema missing properties/type"
                )

    @pytest.mark.tier_b
    def test_invoke_each_tool_validates_response(self, initialized_mcp_server, mock_converter):
        """Test invoking each tool and validating response structure."""
        from extended_google_doc_utils.mcp.tools.formatting import (
            apply_styles,
            extract_styles,
            normalize_formatting,
        )
        from extended_google_doc_utils.mcp.tools.navigation import (
            get_hierarchy,
            get_metadata,
            list_documents,
        )
        from extended_google_doc_utils.mcp.tools.sections import (
            export_section,
            import_section,
        )
        from extended_google_doc_utils.mcp.tools.tabs import (
            export_tab,
            import_tab,
        )

        # Define test invocations for each tool
        test_cases = [
            ("get_hierarchy", lambda: get_hierarchy(document_id="test", tab_id="")),
            ("list_documents", lambda: list_documents()),
            ("get_metadata", lambda: get_metadata(document_id="test")),
            ("export_section", lambda: export_section(document_id="test", anchor_id="h.1", tab_id="")),
            ("import_section", lambda: import_section(document_id="test", anchor_id="h.1", content="# Test", tab_id="")),
            ("export_tab", lambda: export_tab(document_id="test", tab_id="")),
            ("import_tab", lambda: import_tab(document_id="test", content="# Test", tab_id="")),
            ("normalize_formatting", lambda: normalize_formatting(document_id="test", body_font="Arial")),
            ("extract_styles", lambda: extract_styles(document_id="test")),
            ("apply_styles", lambda: apply_styles(document_id="test", styles=[])),
        ]

        for tool_name, invoke_fn in test_cases:
            result = invoke_fn()

            # All tools should return a dict
            assert isinstance(result, dict), f"Tool {tool_name} did not return dict"

            # All tools should have 'success' field
            assert 'success' in result, f"Tool {tool_name} response missing 'success'"

    @pytest.mark.tier_b
    def test_tool_descriptions_are_llm_friendly(self, initialized_mcp_server):
        """Test that tool descriptions are suitable for LLM consumption."""
        tools = initialized_mcp_server.mcp._tool_manager._tools

        for tool_name, tool in tools.items():
            description = tool.description

            # Description should exist and be non-empty
            assert description, f"Tool {tool_name} has no description"

            # Description should be at least 50 chars (meaningful content)
            assert len(description) > 50, (
                f"Tool {tool_name} description too short: {description}"
            )

            # Description should not contain TODO or FIXME
            assert 'TODO' not in description.upper(), (
                f"Tool {tool_name} description contains TODO"
            )
            assert 'FIXME' not in description.upper(), (
                f"Tool {tool_name} description contains FIXME"
            )


class TestPerformance:
    """Performance validation tests."""

    @pytest.mark.tier_b
    def test_tool_discovery_under_1_second(self, initialized_mcp_server):
        """Test that tool discovery completes in under 1 second."""
        import time

        start = time.time()

        # Simulate tool discovery by listing all tools
        tools = initialized_mcp_server.mcp._tool_manager._tools
        tool_list = list(tools.keys())

        elapsed = time.time() - start

        assert elapsed < 1.0, f"Tool discovery took {elapsed:.2f}s (should be <1s)"
        assert len(tool_list) >= 10

    @pytest.mark.tier_b
    def test_hierarchy_retrieval_under_3_seconds(self, initialized_mcp_server, mock_converter):
        """Test that hierarchy retrieval completes in under 3 seconds."""
        import time

        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy

        start = time.time()

        result = get_hierarchy(document_id="test_doc", tab_id="")

        elapsed = time.time() - start

        assert elapsed < 3.0, f"Hierarchy retrieval took {elapsed:.2f}s (should be <3s)"
        assert result["success"] is True
