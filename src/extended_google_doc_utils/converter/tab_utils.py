"""Tab resolution utilities for Google Docs.

Handles resolving tab IDs and validating tab references for multi-tab documents.
"""

from __future__ import annotations

from typing import Any

from extended_google_doc_utils.converter.exceptions import MultipleTabsError
from extended_google_doc_utils.converter.types import TabReference


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
    """
    tabs = get_tabs(document)
    tab_count = len(tabs)

    if tab_count == 0:
        # No tabs info in document - assume single tab
        return tab_ref.tab_id

    if tab_ref.tab_id:
        # Specific tab requested - validate it exists
        tab_ids = [t.get("tabProperties", {}).get("tabId", "") for t in tabs]
        if tab_ref.tab_id not in tab_ids:
            # Tab ID not found, but we'll let the API handle the error
            pass
        return tab_ref.tab_id

    # Empty tab_id - check if single tab
    if tab_count == 1:
        # Return the single tab's ID
        return tabs[0].get("tabProperties", {}).get("tabId", "")

    # Multiple tabs require explicit tab_id
    raise MultipleTabsError(tab_count)


def get_tabs(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Get the list of tabs from a document.

    Args:
        document: The Google Docs API document response.

    Returns:
        List of tab objects, or empty list if no tabs info.
    """
    # The tabs are in document.tabs for multi-tab documents
    # For single-tab, the content is directly in document.body
    return document.get("tabs", [])


def get_tab_content(document: dict[str, Any], tab_id: str) -> dict[str, Any]:
    """Get the content body for a specific tab.

    Args:
        document: The Google Docs API document response.
        tab_id: The tab ID to get content for (empty for default).

    Returns:
        The content body for the tab.
    """
    tabs = get_tabs(document)

    if not tabs:
        # Single-tab document - content is in body
        return document.get("body", {})

    # Find the matching tab
    for tab in tabs:
        tab_props = tab.get("tabProperties", {})
        if tab_props.get("tabId", "") == tab_id:
            # Content is in tab.documentTab.body
            return tab.get("documentTab", {}).get("body", {})

    # Tab not found - fall back to first tab or body
    if tabs:
        return tabs[0].get("documentTab", {}).get("body", {})
    return document.get("body", {})


def get_tab_document_style(document: dict[str, Any], tab_id: str) -> dict[str, Any]:
    """Get the documentStyle for a specific tab.

    For multi-tab documents, each tab can have its own page settings
    (background color, margins, page size). This function returns the
    tab-specific documentStyle.

    Args:
        document: The Google Docs API document response.
        tab_id: The tab ID (empty for default).

    Returns:
        The documentStyle dict for the tab.
    """
    tabs = get_tabs(document)

    if not tabs:
        # Single-tab document - documentStyle is at top level
        return document.get("documentStyle", {})

    # Find the matching tab
    for tab in tabs:
        tab_props = tab.get("tabProperties", {})
        if tab_props.get("tabId", "") == tab_id:
            return tab.get("documentTab", {}).get("documentStyle", {})

    # Tab not found - fall back to first tab or top-level
    if tabs:
        return tabs[0].get("documentTab", {}).get("documentStyle", {})
    return document.get("documentStyle", {})


def get_tab_named_styles(document: dict[str, Any], tab_id: str) -> dict[str, Any]:
    """Get the namedStyles for a specific tab.

    Args:
        document: The Google Docs API document response.
        tab_id: The tab ID (empty for default).

    Returns:
        The namedStyles dict for the tab.
    """
    tabs = get_tabs(document)

    if not tabs:
        # Single-tab document - namedStyles is at top level
        return document.get("namedStyles", {})

    # Find the matching tab
    for tab in tabs:
        tab_props = tab.get("tabProperties", {})
        if tab_props.get("tabId", "") == tab_id:
            return tab.get("documentTab", {}).get("namedStyles", {})

    # Tab not found - fall back to first tab or top-level
    if tabs:
        return tabs[0].get("documentTab", {}).get("namedStyles", {})
    return document.get("namedStyles", {})


def get_inline_objects(document: dict[str, Any], tab_id: str) -> dict[str, Any]:
    """Get inline objects map for a specific tab.

    Args:
        document: The Google Docs API document response.
        tab_id: The tab ID (empty for default).

    Returns:
        Dict mapping object IDs to inline object data.
    """
    tabs = get_tabs(document)

    if not tabs:
        return document.get("inlineObjects", {})

    for tab in tabs:
        tab_props = tab.get("tabProperties", {})
        if tab_props.get("tabId", "") == tab_id:
            return tab.get("documentTab", {}).get("inlineObjects", {})

    if tabs:
        return tabs[0].get("documentTab", {}).get("inlineObjects", {})
    return document.get("inlineObjects", {})


def get_positioned_objects(document: dict[str, Any], tab_id: str) -> dict[str, Any]:
    """Get positioned objects map for a specific tab.

    Args:
        document: The Google Docs API document response.
        tab_id: The tab ID (empty for default).

    Returns:
        Dict mapping object IDs to positioned object data.
    """
    tabs = get_tabs(document)

    if not tabs:
        return document.get("positionedObjects", {})

    for tab in tabs:
        tab_props = tab.get("tabProperties", {})
        if tab_props.get("tabId", "") == tab_id:
            return tab.get("documentTab", {}).get("positionedObjects", {})

    if tabs:
        return tabs[0].get("documentTab", {}).get("positionedObjects", {})
    return document.get("positionedObjects", {})
