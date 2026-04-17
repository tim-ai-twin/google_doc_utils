# MCP Tool Contracts: Large Document Editing

## Modified Tools

### get_hierarchy (enhanced)

**Input** (unchanged):
```
document_id: str  — Google Doc ID
tab_id: str = ""  — Tab ID (empty for single-tab)
```

**Output** (enhanced):
```json
{
  "success": true,
  "headings": [
    {
      "anchor_id": "h.abc123",
      "level": 1,
      "text": "Introduction",
      "word_count": 1250,
      "char_count": 7800
    },
    {
      "anchor_id": "h.def456",
      "level": 2,
      "text": "Background",
      "word_count": 340,
      "char_count": 2100
    }
  ],
  "markdown": "# {^ h.abc123}Introduction (1250 words)\n## {^ h.def456}Background (340 words)",
  "total_word_count": 1590,
  "total_char_count": 9900
}
```

**Behavioral changes**:
- `word_count` and `char_count` per heading count text in that section (heading through next same-or-higher level)
- `total_word_count` / `total_char_count` are sums across entire tab including preamble
- Markdown representation now includes word count hint per heading: `# {^ id}Title (N words)`
- Counts are plain-text only (no formatting markers or image placeholders)

---

### read_tab (enhanced)

**Input** (new parameter):
```
document_id: str  — Google Doc ID
tab_id: str = ""  — Tab ID (empty for single-tab)
format: str = "mebdf"  — Output format: "mebdf" or "plain"
```

**Output** (new field):
```json
{
  "success": true,
  "content": "# Introduction\n\nThis is plain markdown without MEBDF markers...",
  "tab_id": "t.0",
  "format": "plain",
  "warnings": []
}
```

**Behavioral changes**:
- `format="mebdf"` (default): existing behavior, full MEBDF output
- `format="plain"`: standard markdown output without MEBDF formatting markers
  - `{!...}text{/!}` → just `text`
  - `{^= objectId image}` → `[image]`
  - `{^ anchorId}` in headings → stripped
  - Bold, italic, links, headings, lists preserved as standard markdown
- `format` field echoed back in response

---

## Unchanged Tools

- **read_section**: No changes. Always returns MEBDF (needed for editing).
- **write_section**: No changes.
- **write_tab**: No changes.
- **get_metadata**: No changes.
- **list_documents**: No changes.
