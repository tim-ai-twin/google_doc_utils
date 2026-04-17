"""Probe script for the preamble/TITLE bug reproduction.

Reads the user's test doc and inspects what get_hierarchy/read_section return.
Does NOT mutate the document.
"""

from __future__ import annotations

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    CredentialSource,
)
from extended_google_doc_utils.converter import GoogleDocsConverter
from extended_google_doc_utils.converter.types import TabReference

DOC_ID = "19lqJVCK9W3Cu5A20ZfKGvV66C8TmSQRigwsS3iE7A3M"
TAB_ID = "t.526n9tkmsj2y"

HEADING_STYLES = {
    "HEADING_1", "HEADING_2", "HEADING_3",
    "HEADING_4", "HEADING_5", "HEADING_6",
}
SPECIAL_STYLES = {"TITLE", "SUBTITLE", "NORMAL_TEXT"}


def main() -> None:
    manager = CredentialManager(source=CredentialSource.LOCAL_FILE)
    creds = manager.load_credentials()
    assert creds is not None, "Missing credentials at .credentials/token.json"

    converter = GoogleDocsConverter(creds)
    tab = TabReference(document_id=DOC_ID, tab_id=TAB_ID)

    print("=" * 72)
    print("1. get_metadata()")
    print("=" * 72)
    meta = converter.get_metadata(DOC_ID)
    print(f"title: {meta.get('title')!r}")
    print(f"tabs ({len(meta.get('tabs', []))}):")
    for t in meta.get("tabs", []):
        print(f"  tab_id={t['tab_id']!r:20s} title={t['title']!r} index={t['index']}")

    print()
    print("=" * 72)
    print(f"2. get_hierarchy(tab_id={TAB_ID!r})")
    print("=" * 72)
    hierarchy = converter.get_hierarchy(tab)
    print(f"total_word_count: {hierarchy.total_word_count}")
    print(f"total_char_count: {hierarchy.total_char_count}")
    print(f"headings: {len(hierarchy.headings)}")
    for h in hierarchy.headings[:15]:
        print(
            f"  level={h.level} anchor_id={h.anchor_id!r:12s} "
            f"words={h.word_count:<5} text={h.text[:60]!r}"
        )
    if len(hierarchy.headings) > 15:
        print(f"  ... {len(hierarchy.headings) - 15} more")
    print()
    print("--- hierarchy.markdown (first 800 chars) ---")
    print(hierarchy.markdown[:800])

    print()
    print("=" * 72)
    print("3. Raw inspection of tab body (first 20 paragraphs)")
    print("=" * 72)
    # Fetch raw doc + dig into the right tab's body
    doc = converter._get_document(DOC_ID)
    body = _find_tab_body(doc, TAB_ID)
    assert body is not None, f"Tab {TAB_ID} not found"

    para_count = 0
    style_histogram: dict[str, int] = {}
    first_non_heading_para = None
    first_heading_index = None
    for el in body.get("content", []):
        if "paragraph" not in el:
            continue
        para_count += 1
        para = el["paragraph"]
        style = para.get("paragraphStyle", {}).get("namedStyleType", "<missing>")
        style_histogram[style] = style_histogram.get(style, 0) + 1
        text = _para_text(para)[:80]
        if para_count <= 20:
            heading_id = para.get("paragraphStyle", {}).get("headingId", "")
            print(
                f"  #{para_count:<3} start={el.get('startIndex'):<5} "
                f"style={style:<14} headingId={heading_id!r:12s} text={text!r}"
            )
        if first_non_heading_para is None and style not in HEADING_STYLES:
            first_non_heading_para = (para_count, style, text)
        if first_heading_index is None and style in HEADING_STYLES:
            first_heading_index = (para_count, style, el.get("startIndex"), text)

    print()
    print(f"Paragraph style histogram: {style_histogram}")
    print(f"First non-heading paragraph: {first_non_heading_para}")
    print(f"First heading paragraph: {first_heading_index}")

    print()
    print("=" * 72)
    print("4. read_section(anchor_id='')  # preamble")
    print("=" * 72)
    try:
        preamble = converter.read_section(tab, "")
        print(f"length: {len(preamble.content)} chars")
        print("--- preamble.content (first 1200 chars) ---")
        print(preamble.content[:1200])
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

    print()
    print("=" * 72)
    print("5. read_section(first_h1_anchor) for comparison")
    print("=" * 72)
    first_h1 = next((h for h in hierarchy.headings if h.level == 1), None)
    if first_h1 is None:
        print("  No HEADING_1 present in hierarchy.")
    else:
        try:
            first_section = converter.read_section(tab, first_h1.anchor_id)
            print(f"anchor_id: {first_h1.anchor_id!r}  text: {first_h1.text!r}")
            print(f"length: {len(first_section.content)} chars")
            print("--- first_section.content (first 800 chars) ---")
            print(first_section.content[:800])
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")


def _find_tab_body(doc: dict, tab_id: str) -> dict | None:
    """Walk doc.tabs recursively to find the body for a given tab_id."""
    def walk(tabs):
        for t in tabs:
            props = t.get("tabProperties", {})
            if props.get("tabId") == tab_id:
                return t.get("documentTab", {}).get("body")
            child = walk(t.get("childTabs", []))
            if child is not None:
                return child
        return None
    # Top-level
    if tab_id == "" or tab_id is None:
        return doc.get("body")
    return walk(doc.get("tabs", []))


def _para_text(para: dict) -> str:
    parts = []
    for el in para.get("elements", []):
        if "textRun" in el:
            parts.append(el["textRun"].get("content", "").rstrip("\n"))
    return "".join(parts)


if __name__ == "__main__":
    main()
