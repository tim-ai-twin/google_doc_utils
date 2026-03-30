# Research: Document Tabs Support

**Feature**: 131-document-tabs
**Date**: 2026-03-29

## Decision 1: Document Fetch Must Include Tab Content

**Decision**: Add `includeTabsContent=True` parameter to the Google Docs API `documents().get()` call.

**Rationale**: Without this flag, the API returns an empty `tabs` array for multi-tab documents. The current code at `converter.py:106` omits this parameter, meaning multi-tab documents silently fail — `get_tabs()` returns `[]`, and the code falls through to `document.get("body", {})` which only returns the first tab's content.

**Alternatives considered**:
- Fetching tabs individually: Rejected — requires multiple API calls and tab discovery is still needed.

## Decision 2: Fix Silent Fallback Bugs in tab_utils.py

**Decision**: Replace all silent-fallback patterns with explicit errors when a requested tab is not found.

**Rationale**: Five functions in `tab_utils.py` (`get_tab_content`, `get_tab_document_style`, `get_tab_named_styles`, `get_inline_objects`, `get_positioned_objects`) all share the same bug: when a tab_id doesn't match any tab, they silently return the first tab's data or the document-level fallback. This causes data corruption — operations intended for one tab silently affect or read from another.

**Alternatives considered**:
- Keeping fallback for backward compatibility: Rejected — the fallback never triggers correctly today (no tests exercise it), and it creates a data integrity risk.

## Decision 3: Enhance Error Messages with Tab Metadata

**Decision**: `MultipleTabsError` should include available tab IDs and titles, not just count. Add a new `TabNotFoundError` for invalid tab_id values.

**Rationale**: When an LLM encounters `MultipleTabsError`, it needs to know which tab_id values are valid to self-correct. Currently it only sees "Document has 3 tabs" with no way to pick the right one.

**Alternatives considered**:
- Returning tab list only via `get_metadata()`: Rejected — the error is the natural place to surface this since it's where the LLM is blocked.

## Decision 4: Return Resolved tab_id from MCP Tools

**Decision**: MCP tools should return the *resolved* tab_id (e.g., "t.0"), not the input value (which may be empty string for single-tab docs).

**Rationale**: When `tab_id=""` is passed for a single-tab document, the response currently echoes back `""`. The LLM client has no idea which tab was actually used, breaking multi-step workflows where the resolved ID is needed for subsequent operations.

**Alternatives considered**:
- Always requiring explicit tab_id: Rejected — breaks backward compatibility with single-tab workflows.

## Decision 5: Multi-Tab Test Document Strategy

**Decision**: Use a manually-created static reference document (like the existing single-tab test doc). The Google Docs API does not support creating tabs programmatically.

**Rationale**: Tabs can only be created through the Google Docs UI. A persistent reference document with known structure enables repeatable integration tests without manual setup each run.

**Test document requirements**:
- 3 tabs with distinct titles (e.g., "Overview", "Timeline", "Budget")
- Each tab has unique heading structure and content
- At least one tab has styled text (bold, italic, custom fonts)
- Document shared with the test service account

**Alternatives considered**:
- Dynamic document creation: Not possible — API limitation.
- Mock-only testing: Rejected — the whole point is validating against real multi-tab API responses.

## Decision 6: No MEBDF Format Changes Needed

**Decision**: MEBDF remains tab-scoped. No new syntax for tab boundaries.

**Rationale**: Each operation already targets a single tab via `tab_id` parameter. Adding tab boundary markers to MEBDF would increase complexity without user benefit — LLMs work with one tab at a time naturally.

**Alternatives considered**:
- Multi-tab MEBDF with `{#tab:id}` markers: Rejected — violates Constitution Principle III (Minimal Verbosity) and Principle I (LLM-Friendly Design). Adds complexity with no use case.
