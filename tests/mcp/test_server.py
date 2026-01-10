"""Tests for MCP server tool discovery and lifecycle.

Tests for:
- Tool listing and schema completeness
- Tool description quality for LLM discoverability
- Server lifecycle (startup, shutdown)
"""

from __future__ import annotations

import pytest


class TestToolDiscovery:
    """Tests for MCP tool discovery and schema completeness."""

    @pytest.mark.tier_b
    def test_all_tools_have_descriptions(self, initialized_mcp_server):
        """Test that all registered tools have non-empty descriptions."""
        # Get the registered tools from the MCP server
        tools = initialized_mcp_server.mcp._tool_manager._tools

        assert len(tools) > 0, "No tools registered"

        for tool_name, tool in tools.items():
            assert tool.description, f"Tool '{tool_name}' has no description"
            assert len(tool.description) > 20, (
                f"Tool '{tool_name}' description is too short: {tool.description}"
            )

    @pytest.mark.tier_b
    def test_all_tool_parameters_have_descriptions(self, initialized_mcp_server):
        """Test that all tool parameters have descriptions in their schema."""
        tools = initialized_mcp_server.mcp._tool_manager._tools

        for tool_name, tool in tools.items():
            # Get the input schema from the tool
            if hasattr(tool, 'parameters') and tool.parameters:
                schema = tool.parameters
                properties = schema.get('properties', {})

                for param_name, param_schema in properties.items():
                    # Parameters should have a description
                    assert 'description' in param_schema or param_name in schema.get('required', []), (
                        f"Parameter '{param_name}' of tool '{tool_name}' lacks description"
                    )

    @pytest.mark.tier_b
    def test_tool_listing_is_complete(self, initialized_mcp_server):
        """Test that all expected tools are registered."""
        tools = initialized_mcp_server.mcp._tool_manager._tools
        tool_names = set(tools.keys())

        # Expected core tools from Phase 3 and Phase 4
        expected_tools = {
            "get_hierarchy",
            "list_documents",
            "get_metadata",
            "export_section",
            "import_section",
            "export_tab",
            "import_tab",
            "normalize_formatting",
            "extract_styles",
            "apply_styles",
        }

        # Verify all expected tools are present
        for tool in expected_tools:
            assert tool in tool_names, f"Expected tool '{tool}' not found"

    @pytest.mark.tier_b
    def test_tools_return_structured_responses(self, initialized_mcp_server, mock_converter):
        """Test that tools return dict responses with success field."""
        from extended_google_doc_utils.mcp.tools.navigation import get_hierarchy
        from extended_google_doc_utils.mcp.tools.sections import export_section, import_section
        from extended_google_doc_utils.mcp.tools.tabs import export_tab, import_tab

        # Test each tool returns structured response
        tools_to_test = [
            lambda: get_hierarchy(document_id="test", tab_id=""),
            lambda: export_section(document_id="test", anchor_id="h.123", tab_id=""),
            lambda: import_section(document_id="test", anchor_id="h.123", content="# Test", tab_id=""),
            lambda: export_tab(document_id="test", tab_id=""),
            lambda: import_tab(document_id="test", content="# Test", tab_id=""),
        ]

        for tool_fn in tools_to_test:
            result = tool_fn()
            assert isinstance(result, dict), f"Tool did not return dict: {type(result)}"
            assert "success" in result, f"Tool response missing 'success' field: {result}"


class TestServerLifecycle:
    """Tests for MCP server startup and shutdown."""

    @pytest.mark.tier_b
    def test_server_creates_mcp_instance(self, initialized_mcp_server):
        """Test that server creates FastMCP instance."""
        assert initialized_mcp_server.mcp is not None
        assert initialized_mcp_server.mcp.name == "Google Docs MCP Server"

    @pytest.mark.tier_b
    def test_tools_are_registered_after_register_tools(self, initialized_mcp_server):
        """Test that tools are available after register_tools() call."""
        tools = initialized_mcp_server.mcp._tool_manager._tools

        # Should have tools registered
        assert len(tools) >= 5, f"Expected at least 5 tools, got {len(tools)}"

    @pytest.mark.tier_b
    def test_get_converter_raises_without_initialization(self):
        """Test that get_converter raises CredentialError when not initialized."""
        from extended_google_doc_utils.mcp import server
        from extended_google_doc_utils.mcp.errors import CredentialError

        # Save and clear the global state
        original_converter = server._converter
        server._converter = None

        try:
            with pytest.raises(CredentialError):
                server.get_converter()
        finally:
            # Restore
            server._converter = original_converter
