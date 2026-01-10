"""MEBDF to Google Docs Converter.

Converts MEBDF markdown AST to Google Docs API batchUpdate requests.
This module handles:
- Text insertion with formatting
- Heading and paragraph style application
- Anchor preservation and creation
- Embedded object validation
"""

from __future__ import annotations

from typing import Any

from extended_google_doc_utils.converter.exceptions import EmbeddedObjectNotFoundError
from extended_google_doc_utils.converter.mebdf_parser import (
    AnchorNode,
    BlockFormattingNode,
    BoldNode,
    CodeBlockNode,
    CodeSpanNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    LinkNode,
    ListItemNode,
    ListNode,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.tab_utils import (
    get_inline_objects,
    get_positioned_objects,
)
from extended_google_doc_utils.converter.types import Section


def build_import_requests(
    document: dict[str, Any],
    body: dict[str, Any],
    tab_id: str,
    ast: DocumentNode,
    replace_all: bool = True,
) -> tuple[list[dict], list[str], list[str]]:
    """Build Google Docs API requests to import MEBDF content.

    Args:
        document: Full document from API.
        body: Document body content.
        tab_id: Tab ID.
        ast: Parsed MEBDF AST.
        replace_all: If True, delete all content first.

    Returns:
        Tuple of (requests, preserved_object_ids, warnings).
    """
    requests: list[dict] = []
    preserved: list[str] = []
    warnings: list[str] = []

    inline_objects = get_inline_objects(document, tab_id)
    positioned_objects = get_positioned_objects(document, tab_id)
    all_objects = {**inline_objects, **positioned_objects}

    # If replacing all, delete existing content first
    if replace_all:
        content = body.get("content", [])
        if len(content) > 1:
            # Get document end index (exclude final newline)
            last_elem = content[-1]
            end_index = last_elem.get("endIndex", 1) - 1

            if end_index > 1:
                requests.append(
                    {
                        "deleteContentRange": {
                            "range": {"startIndex": 1, "endIndex": end_index}
                        }
                    }
                )

    # Build content insertion requests
    insert_index = 1
    text_content, style_requests, obj_preserved, obj_warnings = serialize_ast_to_requests(
        ast, insert_index, all_objects
    )

    if text_content:
        requests.append({"insertText": {"location": {"index": 1}, "text": text_content}})
        requests.extend(style_requests)

    preserved.extend(obj_preserved)
    warnings.extend(obj_warnings)

    return requests, preserved, warnings


def build_section_import_requests(
    document: dict[str, Any],
    body: dict[str, Any],
    tab_id: str,
    section: Section,
    ast: DocumentNode,
) -> tuple[list[dict], list[str], list[str]]:
    """Build requests to import MEBDF content into a specific section.

    Args:
        document: Full document from API.
        body: Document body content.
        tab_id: Tab ID.
        section: Section boundaries.
        ast: Parsed MEBDF AST.

    Returns:
        Tuple of (requests, preserved_object_ids, warnings).
    """
    requests: list[dict] = []
    preserved: list[str] = []
    warnings: list[str] = []

    inline_objects = get_inline_objects(document, tab_id)
    positioned_objects = get_positioned_objects(document, tab_id)
    all_objects = {**inline_objects, **positioned_objects}

    # Delete section content first (keeping heading if not preamble)
    start = section.start_index
    end = section.end_index - 1  # Exclude final newline

    if end > start:
        requests.append(
            {"deleteContentRange": {"range": {"startIndex": start, "endIndex": end}}}
        )

    # Build content insertion
    text_content, style_requests, obj_preserved, obj_warnings = serialize_ast_to_requests(
        ast, start, all_objects
    )

    if text_content:
        requests.append(
            {"insertText": {"location": {"index": start}, "text": text_content}}
        )
        requests.extend(style_requests)

    preserved.extend(obj_preserved)
    warnings.extend(obj_warnings)

    return requests, preserved, warnings


def serialize_ast_to_requests(
    ast: DocumentNode, start_index: int, available_objects: dict[str, Any]
) -> tuple[str, list[dict], list[str], list[str]]:
    """Serialize AST to text and style requests.

    Args:
        ast: Document AST.
        start_index: Starting index for insertions.
        available_objects: Map of available embedded object IDs.

    Returns:
        Tuple of (text_content, style_requests, preserved_ids, warnings).
    """
    text_parts: list[str] = []
    style_requests: list[dict] = []
    preserved: list[str] = []
    warnings: list[str] = []

    current_index = start_index

    for child in ast.children:
        result = serialize_node(child, current_index, available_objects, warnings)
        if result:
            text, styles, objs = result
            text_parts.append(text)
            style_requests.extend(styles)
            preserved.extend(objs)
            current_index += len(text)

    return "".join(text_parts), style_requests, preserved, warnings


def serialize_node(
    node, index: int, available_objects: dict[str, Any], warnings: list[str]
) -> tuple[str, list[dict], list[str]] | None:
    """Serialize a single AST node.

    Args:
        node: AST node.
        index: Current document index.
        available_objects: Available embedded objects.
        warnings: List to append warnings.

    Returns:
        Tuple of (text, style_requests, preserved_ids) or None.
    """
    if isinstance(node, TextNode):
        return node.content, [], []

    elif isinstance(node, ParagraphNode):
        text = ""
        styles = []
        preserved = []
        current = index

        for child in node.content:
            result = serialize_node(child, current, available_objects, warnings)
            if result:
                t, s, p = result
                text += t
                styles.extend(s)
                preserved.extend(p)
                current += len(t)

        return text + "\n", styles, preserved

    elif isinstance(node, HeadingNode):
        text = ""
        styles = []
        preserved = []
        current = index

        for child in node.content:
            result = serialize_node(child, current, available_objects, warnings)
            if result:
                t, s, p = result
                text += t
                styles.extend(s)
                preserved.extend(p)
                current += len(t)

        text += "\n"

        # Add heading style request
        heading_style = f"HEADING_{node.level}"
        styles.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": index, "endIndex": index + len(text)},
                    "paragraphStyle": {"namedStyleType": heading_style},
                    "fields": "namedStyleType",
                }
            }
        )

        return text, styles, preserved

    elif isinstance(node, BoldNode):
        text = ""
        styles = []
        preserved = []
        current = index

        for child in node.content:
            result = serialize_node(child, current, available_objects, warnings)
            if result:
                t, s, p = result
                text += t
                styles.extend(s)
                preserved.extend(p)
                current += len(t)

        # Add bold style
        styles.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": index, "endIndex": index + len(text)},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            }
        )

        return text, styles, preserved

    elif isinstance(node, ItalicNode):
        text = ""
        styles = []
        preserved = []
        current = index

        for child in node.content:
            result = serialize_node(child, current, available_objects, warnings)
            if result:
                t, s, p = result
                text += t
                styles.extend(s)
                preserved.extend(p)
                current += len(t)

        styles.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": index, "endIndex": index + len(text)},
                    "textStyle": {"italic": True},
                    "fields": "italic",
                }
            }
        )

        return text, styles, preserved

    elif isinstance(node, FormattingNode):
        text = ""
        styles = []
        preserved = []
        current = index

        for child in node.content:
            result = serialize_node(child, current, available_objects, warnings)
            if result:
                t, s, p = result
                text += t
                styles.extend(s)
                preserved.extend(p)
                current += len(t)

        # Apply formatting properties
        text_style: dict[str, Any] = {}
        fields = []

        props = node.properties
        if props.get("underline"):
            text_style["underline"] = True
            fields.append("underline")

        if "highlight" in props:
            # Would need to convert color name/hex to Google format
            warnings.append("Highlight color import not yet implemented")

        if "color" in props:
            # Would need to convert hex to Google format
            warnings.append("Text color import not yet implemented")

        if text_style:
            styles.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": index, "endIndex": index + len(text)},
                        "textStyle": text_style,
                        "fields": ",".join(fields),
                    }
                }
            )

        return text, styles, preserved

    elif isinstance(node, EmbeddedObjectNode):
        # Validate object exists
        if node.object_id is not None:
            if node.object_id not in available_objects:
                raise EmbeddedObjectNotFoundError(node.object_id, node.object_type)
            return "", [], [node.object_id]

        # Equation - no ID to validate
        return "", [], []

    elif isinstance(node, ListNode):
        text = ""
        styles = []
        preserved = []

        for item in node.items:
            if isinstance(item, ListItemNode):
                indent = "  " * item.indent_level
                if node.ordered:
                    count = len([i for i in node.items if isinstance(i, ListItemNode)])
                    bullet = f"{count}. "
                else:
                    bullet = "- "

                item_text = indent + bullet
                current = index + len(text) + len(item_text)

                for child in item.content:
                    result = serialize_node(child, current, available_objects, warnings)
                    if result:
                        t, s, p = result
                        item_text += t
                        styles.extend(s)
                        preserved.extend(p)
                        current += len(t)

                text += item_text + "\n"

        return text, styles, preserved

    elif isinstance(node, CodeBlockNode):
        text = f"```{node.language}\n{node.content}\n```\n"
        return text, [], []

    elif isinstance(node, CodeSpanNode):
        # Would apply monospace formatting
        return node.content, [], []

    elif isinstance(node, LinkNode):
        # Would need to apply link
        return node.text, [], []

    elif isinstance(node, AnchorNode):
        # Anchors don't produce text
        return "", [], []

    elif isinstance(node, BlockFormattingNode):
        # Block formatting doesn't produce text directly
        return "", [], []

    return None
