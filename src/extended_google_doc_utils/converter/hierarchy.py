"""Hierarchy extraction for Google Docs.

Extracts heading structure from a Google Doc and formats it as
markdown with anchor IDs.
"""

from __future__ import annotations

from typing import Any

from extended_google_doc_utils.converter.types import HeadingAnchor, HierarchyResult

# Mapping from Google Docs named styles to heading levels
HEADING_STYLES = {
    "HEADING_1": 1,
    "HEADING_2": 2,
    "HEADING_3": 3,
    "HEADING_4": 4,
    "HEADING_5": 5,
    "HEADING_6": 6,
}


def extract_headings(body: dict[str, Any]) -> list[HeadingAnchor]:
    """Extract all headings from a document body.

    Headings are identified by their paragraphStyle.namedStyleType being
    one of HEADING_1 through HEADING_6. The anchor ID is from
    paragraphStyle.headingId.

    Args:
        body: The document body content from Google Docs API.

    Returns:
        List of HeadingAnchor objects in document order.
    """
    headings: list[HeadingAnchor] = []
    content = body.get("content", [])

    for element in content:
        if "paragraph" not in element:
            continue

        paragraph = element["paragraph"]
        style = paragraph.get("paragraphStyle", {})
        named_style = style.get("namedStyleType", "")

        if named_style not in HEADING_STYLES:
            continue

        # Extract heading info
        level = HEADING_STYLES[named_style]
        heading_id = style.get("headingId", "")
        start_index = element.get("startIndex", 0)

        # Extract heading text from paragraph elements
        text = extract_paragraph_text(paragraph)

        headings.append(
            HeadingAnchor(
                anchor_id=heading_id,
                level=level,
                text=text,
                start_index=start_index,
            )
        )

    return headings


def extract_paragraph_text(paragraph: dict[str, Any]) -> str:
    """Extract plain text from a paragraph.

    Args:
        paragraph: A paragraph element from Google Docs API.

    Returns:
        The concatenated text content of the paragraph.
    """
    parts: list[str] = []

    for element in paragraph.get("elements", []):
        if "textRun" in element:
            content = element["textRun"].get("content", "")
            # Strip trailing newline that Google Docs adds
            parts.append(content.rstrip("\n"))

    return "".join(parts)


def format_hierarchy(headings: list[HeadingAnchor]) -> str:
    """Format headings as markdown with anchors.

    Each heading is formatted as:
    ## {^ anchor_id}Heading Text

    Args:
        headings: List of HeadingAnchor objects.

    Returns:
        Markdown string with one heading per line.
    """
    lines: list[str] = []

    for heading in headings:
        prefix = "#" * heading.level
        anchor = f"{{^ {heading.anchor_id}}}" if heading.anchor_id else ""
        lines.append(f"{prefix} {anchor}{heading.text}")

    return "\n".join(lines)


def get_hierarchy(body: dict[str, Any]) -> HierarchyResult:
    """Get the heading hierarchy from a document body.

    Args:
        body: The document body content from Google Docs API.

    Returns:
        HierarchyResult with headings list and formatted markdown.
    """
    headings = extract_headings(body)
    markdown = format_hierarchy(headings)

    return HierarchyResult(headings=headings, markdown=markdown)
