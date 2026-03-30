"""Tests for read_tab format parameter.

Tests:
- format="mebdf" returns MEBDF (backward compat)
- format="plain" returns plain markdown
- Invalid format value returns error
- Default format is "mebdf"
"""

from __future__ import annotations

import pytest

from extended_google_doc_utils.converter.types import ExportResult


class TestReadTabFormat:
    """Tests for the format parameter on read_tab MCP tool."""

    @pytest.mark.tier_b
    def test_default_format_is_mebdf(self, initialized_mcp_server, mock_converter):
        """Default format should be 'mebdf'."""
        from extended_google_doc_utils.mcp.tools.tabs import read_tab

        result = read_tab(document_id="test_doc_123", tab_id="")

        assert result["success"] is True
        assert result["format"] == "mebdf"

    @pytest.mark.tier_b
    def test_explicit_mebdf_format(self, initialized_mcp_server, mock_converter):
        """Explicitly passing format='mebdf' returns MEBDF content."""
        from extended_google_doc_utils.mcp.tools.tabs import read_tab

        result = read_tab(document_id="test_doc_123", tab_id="", format="mebdf")

        assert result["success"] is True
        assert result["format"] == "mebdf"
        assert "content" in result
        mock_converter.read_tab.assert_called_once()
        _, kwargs = mock_converter.read_tab.call_args
        assert kwargs["format"] == "mebdf"

    @pytest.mark.tier_b
    def test_plain_format(self, initialized_mcp_server, mock_converter):
        """Passing format='plain' returns plain markdown content."""
        from extended_google_doc_utils.mcp.tools.tabs import read_tab

        mock_converter.read_tab.return_value = ExportResult(
            content="# Introduction\n\nSome content here.",
            anchors=[],
            embedded_objects=[],
            warnings=[],
        )

        result = read_tab(document_id="test_doc_123", tab_id="", format="plain")

        assert result["success"] is True
        assert result["format"] == "plain"
        assert "content" in result
        mock_converter.read_tab.assert_called_once()
        _, kwargs = mock_converter.read_tab.call_args
        assert kwargs["format"] == "plain"

    @pytest.mark.tier_b
    def test_invalid_format_returns_error(self, initialized_mcp_server, mock_converter):
        """Invalid format value returns a structured error response."""
        from extended_google_doc_utils.mcp.tools.tabs import read_tab

        result = read_tab(document_id="test_doc_123", tab_id="", format="html")

        assert result["success"] is False
        assert "error" in result
        assert "html" in result["error"]["message"]

    @pytest.mark.tier_b
    def test_format_echoed_in_response(self, initialized_mcp_server, mock_converter):
        """The format value is echoed back in the response."""
        from extended_google_doc_utils.mcp.tools.tabs import read_tab

        for fmt in ("mebdf", "plain"):
            # Reset mock
            mock_converter.read_tab.return_value = ExportResult(
                content="content",
                anchors=[],
                embedded_objects=[],
                warnings=[],
            )

            result = read_tab(document_id="test_doc_123", tab_id="", format=fmt)

            assert result["success"] is True
            assert result["format"] == fmt

    @pytest.mark.tier_b
    def test_backward_compat_no_format_param(self, initialized_mcp_server, mock_converter):
        """Calling without format parameter works (backward compat)."""
        from extended_google_doc_utils.mcp.tools.tabs import read_tab

        result = read_tab(document_id="test_doc_123")

        assert result["success"] is True
        assert result["format"] == "mebdf"
        assert "content" in result
