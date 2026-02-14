"""Mock MCP tool responses for testing without Google Docs API."""

from __future__ import annotations

from typing import Any


class UnknownToolError(Exception):
    """Raised when a mock response is requested for an unknown tool."""


# Realistic mock responses for each MCP tool.
# These are detailed enough that an LLM can continue its workflow.
_MOCK_RESPONSES: dict[str, dict[str, Any]] = {
    "list_documents": {
        "success": True,
        "documents": [
            {
                "document_id": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
                "title": "Project Status Report",
                "last_modified": "2026-02-10T14:30:00Z",
                "owner": "user@example.com",
            },
            {
                "document_id": "2xYzAbCdEfGhIjKlMnOpQrStUv",
                "title": "Company Style Guide",
                "last_modified": "2026-02-08T09:15:00Z",
                "owner": "user@example.com",
            },
            {
                "document_id": "3qWeRtYuIoPlKjHgFdSaZxCvBn",
                "title": "Meeting Notes - Q1 Planning",
                "last_modified": "2026-02-12T16:45:00Z",
                "owner": "user@example.com",
            },
        ],
        "total_count": 3,
    },
    "get_metadata": {
        "success": True,
        "document_id": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
        "title": "Project Status Report",
        "tabs": [
            {"tab_id": "t.0", "title": "Main", "index": 0},
            {"tab_id": "t.1", "title": "Appendix", "index": 1},
        ],
        "can_edit": True,
        "can_comment": True,
    },
    "get_hierarchy": {
        "success": True,
        "headings": [
            {"anchor_id": "h.abc123", "level": 1, "text": "Introduction"},
            {"anchor_id": "h.def456", "level": 1, "text": "Weekly Status"},
            {"anchor_id": "h.ghi789", "level": 2, "text": "Completed Tasks"},
            {"anchor_id": "h.jkl012", "level": 2, "text": "In Progress"},
            {"anchor_id": "h.mno345", "level": 1, "text": "Budget Analysis"},
            {"anchor_id": "h.pqr678", "level": 1, "text": "Next Steps"},
        ],
        "markdown": (
            "# Introduction\n"
            "# Weekly Status\n"
            "## Completed Tasks\n"
            "## In Progress\n"
            "# Budget Analysis\n"
            "# Next Steps\n"
        ),
    },
    "export_section": {
        "success": True,
        "content": (
            "# Weekly Status\n\n"
            "This week we completed the API integration and started testing.\n\n"
            "## Completed Tasks\n\n"
            "- API endpoint implementation\n"
            "- Database migration\n\n"
            "## In Progress\n\n"
            "- Frontend integration\n"
            "- Load testing\n"
        ),
        "anchor_id": "h.def456",
        "warnings": [],
    },
    "import_section": {
        "success": True,
        "anchor_id": "h.def456",
        "preserved_objects": [],
        "warnings": [],
    },
    "export_tab": {
        "success": True,
        "content": (
            "# Project Status Report\n\n"
            "## Introduction\n\n"
            "This document tracks the current project status.\n\n"
            "## Weekly Status\n\n"
            "All tasks on track for Q1 deadline.\n\n"
            "## Budget Analysis\n\n"
            "Budget utilization at 65%.\n\n"
            "## Next Steps\n\n"
            "- Complete frontend\n- Deploy to staging\n"
        ),
        "tab_id": "t.0",
        "warnings": [],
    },
    "import_tab": {
        "success": True,
        "tab_id": "t.0",
        "preserved_objects": [],
        "warnings": [],
    },
    "normalize_formatting": {
        "success": True,
        "changes_made": 42,
        "warnings": [],
    },
    "extract_styles": {
        "success": True,
        "styles": [
            {
                "element_type": "NORMAL_TEXT",
                "font_family": "Arial",
                "font_size": "11pt",
                "font_weight": "normal",
                "text_color": "#000000",
                "line_spacing": "1.15",
                "space_before": "0pt",
                "space_after": "0pt",
            },
            {
                "element_type": "HEADING_1",
                "font_family": "Arial",
                "font_size": "20pt",
                "font_weight": "bold",
                "text_color": "#000000",
                "line_spacing": "1.15",
                "space_before": "20pt",
                "space_after": "6pt",
            },
        ],
        "source_document_id": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
    },
    "apply_styles": {
        "success": True,
        "changes_made": 15,
        "warnings": [],
    },
    "get_document_styles": {
        "success": True,
        "document_id": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
        "document_properties": {
            "background_color": "#ffffff",
            "margin_top": "72pt",
            "margin_bottom": "72pt",
            "margin_left": "72pt",
            "margin_right": "72pt",
            "page_width": "612pt",
            "page_height": "792pt",
        },
        "effective_styles": {
            "NORMAL_TEXT": {
                "font_family": "Arial",
                "font_size": "11pt",
                "font_weight": "normal",
                "foreground_color": "#000000",
            },
            "HEADING_1": {
                "font_family": "Arial",
                "font_size": "20pt",
                "font_weight": "bold",
                "foreground_color": "#000000",
            },
            "HEADING_2": {
                "font_family": "Arial",
                "font_size": "16pt",
                "font_weight": "bold",
                "foreground_color": "#000000",
            },
            "TITLE": {
                "font_family": "Arial",
                "font_size": "26pt",
                "font_weight": "normal",
                "foreground_color": "#000000",
            },
        },
    },
    "apply_document_styles": {
        "success": True,
        "document_properties_applied": True,
        "styles_applied": {
            "NORMAL_TEXT": {"paragraphs_updated": 24, "success": True},
            "HEADING_1": {"paragraphs_updated": 4, "success": True},
            "HEADING_2": {"paragraphs_updated": 6, "success": True},
        },
        "total_paragraphs_updated": 34,
        "errors": [],
    },
}

ALL_TOOL_NAMES = list(_MOCK_RESPONSES.keys())


def get_mock_response(tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Return a canned success response for an MCP tool.

    Args:
        tool_name: Name of the tool called.
        parameters: Parameters provided (used to customize some responses).

    Returns:
        Realistic mock response dict.

    Raises:
        UnknownToolError: If tool_name is not a known MCP tool.
    """
    if tool_name not in _MOCK_RESPONSES:
        raise UnknownToolError(f"Unknown MCP tool: {tool_name}")

    # Return a copy to prevent mutation
    response = _MOCK_RESPONSES[tool_name].copy()

    # Customize responses based on parameters where useful
    if tool_name == "get_metadata" and "document_id" in parameters:
        response = {**response, "document_id": parameters["document_id"]}
    elif tool_name == "export_section" and "anchor_id" in parameters:
        response = {**response, "anchor_id": parameters["anchor_id"]}
    elif tool_name == "import_section" and "anchor_id" in parameters:
        response = {**response, "anchor_id": parameters["anchor_id"]}
    elif tool_name == "export_tab" and "tab_id" in parameters:
        response = {**response, "tab_id": parameters["tab_id"]}
    elif tool_name == "import_tab" and "tab_id" in parameters:
        response = {**response, "tab_id": parameters["tab_id"]}
    elif tool_name == "get_document_styles" and "document_id" in parameters:
        response = {**response, "document_id": parameters["document_id"]}
    elif tool_name == "extract_styles" and "document_id" in parameters:
        response = {**response, "source_document_id": parameters["document_id"]}

    return response
