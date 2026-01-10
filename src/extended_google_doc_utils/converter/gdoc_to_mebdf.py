"""Google Docs to MEBDF Converter.

Converts Google Docs API document structure to MEBDF markdown format.
This module handles:
- Text extraction with formatting
- Anchor extraction (headings, bookmarks, comments)
- Embedded object detection and placeholder generation
- List and table conversion
"""

from __future__ import annotations

from typing import Any

from extended_google_doc_utils.converter.hierarchy import (
    HEADING_STYLES,
    extract_paragraph_text,
)
from extended_google_doc_utils.converter.mebdf_parser import (
    BoldNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    ListItemNode,
    ListNode,
    ParagraphNode,
    TextNode,
)
from extended_google_doc_utils.converter.mebdf_serializer import MebdfSerializer
from extended_google_doc_utils.converter.tab_utils import (
    get_inline_objects,
    get_positioned_objects,
)
from extended_google_doc_utils.converter.types import (
    Anchor,
    AnchorType,
    EmbeddedObject,
    EmbeddedObjectType,
    ExportResult,
    Section,
)


def export_body(
    document: dict[str, Any], body: dict[str, Any], tab_id: str
) -> ExportResult:
    """Export entire document body to MEBDF.

    Args:
        document: Full document from API.
        body: Document body content.
        tab_id: Tab ID for object lookup.

    Returns:
        ExportResult with MEBDF content.
    """
    inline_objects = get_inline_objects(document, tab_id)
    positioned_objects = get_positioned_objects(document, tab_id)

    content_elements = body.get("content", [])
    ast, anchors, embedded, warnings = convert_elements(
        content_elements, inline_objects, positioned_objects
    )

    serializer = MebdfSerializer()
    mebdf_content = serializer.serialize(ast)

    return ExportResult(
        content=mebdf_content,
        anchors=anchors,
        embedded_objects=embedded,
        warnings=warnings,
    )


def export_section(
    document: dict[str, Any],
    body: dict[str, Any],
    tab_id: str,
    section: Section,
) -> ExportResult:
    """Export a specific section to MEBDF.

    Args:
        document: Full document from API.
        body: Document body content.
        tab_id: Tab ID for object lookup.
        section: Section boundaries.

    Returns:
        ExportResult with MEBDF content for the section.
    """
    inline_objects = get_inline_objects(document, tab_id)
    positioned_objects = get_positioned_objects(document, tab_id)

    # Filter elements within section boundaries
    content_elements = body.get("content", [])
    section_elements = [
        e
        for e in content_elements
        if e.get("startIndex", 0) >= section.start_index
        and e.get("startIndex", 0) < section.end_index
    ]

    ast, anchors, embedded, warnings = convert_elements(
        section_elements, inline_objects, positioned_objects
    )

    serializer = MebdfSerializer()
    mebdf_content = serializer.serialize(ast)

    return ExportResult(
        content=mebdf_content,
        anchors=anchors,
        embedded_objects=embedded,
        warnings=warnings,
    )


def convert_elements(
    elements: list[dict[str, Any]],
    inline_objects: dict[str, Any],
    positioned_objects: dict[str, Any],
) -> tuple[DocumentNode, list[Anchor], list[EmbeddedObject], list[str]]:
    """Convert document elements to AST.

    Args:
        elements: List of document content elements.
        inline_objects: Map of inline object IDs to data.
        positioned_objects: Map of positioned object IDs to data.

    Returns:
        Tuple of (DocumentNode, anchors, embedded_objects, warnings).
    """
    children: list = []
    anchors: list[Anchor] = []
    embedded: list[EmbeddedObject] = []
    warnings: list[str] = []

    i = 0
    while i < len(elements):
        element = elements[i]

        if "paragraph" in element:
            paragraph = element["paragraph"]
            style = paragraph.get("paragraphStyle", {})
            named_style = style.get("namedStyleType", "")

            # Check for heading
            if named_style in HEADING_STYLES:
                level = HEADING_STYLES[named_style]
                heading_id = style.get("headingId")
                content, para_anchors, para_embedded, para_warnings = (
                    convert_paragraph_content(
                        paragraph, inline_objects, positioned_objects
                    )
                )

                if heading_id:
                    anchors.append(
                        Anchor(
                            anchor_id=heading_id,
                            anchor_type=AnchorType.HEADING,
                            start_index=element.get("startIndex", 0),
                        )
                    )

                children.append(
                    HeadingNode(level=level, anchor_id=heading_id, content=content)
                )
                anchors.extend(para_anchors)
                embedded.extend(para_embedded)
                warnings.extend(para_warnings)

            # Check for list
            elif "bullet" in paragraph:
                # Collect consecutive list items
                list_items, list_end_idx = collect_list_items(
                    elements, i, inline_objects, positioned_objects
                )
                # Determine if ordered
                bullet = paragraph.get("bullet", {})
                list_id = bullet.get("listId")
                is_ordered = is_list_ordered(elements, list_id) if list_id else False

                for item in list_items:
                    embedded.extend(item.get("embedded", []))
                    anchors.extend(item.get("anchors", []))
                    warnings.extend(item.get("warnings", []))

                children.append(
                    ListNode(
                        ordered=is_ordered,
                        items=[item["node"] for item in list_items],
                    )
                )
                i = list_end_idx
                continue

            # Regular paragraph
            else:
                content, para_anchors, para_embedded, para_warnings = (
                    convert_paragraph_content(
                        paragraph, inline_objects, positioned_objects
                    )
                )
                if content:
                    children.append(ParagraphNode(content=content))
                anchors.extend(para_anchors)
                embedded.extend(para_embedded)
                warnings.extend(para_warnings)

        elif "table" in element:
            table_node, table_warnings = convert_table(element["table"])
            if table_node:
                children.append(table_node)
            warnings.extend(table_warnings)

        elif "sectionBreak" in element:
            # Section breaks are ignored in MEBDF
            pass

        elif "tableOfContents" in element:
            warnings.append("Table of contents not supported in MEBDF")

        i += 1

    return DocumentNode(children=children), anchors, embedded, warnings


def convert_paragraph_content(
    paragraph: dict[str, Any],
    inline_objects: dict[str, Any],
    positioned_objects: dict[str, Any],
) -> tuple[list, list[Anchor], list[EmbeddedObject], list[str]]:
    """Convert paragraph elements to AST nodes.

    Args:
        paragraph: Paragraph element.
        inline_objects: Map of inline object IDs.
        positioned_objects: Map of positioned object IDs.

    Returns:
        Tuple of (content_nodes, anchors, embedded_objects, warnings).
    """
    content: list = []
    anchors: list[Anchor] = []
    embedded: list[EmbeddedObject] = []
    warnings: list[str] = []

    for elem in paragraph.get("elements", []):
        start_index = elem.get("startIndex", 0)

        if "textRun" in elem:
            text_run = elem["textRun"]
            text = text_run.get("content", "").rstrip("\n")
            if not text:
                continue

            style = text_run.get("textStyle", {})
            node = convert_text_with_style(text, style, warnings)
            content.append(node)

        elif "inlineObjectElement" in elem:
            obj_elem = elem["inlineObjectElement"]
            obj_id = obj_elem.get("inlineObjectId")

            if obj_id and obj_id in inline_objects:
                obj_data = inline_objects[obj_id]
                obj_type = detect_embedded_type(obj_data)
                content.append(EmbeddedObjectNode(object_id=obj_id, object_type=obj_type))
                embedded.append(
                    EmbeddedObject(
                        object_id=obj_id,
                        object_type=EmbeddedObjectType(obj_type),
                        start_index=start_index,
                    )
                )

        elif "richLink" in elem:
            rich_link = elem["richLink"]
            link_id = rich_link.get("richLinkId")
            props = rich_link.get("richLinkProperties", {})
            uri = props.get("uri", "")

            # Detect if it's a video
            if "youtube.com" in uri or "youtu.be" in uri:
                obj_type = "video"
            else:
                obj_type = "embed"

            content.append(EmbeddedObjectNode(object_id=link_id, object_type=obj_type))
            embedded.append(
                EmbeddedObject(
                    object_id=link_id,
                    object_type=EmbeddedObjectType.VIDEO
                    if obj_type == "video"
                    else EmbeddedObjectType.EMBED,
                    start_index=start_index,
                )
            )

        elif "equation" in elem:
            # Equations have no ID
            content.append(EmbeddedObjectNode(object_id=None, object_type="equation"))
            embedded.append(
                EmbeddedObject(
                    object_id=None,
                    object_type=EmbeddedObjectType.EQUATION,
                    start_index=start_index,
                )
            )

    # Check for positioned objects
    for obj_id in paragraph.get("positionedObjectIds", []):
        if obj_id in positioned_objects:
            obj_data = positioned_objects[obj_id]
            obj_type = detect_positioned_type(obj_data)
            content.append(EmbeddedObjectNode(object_id=obj_id, object_type=obj_type))
            embedded.append(
                EmbeddedObject(
                    object_id=obj_id,
                    object_type=EmbeddedObjectType(obj_type),
                    start_index=0,
                )
            )

    return content, anchors, embedded, warnings


def convert_text_with_style(text: str, style: dict[str, Any], warnings: list[str]):
    """Convert text with formatting style to AST node.

    Args:
        text: The text content.
        style: The textStyle from Google Docs.
        warnings: List to append warnings to.

    Returns:
        AST node (TextNode, BoldNode, etc. or FormattingNode).
    """
    is_bold = style.get("bold", False)
    is_italic = style.get("italic", False)
    is_underline = style.get("underline", False)
    is_strikethrough = style.get("strikethrough", False)

    # Get colors
    fg_color = style.get("foregroundColor", {}).get("color", {}).get("rgbColor", {})
    bg_color = style.get("backgroundColor", {}).get("color", {}).get("rgbColor", {})

    # Get font
    font_family = style.get("weightedFontFamily", {}).get("fontFamily", "")
    is_mono = font_family.lower() in ("roboto mono", "consolas", "courier new", "monospace")

    # Check for unsupported formatting
    if is_strikethrough:
        warnings.append(f"Strikethrough not supported: '{text[:20]}...'")

    # Build the node
    base_node = TextNode(text)

    # Wrap with formatting as needed
    node = base_node

    # Standard markdown formatting
    if is_bold and is_italic:
        node = BoldNode(content=[ItalicNode(content=[node])])
    elif is_bold:
        node = BoldNode(content=[node])
    elif is_italic:
        node = ItalicNode(content=[node])

    # MEBDF extensions
    mebdf_props: dict[str, str | bool] = {}

    if is_underline:
        mebdf_props["underline"] = True

    if is_mono:
        mebdf_props["mono"] = True

    if bg_color:
        hex_color = rgb_to_hex(bg_color)
        if hex_color:
            mebdf_props["highlight"] = hex_color

    if fg_color:
        hex_color = rgb_to_hex(fg_color)
        if hex_color and hex_color != "#000000":
            mebdf_props["color"] = hex_color

    if mebdf_props:
        node = FormattingNode(properties=mebdf_props, content=[node])

    return node


def rgb_to_hex(rgb: dict[str, float]) -> str | None:
    """Convert RGB color dict to hex string.

    Args:
        rgb: Dict with 'red', 'green', 'blue' keys (0-1 floats).

    Returns:
        Hex color string like '#ff0000', or None if empty.
    """
    if not rgb:
        return None

    r = int(rgb.get("red", 0) * 255)
    g = int(rgb.get("green", 0) * 255)
    b = int(rgb.get("blue", 0) * 255)

    return f"#{r:02x}{g:02x}{b:02x}"


def detect_embedded_type(obj_data: dict[str, Any]) -> str:
    """Detect the type of an inline embedded object.

    Args:
        obj_data: The inline object data from document.

    Returns:
        Type string: 'image', 'drawing', 'chart', etc.
    """
    props = obj_data.get("inlineObjectProperties", {})
    embedded = props.get("embeddedObject", {})

    if "linkedContentReference" in embedded:
        linked = embedded["linkedContentReference"]
        if "sheetsChartReference" in linked:
            return "chart"

    if "embeddedDrawingProperties" in embedded:
        return "drawing"

    if "imageProperties" in embedded:
        return "image"

    return "embed"


def detect_positioned_type(obj_data: dict[str, Any]) -> str:
    """Detect the type of a positioned embedded object.

    Args:
        obj_data: The positioned object data from document.

    Returns:
        Type string: 'image', 'drawing', 'chart', etc.
    """
    props = obj_data.get("positionedObjectProperties", {})
    embedded = props.get("embeddedObject", {})

    if "linkedContentReference" in embedded:
        linked = embedded["linkedContentReference"]
        if "sheetsChartReference" in linked:
            return "chart"

    if "embeddedDrawingProperties" in embedded:
        return "drawing"

    if "imageProperties" in embedded:
        return "image"

    return "embed"


def collect_list_items(
    elements: list[dict[str, Any]],
    start_idx: int,
    inline_objects: dict[str, Any],
    positioned_objects: dict[str, Any],
) -> tuple[list[dict], int]:
    """Collect consecutive list items.

    Args:
        elements: All document elements.
        start_idx: Index of first list item.
        inline_objects: Inline objects map.
        positioned_objects: Positioned objects map.

    Returns:
        Tuple of (list of item dicts, end index).
    """
    items = []
    i = start_idx

    while i < len(elements):
        element = elements[i]
        if "paragraph" not in element:
            break

        paragraph = element["paragraph"]
        if "bullet" not in paragraph:
            break

        bullet = paragraph.get("bullet", {})
        nesting_level = bullet.get("nestingLevel", 0)

        content, anchors, embedded, warnings = convert_paragraph_content(
            paragraph, inline_objects, positioned_objects
        )

        items.append(
            {
                "node": ListItemNode(content=content, indent_level=nesting_level),
                "anchors": anchors,
                "embedded": embedded,
                "warnings": warnings,
            }
        )

        i += 1

    return items, i


def is_list_ordered(elements: list[dict[str, Any]], list_id: str) -> bool:
    """Check if a list is ordered or unordered.

    This is a heuristic - we'd need the full document.lists to be certain.

    Args:
        elements: Document elements.
        list_id: The list ID.

    Returns:
        True if ordered, False if unordered.
    """
    # Default to unordered - would need document.lists for accurate detection
    return False


def convert_table(table: dict[str, Any]) -> tuple[ParagraphNode | None, list[str]]:
    """Convert a Google Docs table to markdown table.

    Note: Complex tables may not convert well to markdown.

    Args:
        table: Table element from document.

    Returns:
        Tuple of (table node, warnings).
    """
    warnings = []
    rows = table.get("tableRows", [])

    if not rows:
        return None, warnings

    # Convert to simple markdown table representation
    table_lines = []

    for row_idx, row in enumerate(rows):
        cells = row.get("tableCells", [])
        cell_texts = []

        for cell in cells:
            cell_content = cell.get("content", [])
            cell_text = ""
            for elem in cell_content:
                if "paragraph" in elem:
                    cell_text += extract_paragraph_text(elem["paragraph"]) + " "
            cell_texts.append(cell_text.strip())

        table_lines.append("| " + " | ".join(cell_texts) + " |")

        # Add header separator after first row
        if row_idx == 0:
            separator = "| " + " | ".join(["---"] * len(cell_texts)) + " |"
            table_lines.append(separator)

    # Return as a paragraph containing the table text
    return ParagraphNode(content=[TextNode("\n".join(table_lines))]), warnings
