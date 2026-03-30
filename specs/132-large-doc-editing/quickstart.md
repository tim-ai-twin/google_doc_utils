# Quickstart: Large Document Editing

## What's Being Built

Three changes to enable efficient editing of large Google Docs:

1. **Enhanced `get_hierarchy`** — returns word/character counts per section so the LLM can judge document size before reading
2. **`format` parameter on `read_tab`** — supports `"plain"` output (no MEBDF markers) for cleaner disk-based search
3. **Claude Code skill** — orchestrates the optimal workflow: discover → measure → export → search → edit

## Layer Responsibilities

| Layer | Does | Does NOT |
|-------|------|----------|
| MCP server | Data access: read/write docs, hierarchy, metadata | Write to filesystem |
| Claude Code skill | Orchestration: workflow, temp files, search, cleanup | Direct Google API calls |

## Key Files to Modify

```
src/extended_google_doc_utils/converter/
├── types.py                  # Add word_count/char_count to HeadingAnchor, HierarchyResult
├── hierarchy.py              # Compute section sizes during extraction
├── converter.py              # Add format param to read_tab
├── plain_serializer.py       # NEW: PlainMarkdownSerializer (mirrors MebdfSerializer)

src/extended_google_doc_utils/mcp/
├── schemas.py                # Add fields to HeadingInfo, HierarchyResponse, ReadTabResponse
├── tools/navigation.py       # Wire up new hierarchy fields
├── tools/tabs.py             # Add format param to read_tab tool

.claude/skills/
├── edit-google-doc.md        # NEW: Skill definition

tests/
├── tier_a/test_plain_serializer.py    # NEW: Plain markdown output tests
├── tier_a/test_hierarchy_sizes.py     # NEW: Section size calculation tests
├── mcp/test_read_tab_format.py        # NEW: Format parameter tests
```

## Implementation Order

1. **Types + hierarchy sizes** (P1, no dependencies)
2. **Plain markdown serializer** (P1, depends on AST understanding)
3. **MCP tool changes** (P1, depends on 1+2)
4. **Skill definition** (P2, depends on 3)
5. **Tests** (throughout, alongside each step)

## Quick Validation

After implementing, verify with:
```bash
# Run tier A tests (no credentials needed)
cd src && pytest ../tests/tier_a/ -v

# Check the skill file exists and is valid markdown
cat .claude/skills/edit-google-doc.md
```
