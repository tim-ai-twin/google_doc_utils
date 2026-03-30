"""Tab resolution utilities for Google Docs.

Handles resolving tab IDs and validating tab references for multi-tab documents.
"""

from __future__ import annotations

from typing import Any

from extended_google_doc_utils.converter.exceptions import (
    MultipleTabsError,
    TabNotFoundError,
)
from extended_google_doc_utils.converter.types import TabReference


def _extract_available_tabs(
    tabs: list[dict[str, Any]],
) -> list[tuple[str, str, int]]:
    """Extract (tab_id, title, index) tuples from tab objects."""
    return [
        (
            t.get("tabProperties", {}).get("tabId", ""),
            t.get("tabProperties", {}).get("title", ""),
            t.get("tabProperties", {}).get("index", 0),
        )
        for t in tabs
    ]


def resolve_tab_id(document: dict[str, Any], tab_ref: TabReference) -> str:
    """Resolve the tab ID for a document.

    For single-tab documents, an empty tab_id is acceptable.
    For multi-tab documents, a specific tab_id must be provided.

    Args:
        document: The Google Docs API document response.
        tab_ref: Tab reference with potentially empty tab_id.

    Returns:
        The resolved tab ID.

    Raises:
        MultipleTabsError: If document has multiple tabs and tab_id is empty.
        TabNotFoundError: If the specified tab_id does not exist.
    """
    tabs = get_tabs(document)
    tab_count = len(tabs)

    if tab_count == 0:
        # No tabs info in document - assume single tab
        return tab_ref.tab_id

    if tab_ref.tab_id:
        # Specific tab requested - validate it exists
        tab_ids = [
            t.get("tabProperties", {}).get("tabId", "") for t in tabs
        ]
        if tab_ref.tab_id not in tab_ids:
            raise TabNotFoundError(
                tab_ref.tab_id, _extract_available_tabs(tabs)
            )
        return tab_ref.tab_id

    # Empty tab_id - check if single tab
    if tab_count == 1:
        return tabs[0].get("tabProperties", {}).get("tabId", "")

    # Multiple tabs require explicit tab_id
    raise MultipleTabsError(tab_count, _extract_available_tabs(tabs))


def get_tabs(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Get the list of tabs from a document.

    Args:
        document: The Google Docs API document response.

    Returns:
        List of tab objects, or empty list if no tabs info.
    """
    return document.get("tabs", [])


def _get_tab_property(
    document: dict[str, Any],
    tab_id: str,
    doc_key: str,
    tab_key: str | None = None,
) -> dict[str, Any]:
    """Get a property from a specific tab.

    Shared implementation for all tab property accessors.

    Args:
        document: The Google Docs API document response.
        tab_id: The tab ID (empty for legacy/single-tab fallback).
        doc_key: Top-level key in document dict (legacy path).
        tab_key: Key inside documentTab dict. Defaults to doc_key.

    Returns:
        The property dict for the tab.

    Raises:
        TabNotFoundError: If tab_id doesn't match any tab.
    """
    if tab_key is None:
        tab_key = doc_key

    tabs = get_tabs(document)

    if not tabs:
        return document.get(doc_key, {})

    for tab in tabs:
        if tab.get("tabProperties", {}).get("tabId", "") == tab_id:
            return tab.get("documentTab", {}).get(tab_key, {})

    raise TabNotFoundError(tab_id, _extract_available_tabs(tabs))


def get_tab_content(
    document: dict[str, Any], tab_id: str
) -> dict[str, Any]:
    """Get the content body for a specific tab."""
    return _get_tab_property(document, tab_id, "body")


def get_tab_document_style(
    document: dict[str, Any], tab_id: str
) -> dict[str, Any]:
    """Get the documentStyle for a specific tab."""
    return _get_tab_property(document, tab_id, "documentStyle")


def get_tab_named_styles(
    document: dict[str, Any], tab_id: str
) -> dict[str, Any]:
    """Get the namedStyles for a specific tab."""
    return _get_tab_property(document, tab_id, "namedStyles")


def get_inline_objects(
    document: dict[str, Any], tab_id: str
) -> dict[str, Any]:
    """Get inline objects map for a specific tab."""
    return _get_tab_property(document, tab_id, "inlineObjects")


def get_positioned_objects(
    document: dict[str, Any], tab_id: str
) -> dict[str, Any]:
    """Get positioned objects map for a specific tab."""
    return _get_tab_property(document, tab_id, "positionedObjects")
