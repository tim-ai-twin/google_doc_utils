# API Contracts: Document Tabs Support

**Feature**: 131-document-tabs
**Date**: 2026-03-29

## Changes to Existing Contracts

### 1. MultipleTabsError — Enhanced Error Message

**Before:**
```
Document has 3 tabs. Specify tab_id to select one.
```

**After:**
```
Document has 3 tabs. Specify tab_id to select one.
Available tabs:
  - tab_id="t.0" title="Overview" (index 0)
  - tab_id="t.1" title="Timeline" (index 1)
  - tab_id="t.2" title="Budget" (index 2)
```

### 2. New Exception: TabNotFoundError

Raised when a specific tab_id is provided but does not exist in the document.

```
Tab "t.99" not found in document. Available tabs:
  - tab_id="t.0" title="Overview" (index 0)
  - tab_id="t.1" title="Timeline" (index 1)
```

### 3. MCP Tool Responses — Resolved tab_id

All MCP tools that accept `tab_id` return the resolved value:

**Before (single-tab, tab_id=""):**
```json
{"success": true, "tab_id": "", "content": "..."}
```

**After (single-tab, tab_id=""):**
```json
{"success": true, "tab_id": "t.0", "content": "..."}
```

### 4. Document Fetch — includeTabsContent

The `_get_document()` call adds `includeTabsContent=True`:

**Before:**
```python
service.documents().get(documentId=document_id).execute()
```

**After:**
```python
service.documents().get(documentId=document_id, includeTabsContent=True).execute()
```

## Unchanged Contracts

- All MCP tool signatures remain identical (same parameters, same return types)
- MEBDF format unchanged
- `get_metadata()` response structure unchanged (already includes tabs)
- `TabReference` dataclass unchanged
- Single-tab document behavior unchanged (tab_id="" still works)
