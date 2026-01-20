"""Style reader for extracting document styles from Google Docs.

This module provides functions to read document-level properties and
effective/visible styles from Google Docs. The "effective style" captures
what the user actually sees - if paragraphs have inline overrides, those
overrides are returned instead of the named style definition.

Feature: 130-document-style-transfer
"""

from __future__ import annotations

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    OAuthCredentials,
)
from extended_google_doc_utils.converter.exceptions import (
    DocumentAccessError,
    MultipleTabsError,
    StyleReadError,
)
from extended_google_doc_utils.converter.tab_utils import (
    get_tab_content,
    get_tab_document_style,
    get_tab_named_styles,
    resolve_tab_id,
)
from extended_google_doc_utils.converter.types import (
    DocumentProperties,
    DocumentStyles,
    EffectiveStyle,
    NamedStyleType,
    ParagraphStyleProperties,
    RGBColor,
    StyleSource,
    TabReference,
    TextStyleProperties,
)


# =============================================================================
# T003: Module skeleton with API client setup
# =============================================================================


def _get_docs_service(credentials: OAuthCredentials | None = None):
    """Get Google Docs API service.

    Args:
        credentials: OAuth credentials. If None, uses default credential manager.

    Returns:
        Google Docs API service object.
    """
    if credentials is None:
        manager = CredentialManager()
        credentials = manager.get_credentials()

    from google.oauth2.credentials import Credentials as GoogleCredentials

    google_creds = GoogleCredentials(
        token=credentials.access_token,
        refresh_token=credentials.refresh_token,
        token_uri=credentials.token_uri,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scopes=credentials.scopes,
    )

    return build("docs", "v1", credentials=google_creds)


def _fetch_document(document_id: str, credentials: OAuthCredentials | None = None) -> dict:
    """Fetch a Google Doc by ID.

    Args:
        document_id: The Google Doc ID.
        credentials: OAuth credentials.

    Returns:
        The document dictionary from the API.

    Raises:
        DocumentAccessError: If the document cannot be accessed.
    """
    if not document_id:
        raise ValueError("document_id is required")

    try:
        service = _get_docs_service(credentials)
        return service.documents().get(
            documentId=document_id,
            includeTabsContent=True,
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise DocumentAccessError(document_id, "document not found")
        elif e.resp.status == 403:
            raise DocumentAccessError(document_id, "permission denied")
        else:
            raise DocumentAccessError(document_id, str(e))


# =============================================================================
# T004: Helper to extract RGB color from Google API color structures
# =============================================================================


def extract_rgb_color(color_obj: dict | None) -> RGBColor | None:
    """Extract RGB color from Google API color structure.

    Handles various color formats:
    - {"color": {"rgbColor": {"red": 0.5, "green": 0.5, "blue": 0.5}}}
    - {"rgbColor": {"red": 0.5, "green": 0.5, "blue": 0.5}}
    - {"color": {...}} nested structures

    Args:
        color_obj: Color object from Google Docs API.

    Returns:
        RGBColor if color is present, None otherwise.
    """
    if not color_obj:
        return None

    # Navigate nested "color" wrappers
    while "color" in color_obj and isinstance(color_obj["color"], dict):
        color_obj = color_obj["color"]

    # Extract rgbColor
    rgb = color_obj.get("rgbColor")
    if not rgb:
        return None

    return RGBColor(
        red=rgb.get("red", 0.0),
        green=rgb.get("green", 0.0),
        blue=rgb.get("blue", 0.0),
    )


# =============================================================================
# T005: Helper to extract document properties from documentStyle
# =============================================================================


def extract_document_properties(doc_style: dict | None) -> DocumentProperties:
    """Extract document-level properties from documentStyle.

    Args:
        doc_style: The documentStyle object from the API response.

    Returns:
        DocumentProperties with background, margins, and page size.
    """
    if not doc_style:
        return DocumentProperties()

    # Extract background color
    background = doc_style.get("background", {})
    background_color = extract_rgb_color(background.get("color"))

    # Helper to extract dimension magnitude in points
    def get_dimension_pt(dim: dict | None) -> float | None:
        if not dim:
            return None
        magnitude = dim.get("magnitude")
        if magnitude is None:
            return None
        unit = dim.get("unit", "PT")
        # Convert to points if needed (Google Docs uses PT internally)
        if unit == "PT":
            return float(magnitude)
        return float(magnitude)  # Assume PT for unknown units

    # Extract margins
    margin_top = get_dimension_pt(doc_style.get("marginTop"))
    margin_bottom = get_dimension_pt(doc_style.get("marginBottom"))
    margin_left = get_dimension_pt(doc_style.get("marginLeft"))
    margin_right = get_dimension_pt(doc_style.get("marginRight"))

    # Extract page size
    page_size = doc_style.get("pageSize", {})
    page_width = get_dimension_pt(page_size.get("width"))
    page_height = get_dimension_pt(page_size.get("height"))

    return DocumentProperties(
        background_color=background_color,
        margin_top_pt=margin_top,
        margin_bottom_pt=margin_bottom,
        margin_left_pt=margin_left,
        margin_right_pt=margin_right,
        page_width_pt=page_width,
        page_height_pt=page_height,
    )


# =============================================================================
# T006: Helper to extract named style definitions from namedStyles
# =============================================================================


def extract_named_style_definitions(
    named_styles: dict | None,
) -> dict[NamedStyleType, tuple[TextStyleProperties, ParagraphStyleProperties]]:
    """Extract named style definitions from namedStyles.

    Args:
        named_styles: The namedStyles object from the API response.

    Returns:
        Dict mapping style type to (text_style, paragraph_style) tuple.
    """
    result: dict[NamedStyleType, tuple[TextStyleProperties, ParagraphStyleProperties]] = {}

    if not named_styles:
        return result

    styles_list = named_styles.get("styles", [])

    for style in styles_list:
        style_type_str = style.get("namedStyleType")
        if not style_type_str:
            continue

        # Check if this is one of the 9 supported types
        try:
            style_type = NamedStyleType(style_type_str)
        except ValueError:
            continue  # Skip unknown style types

        text_style = _extract_text_style_properties(style.get("textStyle", {}))
        para_style = _extract_paragraph_style_properties(style.get("paragraphStyle", {}))

        result[style_type] = (text_style, para_style)

    return result


def _extract_text_style_properties(text_style: dict) -> TextStyleProperties:
    """Extract TextStyleProperties from a textStyle dict."""
    # Font family and weight
    weighted_font = text_style.get("weightedFontFamily", {})
    font_family = weighted_font.get("fontFamily")
    font_weight = weighted_font.get("weight")

    # Font size
    font_size = text_style.get("fontSize", {})
    font_size_pt = font_size.get("magnitude") if font_size else None

    # Colors
    text_color = extract_rgb_color(text_style.get("foregroundColor"))
    highlight_color = extract_rgb_color(text_style.get("backgroundColor"))

    # Boolean properties
    bold = text_style.get("bold")
    italic = text_style.get("italic")
    underline = text_style.get("underline")

    return TextStyleProperties(
        font_family=font_family,
        font_size_pt=font_size_pt,
        font_weight=font_weight,
        text_color=text_color,
        highlight_color=highlight_color,
        bold=bold,
        italic=italic,
        underline=underline,
    )


def _extract_paragraph_style_properties(para_style: dict) -> ParagraphStyleProperties:
    """Extract ParagraphStyleProperties from a paragraphStyle dict."""

    def get_dimension_pt(dim: dict | None) -> float | None:
        if not dim:
            return None
        magnitude = dim.get("magnitude")
        return float(magnitude) if magnitude is not None else None

    # Alignment
    alignment = para_style.get("alignment")

    # Line spacing (stored as percentage, convert to multiplier)
    line_spacing_raw = para_style.get("lineSpacing")
    line_spacing = float(line_spacing_raw) / 100.0 if line_spacing_raw else None

    # Spacing
    space_before = get_dimension_pt(para_style.get("spaceAbove"))
    space_after = get_dimension_pt(para_style.get("spaceBelow"))

    # Indentation
    indent_start = get_dimension_pt(para_style.get("indentStart"))
    indent_end = get_dimension_pt(para_style.get("indentEnd"))
    first_line_indent = get_dimension_pt(para_style.get("indentFirstLine"))

    return ParagraphStyleProperties(
        alignment=alignment,
        line_spacing=line_spacing,
        space_before_pt=space_before,
        space_after_pt=space_after,
        indent_start_pt=indent_start,
        indent_end_pt=indent_end,
        first_line_indent_pt=first_line_indent,
    )


# =============================================================================
# T007: Helper to find paragraphs by namedStyleType in document body
# =============================================================================


def find_paragraphs_by_style_type(
    body: dict,
) -> dict[NamedStyleType, list[dict]]:
    """Find all paragraphs grouped by their namedStyleType.

    Args:
        body: The document body object from the API.

    Returns:
        Dict mapping style type to list of paragraph elements.
    """
    result: dict[NamedStyleType, list[dict]] = {
        style_type: [] for style_type in NamedStyleType
    }

    content = body.get("content", [])

    for element in content:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue

        para_style = paragraph.get("paragraphStyle", {})
        style_type_str = para_style.get("namedStyleType")

        if not style_type_str:
            continue

        try:
            style_type = NamedStyleType(style_type_str)
            result[style_type].append(paragraph)
        except ValueError:
            continue  # Skip unknown style types

    return result


# =============================================================================
# T008: Helper to extract effective text/paragraph style from a paragraph element
# =============================================================================


def _merge_text_styles(
    base: TextStyleProperties, override: TextStyleProperties
) -> TextStyleProperties:
    """Merge two TextStyleProperties, with override taking precedence.

    For each property, if the override has a non-None value, use it;
    otherwise use the base value.
    """
    return TextStyleProperties(
        font_family=override.font_family if override.font_family is not None else base.font_family,
        font_size_pt=override.font_size_pt if override.font_size_pt is not None else base.font_size_pt,
        font_weight=override.font_weight if override.font_weight is not None else base.font_weight,
        text_color=override.text_color if override.text_color is not None else base.text_color,
        highlight_color=override.highlight_color if override.highlight_color is not None else base.highlight_color,
        bold=override.bold if override.bold is not None else base.bold,
        italic=override.italic if override.italic is not None else base.italic,
        underline=override.underline if override.underline is not None else base.underline,
    )


def _merge_paragraph_styles(
    base: ParagraphStyleProperties, override: ParagraphStyleProperties
) -> ParagraphStyleProperties:
    """Merge two ParagraphStyleProperties, with override taking precedence."""
    return ParagraphStyleProperties(
        alignment=override.alignment if override.alignment is not None else base.alignment,
        line_spacing=override.line_spacing if override.line_spacing is not None else base.line_spacing,
        space_before_pt=override.space_before_pt if override.space_before_pt is not None else base.space_before_pt,
        space_after_pt=override.space_after_pt if override.space_after_pt is not None else base.space_after_pt,
        indent_start_pt=override.indent_start_pt if override.indent_start_pt is not None else base.indent_start_pt,
        indent_end_pt=override.indent_end_pt if override.indent_end_pt is not None else base.indent_end_pt,
        first_line_indent_pt=override.first_line_indent_pt if override.first_line_indent_pt is not None else base.first_line_indent_pt,
    )


def extract_effective_style_from_paragraph(
    paragraph: dict,
    style_definition: tuple[TextStyleProperties, ParagraphStyleProperties] | None = None,
) -> tuple[TextStyleProperties, ParagraphStyleProperties]:
    """Extract effective text and paragraph style from a paragraph element.

    This captures the actual formatting visible to the user by merging the
    named style definition with any inline overrides.

    Args:
        paragraph: A paragraph element from document body content.
        style_definition: Optional (text_style, para_style) tuple from named style.
            If provided, inline overrides are merged on top of this base.

    Returns:
        Tuple of (text_style, paragraph_style) representing effective formatting.
    """
    # Extract paragraph style from the paragraph element
    para_style_dict = paragraph.get("paragraphStyle", {})
    para_style_override = _extract_paragraph_style_properties(para_style_dict)

    # For text style, look at the first text run
    elements = paragraph.get("elements", [])
    text_style_override = TextStyleProperties()  # Default empty

    for element in elements:
        text_run = element.get("textRun")
        if text_run:
            text_style_dict = text_run.get("textStyle", {})
            text_style_override = _extract_text_style_properties(text_style_dict)
            break  # Use first text run's style

    # Merge with style definition if provided
    if style_definition:
        base_text, base_para = style_definition
        text_style = _merge_text_styles(base_text, text_style_override)
        para_style = _merge_paragraph_styles(base_para, para_style_override)
    else:
        text_style = text_style_override
        para_style = para_style_override

    return text_style, para_style


# =============================================================================
# T014: Main function - read_document_styles()
# =============================================================================


def read_document_styles(
    document_id: str,
    credentials: OAuthCredentials | None = None,
    tab_id: str = "",
) -> DocumentStyles:
    """Read document-level properties and effective styles from a Google Doc.

    Args:
        document_id: The Google Doc ID (from URL or API).
        credentials: OAuth credentials. If None, uses default credential manager.
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs or first tab.

    Returns:
        DocumentStyles containing:
        - document_properties: Background, margins, page size
        - effective_styles: Dict of NamedStyleType → EffectiveStyle for all 9 types

    Raises:
        DocumentAccessError: If API call fails (permissions, invalid ID, etc.)
        MultipleTabsError: If tab_id is empty and document has multiple tabs.
        ValueError: If document_id is empty or invalid format
    """
    # Fetch document
    doc = _fetch_document(document_id, credentials)

    # Resolve tab_id for multi-tab support
    tab_ref = TabReference(document_id=document_id, tab_id=tab_id)
    resolved_tab_id = resolve_tab_id(doc, tab_ref)

    # Extract document properties from tab-level documentStyle (FR-035)
    # Each tab can have different page settings (background, margins, page size)
    doc_style = get_tab_document_style(doc, resolved_tab_id)
    doc_properties = extract_document_properties(doc_style)

    # Extract named style definitions from tab-level namedStyles
    named_styles = get_tab_named_styles(doc, resolved_tab_id)
    style_definitions = extract_named_style_definitions(named_styles)

    # Find all paragraphs by style type from the specific tab
    body = get_tab_content(doc, resolved_tab_id)
    paragraphs_by_type = find_paragraphs_by_style_type(body)

    # Build effective styles for all 9 types
    effective_styles: dict[NamedStyleType, EffectiveStyle] = {}

    for style_type in NamedStyleType:
        paragraphs = paragraphs_by_type.get(style_type, [])

        # Get the style definition for this type (if available)
        style_def = style_definitions.get(style_type)

        if paragraphs:
            # Use first paragraph's effective style, merged with style definition
            text_style, para_style = extract_effective_style_from_paragraph(
                paragraphs[0], style_definition=style_def
            )
            source = StyleSource.PARAGRAPH_SAMPLE
        else:
            # Fall back to style definition
            if style_def:
                text_style, para_style = style_def
            else:
                # No definition found, use empty defaults
                text_style = TextStyleProperties()
                para_style = ParagraphStyleProperties()
            source = StyleSource.STYLE_DEFINITION

        effective_styles[style_type] = EffectiveStyle(
            style_type=style_type,
            text_style=text_style,
            paragraph_style=para_style,
            source=source,
        )

    return DocumentStyles(
        document_id=document_id,
        document_properties=doc_properties,
        effective_styles=effective_styles,
    )


# =============================================================================
# T015: read_effective_style() for single style type
# =============================================================================


def read_effective_style(
    document_id: str,
    style_type: NamedStyleType,
    credentials: OAuthCredentials | None = None,
    tab_id: str = "",
) -> EffectiveStyle:
    """Read the effective/visible style for a specific named style type.

    Analyzes actual paragraphs in the document to determine what the user sees.
    Falls back to style definition if no paragraphs of that type exist.

    Args:
        document_id: The Google Doc ID.
        style_type: Which named style to read (e.g., NamedStyleType.HEADING_1).
        credentials: OAuth credentials. If None, uses default credential manager.
        tab_id: Tab ID for multi-tab documents. Empty for single-tab docs or first tab.

    Returns:
        EffectiveStyle with text and paragraph properties, plus source indicator.

    Raises:
        DocumentAccessError: If API call fails.
        MultipleTabsError: If tab_id is empty and document has multiple tabs.
    """
    # For efficiency, we could optimize to only fetch what we need,
    # but for now we reuse read_document_styles
    styles = read_document_styles(document_id, credentials, tab_id)
    style = styles.get_style(style_type)

    if style is None:
        raise StyleReadError(
            document_id, f"Style type {style_type.value} not found in document"
        )

    return style
