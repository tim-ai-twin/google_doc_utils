"""MEBDF to Google Docs Converter.

Converts MEBDF markdown AST to Google Docs API batchUpdate requests.
This module handles:
- Text insertion with formatting
- Heading and paragraph style application
- Anchor preservation and creation
- Embedded object validation
"""

from __future__ import annotations

import re
from typing import Any

from extended_google_doc_utils.converter.exceptions import (
    EmbeddedObjectNotFoundError,
    FontValidationError,
)
from extended_google_doc_utils.converter.font_catalog import (
    validate_font_family,
    validate_font_weight,
)
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

# =============================================================================
# Color Conversion Utilities
# =============================================================================

# Named colors mapping to hex values
NAMED_COLORS = {
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "black": "#000000",
    "white": "#FFFFFF",
    "orange": "#FFA500",
    "purple": "#800080",
    "pink": "#FFC0CB",
    "gray": "#808080",
    "grey": "#808080",
    "brown": "#A52A2A",
    "navy": "#000080",
    "teal": "#008080",
    "lime": "#00FF00",
    "olive": "#808000",
    "maroon": "#800000",
    "aqua": "#00FFFF",
    "silver": "#C0C0C0",
    "fuchsia": "#FF00FF",
}


def hex_to_rgb_color(hex_color: str) -> dict[str, Any] | None:
    """Convert hex color to Google Docs API RGB color format.

    Args:
        hex_color: Color in #RRGGBB or #RGB format, or a named color.

    Returns:
        Google Docs API color dict with rgbColor, or None if invalid.
    """
    # Check for named color first
    if hex_color.lower() in NAMED_COLORS:
        hex_color = NAMED_COLORS[hex_color.lower()]

    # Handle hex colors
    if not hex_color.startswith("#"):
        return None

    hex_value = hex_color[1:]

    # Support both #RGB and #RRGGBB formats
    if len(hex_value) == 3:
        hex_value = "".join(c * 2 for c in hex_value)

    if len(hex_value) != 6 or not re.match(r"^[0-9a-fA-F]{6}$", hex_value):
        return None

    r = int(hex_value[0:2], 16) / 255.0
    g = int(hex_value[2:4], 16) / 255.0
    b = int(hex_value[4:6], 16) / 255.0

    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}


# Font weight name to numeric value mapping
FONT_WEIGHTS = {
    "thin": 100,
    "extralight": 200,
    "extra-light": 200,
    "light": 300,
    "normal": 400,
    "regular": 400,
    "medium": 500,
    "semibold": 600,
    "semi-bold": 600,
    "bold": 700,
    "extrabold": 800,
    "extra-bold": 800,
    "black": 900,
    "heavy": 900,
}


def parse_font_weight(weight_str: str) -> int | None:
    """Parse font weight string to numeric value.

    Args:
        weight_str: Weight name (e.g., "bold", "light") or numeric (e.g., "700").

    Returns:
        Numeric weight 100-900, or None if invalid.
    """
    # Try numeric first
    try:
        weight = int(weight_str)
        if 100 <= weight <= 900:
            return weight
        return None
    except ValueError:
        pass

    # Try named weight
    return FONT_WEIGHTS.get(weight_str.lower().replace(" ", ""))


def parse_font_size(size_str: str) -> dict[str, Any] | None:
    """Parse font size string to Google Docs format.

    Args:
        size_str: Size like "12pt", "14", or "10.5pt".

    Returns:
        Google Docs fontSize dict, or None if invalid.
    """
    # Remove 'pt' suffix if present
    size_str = size_str.lower().rstrip("pt").strip()

    try:
        magnitude = float(size_str)
        if magnitude > 0:
            return {"magnitude": magnitude, "unit": "PT"}
        return None
    except ValueError:
        return None


# Line spacing presets
LINE_SPACING_PRESETS = {
    "single": 1.0,
    "1.15": 1.15,
    "1.5": 1.5,
    "double": 2.0,
}


def parse_line_spacing(spacing_str: str) -> float | None:
    """Parse line spacing string to multiplier.

    Args:
        spacing_str: Spacing like "single", "1.5", "double", or a number.

    Returns:
        Line spacing multiplier, or None if invalid.
    """
    # Check presets first
    preset = LINE_SPACING_PRESETS.get(spacing_str.lower())
    if preset is not None:
        return preset

    # Try numeric
    try:
        spacing = float(spacing_str)
        if spacing > 0:
            return spacing
        return None
    except ValueError:
        return None


def parse_dimension(dim_str: str) -> dict[str, Any] | None:
    """Parse dimension string (e.g., "0.5in", "36pt") to Google Docs format.

    Args:
        dim_str: Dimension like "0.5in", "1in", "36pt".

    Returns:
        Google Docs dimension dict, or None if invalid.
    """
    dim_str = dim_str.lower().strip()

    # Parse unit and magnitude
    if dim_str.endswith("in"):
        unit = "PT"
        try:
            magnitude = float(dim_str[:-2]) * 72  # 1 inch = 72 points
        except ValueError:
            return None
    elif dim_str.endswith("pt"):
        unit = "PT"
        try:
            magnitude = float(dim_str[:-2])
        except ValueError:
            return None
    else:
        # Assume points if no unit
        unit = "PT"
        try:
            magnitude = float(dim_str)
        except ValueError:
            return None

    if magnitude >= 0:
        return {"magnitude": magnitude, "unit": unit}
    return None


# Alignment name mapping
ALIGNMENT_MAP = {
    "left": "START",
    "start": "START",
    "center": "CENTER",
    "right": "END",
    "end": "END",
    "justify": "JUSTIFIED",
    "justified": "JUSTIFIED",
}


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

        # Add heading style request BEFORE text styles so inline formatting
        # can override the heading's default text style
        heading_style = f"HEADING_{node.level}"
        styles.insert(
            0,
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": index, "endIndex": index + len(text)},
                    "paragraphStyle": {"namedStyleType": heading_style},
                    "fields": "namedStyleType",
                }
            },
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
            # Background/highlight color
            color_value = props["highlight"]
            if isinstance(color_value, str):
                rgb_color = hex_to_rgb_color(color_value)
                if rgb_color:
                    text_style["backgroundColor"] = rgb_color
                    fields.append("backgroundColor")
                else:
                    warnings.append(f"Invalid highlight color: {color_value}")

        if "color" in props:
            # Foreground/text color
            color_value = props["color"]
            if isinstance(color_value, str):
                rgb_color = hex_to_rgb_color(color_value)
                if rgb_color:
                    text_style["foregroundColor"] = rgb_color
                    fields.append("foregroundColor")
                else:
                    warnings.append(f"Invalid text color: {color_value}")

        # Handle font properties (font, weight, mono)
        font_family = None
        font_weight = 400  # Default weight

        if props.get("mono"):
            # mono shorthand uses Courier New, which is always valid
            font_family = "Courier New"
        elif "font" in props:
            font_value = props["font"]
            if isinstance(font_value, str):
                # Validate font family
                result = validate_font_family(font_value)
                if result.is_valid:
                    font_family = result.canonical_name
                else:
                    raise FontValidationError(
                        error_code=result.error_code or "INVALID_FONT_FAMILY",
                        message=result.error_message or f"Invalid font: {font_value}",
                        font_name=font_value,
                        suggestions=result.suggestions,
                    )

        if "weight" in props and font_family:
            weight_value = props["weight"]
            if isinstance(weight_value, str):
                # Validate weight for the font family
                result = validate_font_weight(font_family, weight_value)
                if result.is_valid:
                    font_weight = result.normalized_weight or 400
                else:
                    raise FontValidationError(
                        error_code=result.error_code or "INVALID_FONT_WEIGHT",
                        message=result.error_message or f"Invalid weight: {weight_value}",
                        font_name=font_family,
                        weight=weight_value,
                        suggestions=result.suggestions,
                    )
        elif "weight" in props:
            # Weight specified but no font - use parse_font_weight for validation
            weight_value = props["weight"]
            if isinstance(weight_value, str):
                parsed_weight = parse_font_weight(weight_value)
                if parsed_weight:
                    font_weight = parsed_weight
                else:
                    warnings.append(f"Invalid font weight: {weight_value}")

        if font_family:
            text_style["weightedFontFamily"] = {
                "fontFamily": font_family,
                "weight": font_weight,
            }
            fields.append("weightedFontFamily")

        if "size" in props:
            size_value = props["size"]
            if isinstance(size_value, str):
                font_size = parse_font_size(size_value)
                if font_size:
                    text_style["fontSize"] = font_size
                    fields.append("fontSize")
                else:
                    warnings.append(f"Invalid font size: {size_value}")

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

        # Handle paragraph-level properties
        para_style: dict[str, Any] = {}
        para_fields = []

        if "align" in props:
            align_value = props["align"]
            if isinstance(align_value, str):
                alignment = ALIGNMENT_MAP.get(align_value.lower())
                if alignment:
                    para_style["alignment"] = alignment
                    para_fields.append("alignment")
                else:
                    warnings.append(f"Invalid alignment: {align_value}")

        if "line-spacing" in props:
            spacing_value = props["line-spacing"]
            if isinstance(spacing_value, str):
                spacing = parse_line_spacing(spacing_value)
                if spacing:
                    # Google Docs uses 100-based percentages for line spacing
                    para_style["lineSpacing"] = spacing * 100
                    para_fields.append("lineSpacing")
                else:
                    warnings.append(f"Invalid line spacing: {spacing_value}")

        if "space-before" in props:
            space_value = props["space-before"]
            if isinstance(space_value, str):
                dimension = parse_dimension(space_value)
                if dimension:
                    para_style["spaceAbove"] = dimension
                    para_fields.append("spaceAbove")
                else:
                    warnings.append(f"Invalid space-before: {space_value}")

        if "space-after" in props:
            space_value = props["space-after"]
            if isinstance(space_value, str):
                dimension = parse_dimension(space_value)
                if dimension:
                    para_style["spaceBelow"] = dimension
                    para_fields.append("spaceBelow")
                else:
                    warnings.append(f"Invalid space-after: {space_value}")

        if "indent-left" in props:
            indent_value = props["indent-left"]
            if isinstance(indent_value, str):
                dimension = parse_dimension(indent_value)
                if dimension:
                    para_style["indentStart"] = dimension
                    para_fields.append("indentStart")
                else:
                    warnings.append(f"Invalid indent-left: {indent_value}")

        if "indent-right" in props:
            indent_value = props["indent-right"]
            if isinstance(indent_value, str):
                dimension = parse_dimension(indent_value)
                if dimension:
                    para_style["indentEnd"] = dimension
                    para_fields.append("indentEnd")
                else:
                    warnings.append(f"Invalid indent-right: {indent_value}")

        if "first-line-indent" in props:
            indent_value = props["first-line-indent"]
            if isinstance(indent_value, str):
                dimension = parse_dimension(indent_value)
                if dimension:
                    para_style["indentFirstLine"] = dimension
                    para_fields.append("indentFirstLine")
                else:
                    warnings.append(f"Invalid first-line-indent: {indent_value}")

        if para_style:
            styles.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": index, "endIndex": index + len(text)},
                        "paragraphStyle": para_style,
                        "fields": ",".join(para_fields),
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
        # Apply monospace formatting to inline code
        text = node.content
        styles = [
            {
                "updateTextStyle": {
                    "range": {"startIndex": index, "endIndex": index + len(text)},
                    "textStyle": {
                        "weightedFontFamily": {
                            "fontFamily": "Courier New",
                            "weight": 400,
                        }
                    },
                    "fields": "weightedFontFamily",
                }
            }
        ]
        return text, styles, []

    elif isinstance(node, LinkNode):
        # Apply hyperlink to text
        text = node.text
        styles = [
            {
                "updateTextStyle": {
                    "range": {"startIndex": index, "endIndex": index + len(text)},
                    "textStyle": {"link": {"url": node.url}},
                    "fields": "link",
                }
            }
        ]
        return text, styles, []

    elif isinstance(node, AnchorNode):
        # Anchors don't produce text
        return "", [], []

    elif isinstance(node, BlockFormattingNode):
        # Block formatting doesn't produce text directly
        return "", [], []

    return None
