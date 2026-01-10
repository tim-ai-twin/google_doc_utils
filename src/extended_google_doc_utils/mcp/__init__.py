"""MCP (Model Context Protocol) server for Google Docs operations.

This module provides an MCP server that exposes Google Docs functionality
to LLMs through well-documented tools for section editing, formatting,
and document navigation.
"""

from extended_google_doc_utils.mcp.server import create_server, mcp

__all__ = ["create_server", "mcp"]
