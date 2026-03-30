# Quickstart: Document Tabs Support

**Feature**: 131-document-tabs
**Date**: 2026-03-29

## Prerequisites

- Python 3.11+
- `uv` for package management
- Google OAuth credentials (for tier_b tests)
- A multi-tab Google Doc test document (created manually, ID shared in test config)

## Setup

```bash
git checkout 131-document-tabs
cd /Users/tim/ai-twin/google_doc_utils
uv sync
```

## Running Tests

```bash
# Tier A tests (unit, no credentials needed)
cd src && uv run pytest ../tests/tier_a/ ../tests/unit/ -v

# Tier B tests (integration, needs credentials)
cd src && uv run pytest ../tests/mcp/ ../tests/tier_b/ -v -m tier_b

# Just the new multi-tab tests
cd src && uv run pytest ../tests/tier_a/test_tab_utils.py ../tests/mcp/test_tab_tools.py -v
```

## Manual Verification

After implementation, verify with MCP inspector:

```bash
# Start the MCP server
cd src && uv run python -m extended_google_doc_utils.mcp

# In MCP inspector or Claude Desktop:
# 1. Call get_metadata(document_id="<MULTI_TAB_DOC_ID>")
#    → Should list all tabs with IDs and titles
#
# 2. Call read_tab(document_id="<MULTI_TAB_DOC_ID>", tab_id="t.0")
#    → Should return first tab's content
#
# 3. Call read_tab(document_id="<MULTI_TAB_DOC_ID>", tab_id="")
#    → Should error with list of available tabs
```

## Key Files to Modify

| File | Change |
|------|--------|
| `converter/tab_utils.py` | Fix silent fallbacks, add validation |
| `converter/converter.py` | Add `includeTabsContent=True` |
| `converter/exceptions.py` | Enhance `MultipleTabsError`, add `TabNotFoundError` |
| `mcp/tools/tabs.py` | Return resolved tab_id |
| `mcp/tools/sections.py` | Return resolved tab_id |
| `mcp/tools/navigation.py` | Return resolved tab_id in hierarchy |
