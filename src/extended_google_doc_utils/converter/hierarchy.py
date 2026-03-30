"""Hierarchy extraction for Google Docs.

Extracts heading structure from a Google Doc and formats it as
markdown with anchor IDs.
"""

from __future__ import annotations

import bisect
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


def _count_all_sections(
    body: dict[str, Any], sections: list,
) -> dict[int, tuple[int, int]]:
    """Count words and characters for all sections in a single pass.

    Walks body elements once, accumulating text per section based on
    start_index boundaries. Returns a mapping from section start_index
    to (word_count, char_count).

    Args:
        body: The document body content from Google Docs API.
        sections: List of Section objects with start_index/end_index.

    Returns:
        Dict mapping section start_index to (word_count, char_count).
    """
    if not sections:
        return {}

    # Sort sections by start_index for binary-search assignment
    sorted_sections = sorted(sections, key=lambda s: s.start_index)
    boundaries = [s.start_index for s in sorted_sections]
    # Accumulate text per section (keyed by index into sorted_sections)
    text_buckets: dict[int, list[str]] = {i: [] for i in range(len(sorted_sections))}

    for element in body.get("content", []):
        if "paragraph" not in element:
            continue

        for para_el in element["paragraph"].get("elements", []):
            if "textRun" not in para_el:
                continue

            pe_start = para_el.get("startIndex", 0)
            pe_end = para_el.get("endIndex", 0)
            text = para_el["textRun"].get("content", "")

            # Find which section(s) this text run belongs to.
            # bisect_right gives the index after the last boundary <= pe_start.
            idx = bisect.bisect_right(boundaries, pe_start) - 1
            if idx < 0:
                idx = 0

            section = sorted_sections[idx]
            if pe_start >= section.end_index:
                continue

            # Clip text if it partially overlaps section boundary
            if pe_start < section.start_index:
                text = text[section.start_index - pe_start:]
            if pe_end > section.end_index:
                text = text[:-(pe_end - section.end_index)]

            text_buckets[idx].append(text)

    # Compute counts from accumulated text
    result: dict[int, tuple[int, int]] = {}
    for i, section in enumerate(sorted_sections):
        full_text = "".join(text_buckets[i]).strip()
        if full_text:
            result[section.start_index] = (len(full_text.split()), len(full_text))
        else:
            result[section.start_index] = (0, 0)

    return result


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
        word_hint = f" ({heading.word_count} words)" if heading.word_count > 0 else ""
        lines.append(f"{prefix} {anchor}{heading.text}{word_hint}")

    return "\n".join(lines)


def get_hierarchy(body: dict[str, Any]) -> HierarchyResult:
    """Get the heading hierarchy from a document body.

    Args:
        body: The document body content from Google Docs API.

    Returns:
        HierarchyResult with headings list and formatted markdown.
    """
    # Lazy import to avoid circular dependency (section_utils imports HEADING_STYLES)
    from extended_google_doc_utils.converter.section_utils import get_all_sections

    headings = extract_headings(body)
    sections = get_all_sections(body)

    # Count all sections in a single pass over body content
    counts = _count_all_sections(body, sections)

    total_word_count = 0
    total_char_count = 0

    # Add preamble counts to totals (not attributed to any heading)
    preamble = next((s for s in sections if s.is_preamble), None)
    if preamble:
        pw, pc = counts.get(preamble.start_index, (0, 0))
        total_word_count += pw
        total_char_count += pc

    # Populate counts on each heading (HeadingAnchor is frozen, create new instances)
    counted_headings: list[HeadingAnchor] = []
    for h in headings:
        wc, cc = counts.get(h.start_index, (0, 0))
        total_word_count += wc
        total_char_count += cc
        counted_headings.append(
            HeadingAnchor(
                anchor_id=h.anchor_id,
                level=h.level,
                text=h.text,
                start_index=h.start_index,
                word_count=wc,
                char_count=cc,
            )
        )

    markdown = format_hierarchy(counted_headings)

    return HierarchyResult(
        headings=counted_headings,
        markdown=markdown,
        total_word_count=total_word_count,
        total_char_count=total_char_count,
    )
