"""Section boundary utilities for Google Docs.

Provides utilities for finding and manipulating section boundaries
based on heading anchor IDs.
"""

from __future__ import annotations

from typing import Any

from extended_google_doc_utils.converter.hierarchy import (
    HEADING_STYLES,
)
from extended_google_doc_utils.converter.types import Section


def find_section(body: dict[str, Any], anchor_id: str) -> Section | None:
    """Find section boundaries for a given anchor ID.

    A section starts at the heading with the given anchor ID and extends
    until the next heading of equal or higher level (smaller number).

    For preamble (anchor_id=""), returns content from start to first heading.

    Args:
        body: The document body content from Google Docs API.
        anchor_id: The heading anchor ID, or empty string for preamble.

    Returns:
        Section object with boundaries, or None if anchor not found.
    """
    content = body.get("content", [])

    if anchor_id == "":
        # Preamble: from start to first heading
        return _find_preamble(content)

    return _find_heading_section(content, anchor_id)


def _find_preamble(content: list[dict[str, Any]]) -> Section:
    """Find the preamble section (content before first heading).

    Args:
        content: Document content elements.

    Returns:
        Section for preamble.
    """
    # Find the first heading
    for element in content:
        if "paragraph" in element:
            style = element["paragraph"].get("paragraphStyle", {})
            if style.get("namedStyleType", "") in HEADING_STYLES:
                # Found first heading - preamble ends here
                return Section(
                    anchor_id="",
                    level=0,
                    start_index=1,  # Start after document start
                    end_index=element.get("startIndex", 1),
                )

    # No headings - entire document is preamble
    if content:
        last_element = content[-1]
        end_index = last_element.get("endIndex", 1)
        return Section(anchor_id="", level=0, start_index=1, end_index=end_index)

    return Section(anchor_id="", level=0, start_index=1, end_index=1)


def _find_heading_section(
    content: list[dict[str, Any]], anchor_id: str
) -> Section | None:
    """Find section for a specific heading anchor.

    Args:
        content: Document content elements.
        anchor_id: The heading anchor ID to find.

    Returns:
        Section object, or None if anchor not found.
    """
    # First pass: find the target heading
    target_element = None
    target_level = 0
    target_start = 0

    for element in content:
        if "paragraph" not in element:
            continue

        paragraph = element["paragraph"]
        style = paragraph.get("paragraphStyle", {})
        named_style = style.get("namedStyleType", "")

        if named_style not in HEADING_STYLES:
            continue

        heading_id = style.get("headingId", "")
        if heading_id == anchor_id:
            target_element = element
            target_level = HEADING_STYLES[named_style]
            target_start = element.get("startIndex", 0)
            break

    if target_element is None:
        return None

    # Second pass: find where section ends
    found_target = False
    for element in content:
        if "paragraph" not in element:
            continue

        paragraph = element["paragraph"]
        style = paragraph.get("paragraphStyle", {})
        named_style = style.get("namedStyleType", "")

        if named_style not in HEADING_STYLES:
            continue

        heading_id = style.get("headingId", "")
        level = HEADING_STYLES[named_style]

        if heading_id == anchor_id:
            found_target = True
            continue

        if found_target and level <= target_level:
            # Found next same-or-higher level heading
            return Section(
                anchor_id=anchor_id,
                level=target_level,
                start_index=target_start,
                end_index=element.get("startIndex", target_start),
            )

    # No ending heading found - section goes to end of document
    if content:
        last_element = content[-1]
        end_index = last_element.get("endIndex", target_start)
        return Section(
            anchor_id=anchor_id,
            level=target_level,
            start_index=target_start,
            end_index=end_index,
        )

    return Section(
        anchor_id=anchor_id,
        level=target_level,
        start_index=target_start,
        end_index=target_start,
    )


def get_all_sections(body: dict[str, Any]) -> list[Section]:
    """Get all sections in a document.

    Args:
        body: The document body content from Google Docs API.

    Returns:
        List of Section objects for all sections including preamble.
    """
    sections: list[Section] = []
    content = body.get("content", [])

    # Always start with preamble
    preamble = _find_preamble(content)
    if preamble.end_index > preamble.start_index:
        sections.append(preamble)

    # Find all headings and their sections
    headings: list[tuple[str, int, int]] = []  # (anchor_id, level, start_index)

    for element in content:
        if "paragraph" not in element:
            continue

        paragraph = element["paragraph"]
        style = paragraph.get("paragraphStyle", {})
        named_style = style.get("namedStyleType", "")

        if named_style not in HEADING_STYLES:
            continue

        headings.append(
            (
                style.get("headingId", ""),
                HEADING_STYLES[named_style],
                element.get("startIndex", 0),
            )
        )

    # Convert headings to sections
    for i, (anchor_id, level, start_index) in enumerate(headings):
        # Find end index
        end_index = None

        # Look for next same-or-higher level heading
        for j in range(i + 1, len(headings)):
            if headings[j][1] <= level:
                end_index = headings[j][2]
                break

        if end_index is None:
            # Last section extends to document end
            if content:
                end_index = content[-1].get("endIndex", start_index)
            else:
                end_index = start_index

        sections.append(
            Section(
                anchor_id=anchor_id,
                level=level,
                start_index=start_index,
                end_index=end_index,
            )
        )

    return sections
