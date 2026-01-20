"""Style writer for applying document styles to Google Docs.

This module provides functions to apply document-level properties and
effective styles to target Google Docs. Uses "style flattening" to apply
formatting inline since the Google Docs API does not support updating
named style definitions.

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
    StyleWriteError,
)
from extended_google_doc_utils.converter.tab_utils import (
    get_tab_content,
    resolve_tab_id,
)
from extended_google_doc_utils.converter.style_reader import (
    _fetch_document,
    _get_docs_service,
    find_paragraphs_by_style_type,
    read_document_styles,
)
from extended_google_doc_utils.converter.types import (
    DocumentProperties,
    DocumentStyles,
    EffectiveStyle,
    NamedStyleType,
    ParagraphStyleProperties,
    RGBColor,
    StyleApplicationResult,
    StyleSource,
    StyleTransferOptions,
    StyleTransferResult,
    TabReference,
    TextStyleProperties,
)


# =============================================================================
# T021: Helper to build UpdateDocumentStyle request
# =============================================================================


def build_update_document_style_request(props: DocumentProperties) -> dict | None:
    """Build UpdateDocumentStyle request from DocumentProperties.

    Args:
        props: Document properties to apply.

    Returns:
        API request dict, or None if no properties are set.
    """
    doc_style: dict = {}
    fields: list[str] = []

    # Background color
    if props.background_color is not None:
        doc_style["background"] = {
            "color": {
                "color": {
                    "rgbColor": {
                        "red": props.background_color.red,
                        "green": props.background_color.green,
                        "blue": props.background_color.blue,
                    }
                }
            }
        }
        fields.append("background")

    # Margins
    if props.margin_top_pt is not None:
        doc_style["marginTop"] = {"magnitude": props.margin_top_pt, "unit": "PT"}
        fields.append("marginTop")
    if props.margin_bottom_pt is not None:
        doc_style["marginBottom"] = {"magnitude": props.margin_bottom_pt, "unit": "PT"}
        fields.append("marginBottom")
    if props.margin_left_pt is not None:
        doc_style["marginLeft"] = {"magnitude": props.margin_left_pt, "unit": "PT"}
        fields.append("marginLeft")
    if props.margin_right_pt is not None:
        doc_style["marginRight"] = {"magnitude": props.margin_right_pt, "unit": "PT"}
        fields.append("marginRight")

    # Page size
    if props.page_width_pt is not None or props.page_height_pt is not None:
        page_size: dict = {}
        if props.page_width_pt is not None:
            page_size["width"] = {"magnitude": props.page_width_pt, "unit": "PT"}
        if props.page_height_pt is not None:
            page_size["height"] = {"magnitude": props.page_height_pt, "unit": "PT"}
        doc_style["pageSize"] = page_size
        fields.append("pageSize")

    if not fields:
        return None

    return {
        "updateDocumentStyle": {
            "documentStyle": doc_style,
            "fields": ",".join(fields),
        }
    }


# =============================================================================
# T029: Helper to build updateParagraphStyle request
# =============================================================================


def build_update_paragraph_style_request(
    start_index: int,
    end_index: int,
    para_style: ParagraphStyleProperties,
) -> dict | None:
    """Build updateParagraphStyle request from ParagraphStyleProperties.

    Args:
        start_index: Start of range.
        end_index: End of range.
        para_style: Paragraph style properties to apply.

    Returns:
        API request dict, or None if no properties are set.
    """
    style: dict = {}
    fields: list[str] = []

    # Alignment
    if para_style.alignment is not None:
        style["alignment"] = para_style.alignment
        fields.append("alignment")

    # Line spacing (convert multiplier to percentage)
    if para_style.line_spacing is not None:
        style["lineSpacing"] = int(para_style.line_spacing * 100)
        fields.append("lineSpacing")

    # Spacing
    if para_style.space_before_pt is not None:
        style["spaceAbove"] = {"magnitude": para_style.space_before_pt, "unit": "PT"}
        fields.append("spaceAbove")
    if para_style.space_after_pt is not None:
        style["spaceBelow"] = {"magnitude": para_style.space_after_pt, "unit": "PT"}
        fields.append("spaceBelow")

    # Indentation
    if para_style.indent_start_pt is not None:
        style["indentStart"] = {"magnitude": para_style.indent_start_pt, "unit": "PT"}
        fields.append("indentStart")
    if para_style.indent_end_pt is not None:
        style["indentEnd"] = {"magnitude": para_style.indent_end_pt, "unit": "PT"}
        fields.append("indentEnd")
    if para_style.first_line_indent_pt is not None:
        style["indentFirstLine"] = {
            "magnitude": para_style.first_line_indent_pt,
            "unit": "PT",
        }
        fields.append("indentFirstLine")

    if not fields:
        return None

    return {
        "updateParagraphStyle": {
            "range": {"startIndex": start_index, "endIndex": end_index},
            "paragraphStyle": style,
            "fields": ",".join(fields),
        }
    }


# =============================================================================
# T030: Helper to build updateTextStyle request
# =============================================================================


def build_update_text_style_request(
    start_index: int,
    end_index: int,
    text_style: TextStyleProperties,
) -> dict | None:
    """Build updateTextStyle request from TextStyleProperties.

    Args:
        start_index: Start of range.
        end_index: End of range.
        text_style: Text style properties to apply.

    Returns:
        API request dict, or None if no properties are set.
    """
    style: dict = {}
    fields: list[str] = []

    # Font family and weight
    if text_style.font_family is not None or text_style.font_weight is not None:
        weighted_font: dict = {}
        if text_style.font_family is not None:
            weighted_font["fontFamily"] = text_style.font_family
        if text_style.font_weight is not None:
            weighted_font["weight"] = text_style.font_weight
        style["weightedFontFamily"] = weighted_font
        fields.append("weightedFontFamily")

    # Font size
    if text_style.font_size_pt is not None:
        style["fontSize"] = {"magnitude": text_style.font_size_pt, "unit": "PT"}
        fields.append("fontSize")

    # Colors
    if text_style.text_color is not None:
        style["foregroundColor"] = {
            "color": {
                "rgbColor": {
                    "red": text_style.text_color.red,
                    "green": text_style.text_color.green,
                    "blue": text_style.text_color.blue,
                }
            }
        }
        fields.append("foregroundColor")

    if text_style.highlight_color is not None:
        style["backgroundColor"] = {
            "color": {
                "rgbColor": {
                    "red": text_style.highlight_color.red,
                    "green": text_style.highlight_color.green,
                    "blue": text_style.highlight_color.blue,
                }
            }
        }
        fields.append("backgroundColor")

    # Boolean properties
    if text_style.bold is not None:
        style["bold"] = text_style.bold
        fields.append("bold")
    if text_style.italic is not None:
        style["italic"] = text_style.italic
        fields.append("italic")
    if text_style.underline is not None:
        style["underline"] = text_style.underline
        fields.append("underline")

    if not fields:
        return None

    return {
        "updateTextStyle": {
            "range": {"startIndex": start_index, "endIndex": end_index},
            "textStyle": style,
            "fields": ",".join(fields),
        }
    }


# =============================================================================
# T027: Generate batch requests for all paragraphs of a style type
# =============================================================================


def generate_style_application_requests(
    paragraph_ranges: list[dict],
    effective_style: EffectiveStyle,
) -> list[dict]:
    """Generate API requests to apply effective style to paragraphs.

    Args:
        paragraph_ranges: List of dicts with startIndex and endIndex.
        effective_style: The style to apply.

    Returns:
        List of API requests (updateParagraphStyle and updateTextStyle).
    """
    requests: list[dict] = []

    for range_dict in paragraph_ranges:
        start = range_dict["startIndex"]
        end = range_dict["endIndex"]

        # Build paragraph style request
        para_request = build_update_paragraph_style_request(
            start, end, effective_style.paragraph_style
        )
        if para_request:
            requests.append(para_request)

        # Build text style request (uses paragraph range to preserve inline overrides)
        text_request = build_update_text_style_request(
            start, end, effective_style.text_style
        )
        if text_request:
            requests.append(text_request)

    return requests


# =============================================================================
# T031: Helper to find all paragraph ranges by style type
# =============================================================================


def find_paragraph_ranges_by_style_type(
    body: dict,
) -> dict[NamedStyleType, list[dict]]:
    """Find all paragraph ranges grouped by their namedStyleType.

    Args:
        body: The document body object from the API.

    Returns:
        Dict mapping style type to list of range dicts {startIndex, endIndex}.
    """
    result: dict[NamedStyleType, list[dict]] = {
        style_type: [] for style_type in NamedStyleType
    }

    content = body.get("content", [])

    for element in content:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue

        # Get paragraph range
        start_index = element.get("startIndex", 0)
        end_index = element.get("endIndex", start_index)

        para_style = paragraph.get("paragraphStyle", {})
        style_type_str = para_style.get("namedStyleType")

        if not style_type_str:
            continue

        try:
            style_type = NamedStyleType(style_type_str)
            result[style_type].append(
                {"startIndex": start_index, "endIndex": end_index}
            )
        except ValueError:
            continue

    return result


# =============================================================================
# T022: apply_document_properties()
# =============================================================================


def apply_document_properties(
    source_document_id: str,
    target_document_id: str,
    credentials: OAuthCredentials | None = None,
    source_tab_id: str = "",
    target_tab_id: str = "",
) -> bool:
    """Apply document-level properties from source to target.

    Transfers: background color, margins, page size.
    Does NOT transfer named styles.

    Note: Document properties are document-level (not tab-specific), but
    tab_id parameters are accepted for consistency with other functions.

    Args:
        source_document_id: Document to read properties from.
        target_document_id: Document to apply properties to.
        credentials: OAuth credentials.
        source_tab_id: Tab ID for source (for validation only, props are doc-level).
        target_tab_id: Tab ID for target (for validation only, props are doc-level).

    Returns:
        True if properties were applied successfully.

    Raises:
        DocumentAccessError: If API call fails.
        MultipleTabsError: If tab_id is empty and document has multiple tabs.
    """
    # Read source properties (tab_id validates multi-tab handling)
    source_styles = read_document_styles(source_document_id, credentials, source_tab_id)
    props = source_styles.document_properties

    # Build request
    request = build_update_document_style_request(props)
    if request is None:
        # No properties to apply
        return True

    # Execute request
    try:
        service = _get_docs_service(credentials)
        service.documents().batchUpdate(
            documentId=target_document_id, body={"requests": [request]}
        ).execute()
        return True
    except HttpError as e:
        if e.resp.status == 403:
            raise DocumentAccessError(target_document_id, "permission denied")
        raise StyleWriteError(target_document_id, str(e))


# =============================================================================
# T032: apply_effective_styles()
# =============================================================================


def apply_effective_styles(
    source_document_id: str,
    target_document_id: str,
    style_types: list[NamedStyleType] | None = None,
    credentials: OAuthCredentials | None = None,
    source_tab_id: str = "",
    target_tab_id: str = "",
) -> dict[NamedStyleType, StyleApplicationResult]:
    """Apply effective styles from source to target paragraphs.

    For each style type, finds all paragraphs of that type in target
    and applies the source's effective style formatting inline.

    Args:
        source_document_id: Document to read effective styles from.
        target_document_id: Document to apply styles to.
        style_types: Which styles to transfer. None = all 9 types.
        credentials: OAuth credentials.
        source_tab_id: Tab ID for source document. Empty for single-tab docs.
        target_tab_id: Tab ID for target document. Empty for single-tab docs.

    Returns:
        Dict mapping style type to application result (paragraphs updated).

    Raises:
        DocumentAccessError: If API call fails.
        MultipleTabsError: If tab_id is empty and document has multiple tabs.
    """
    # Default to all style types
    if style_types is None:
        style_types = list(NamedStyleType)

    # Read source styles with tab support
    source_styles = read_document_styles(source_document_id, credentials, source_tab_id)

    # Fetch target document to get paragraph ranges
    target_doc = _fetch_document(target_document_id, credentials)

    # Resolve target tab and get body from specific tab
    target_tab_ref = TabReference(document_id=target_document_id, tab_id=target_tab_id)
    resolved_target_tab_id = resolve_tab_id(target_doc, target_tab_ref)
    target_body = get_tab_content(target_doc, resolved_target_tab_id)
    target_ranges = find_paragraph_ranges_by_style_type(target_body)

    # Generate all requests
    all_requests: list[dict] = []
    results: dict[NamedStyleType, StyleApplicationResult] = {}

    for style_type in style_types:
        effective_style = source_styles.effective_styles.get(style_type)
        if effective_style is None:
            results[style_type] = StyleApplicationResult(
                style_type=style_type,
                paragraphs_updated=0,
                success=False,
                error="Style not found in source document",
            )
            continue

        ranges = target_ranges.get(style_type, [])
        requests = generate_style_application_requests(ranges, effective_style)
        all_requests.extend(requests)

        results[style_type] = StyleApplicationResult(
            style_type=style_type,
            paragraphs_updated=len(ranges),
            success=True,
        )

    # Execute all requests in one batch
    if all_requests:
        try:
            service = _get_docs_service(credentials)
            service.documents().batchUpdate(
                documentId=target_document_id, body={"requests": all_requests}
            ).execute()
        except HttpError as e:
            if e.resp.status == 403:
                raise DocumentAccessError(target_document_id, "permission denied")
            raise StyleWriteError(target_document_id, str(e))

    return results


# =============================================================================
# T033: apply_document_styles() - main function
# =============================================================================


def apply_document_styles(
    source_document_id: str,
    target_document_id: str,
    options: StyleTransferOptions | None = None,
    credentials: OAuthCredentials | None = None,
    source_tab_id: str = "",
    target_tab_id: str = "",
) -> StyleTransferResult:
    """Apply styles from source document to target document.

    Reads effective styles from source and applies them to all matching
    paragraphs in target. Uses "style flattening" - applies formatting inline
    since Google Docs API doesn't support updating named style definitions.

    Args:
        source_document_id: Document to read styles from.
        target_document_id: Document to apply styles to.
        options: Control what gets transferred. Default: all properties and styles.
        credentials: OAuth credentials. If None, uses default credential manager.
        source_tab_id: Tab ID for source document. Empty for single-tab docs or first tab.
        target_tab_id: Tab ID for target document. Empty for single-tab docs or first tab.

    Returns:
        StyleTransferResult with:
        - success: True if all operations completed
        - document_properties_applied: Whether doc properties were updated
        - styles_applied: Dict of style type → paragraphs updated
        - total_paragraphs_updated: Sum of all paragraph updates
        - errors: List of any error messages

    Raises:
        DocumentAccessError: If API call fails (permissions, invalid ID, etc.)
        MultipleTabsError: If tab_id is empty and document has multiple tabs.
        ValueError: If source and target document IDs are the same
    """
    # T049: Handle edge case - source/target same document
    if source_document_id == target_document_id:
        raise ValueError("Source and target document IDs cannot be the same")

    if options is None:
        options = StyleTransferOptions()

    errors: list[str] = []
    doc_props_applied = False
    styles_applied: dict[NamedStyleType, StyleApplicationResult] = {}
    total_updated = 0

    # Apply document properties if requested
    if options.include_document_properties:
        try:
            doc_props_applied = apply_document_properties(
                source_document_id,
                target_document_id,
                credentials,
                source_tab_id,
                target_tab_id,
            )
        except Exception as e:
            errors.append(f"Document properties: {str(e)}")

    # Apply effective styles if requested
    if options.include_effective_styles:
        try:
            styles_applied = apply_effective_styles(
                source_document_id,
                target_document_id,
                options.style_types,
                credentials,
                source_tab_id,
                target_tab_id,
            )
            total_updated = sum(
                r.paragraphs_updated for r in styles_applied.values() if r.success
            )
        except Exception as e:
            errors.append(f"Effective styles: {str(e)}")

    success = len(errors) == 0

    return StyleTransferResult(
        success=success,
        document_properties_applied=doc_props_applied,
        styles_applied=styles_applied,
        total_paragraphs_updated=total_updated,
        errors=errors,
    )
