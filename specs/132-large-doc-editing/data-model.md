# Data Model: Large Document Editing

## Modified Entities

### HeadingAnchor (converter/types.py — existing, extended)

Current fields:
- `anchor_id: str` — heading ID
- `level: int` — 1-6
- `text: str` — heading text
- `start_index: int` — position in document

New fields:
- `word_count: int` — words in this section (heading through next same-or-higher level heading)
- `char_count: int` — characters in this section (text only, no markup)

### HierarchyResult (converter/types.py — existing, extended)

Current fields:
- `headings: list[HeadingAnchor]`
- `markdown: str`

New fields:
- `total_word_count: int` — total words across all sections
- `total_char_count: int` — total characters across all sections

### HeadingInfo (mcp/schemas.py — existing, extended)

Current fields:
- `anchor_id: str`
- `level: int`
- `text: str`

New fields:
- `word_count: int` — mirrors HeadingAnchor.word_count
- `char_count: int` — mirrors HeadingAnchor.char_count

### HierarchyResponse (mcp/schemas.py — existing, extended)

Current fields:
- `success: bool`
- `headings: list[HeadingInfo]`
- `markdown: str`

New fields:
- `total_word_count: int`
- `total_char_count: int`

### ExportResult (converter/types.py — unchanged)

No changes needed. The `content` field already holds the serialized output — the serializer determines format (MEBDF vs plain markdown).

### ReadTabResponse (mcp/schemas.py — existing, extended)

Current fields:
- `success: bool`
- `content: str`
- `tab_id: str`
- `warnings: list[str]`

New fields:
- `format: str` — `"mebdf"` or `"plain"`, echoes back the requested format

## New Entities

None. All changes extend existing dataclasses.

## Relationships

```
get_hierarchy(tab) → HierarchyResult
  └── headings[].word_count/char_count  (NEW: computed from section boundaries)
  └── total_word_count/total_char_count  (NEW: sum of all sections)

read_tab(tab, format) → ExportResult
  └── content: str  (format determines serializer: MebdfSerializer vs PlainMarkdownSerializer)
```
