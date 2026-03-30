# Implementation Plan: Document Tabs Support

**Branch**: `131-document-tabs` | **Date**: 2026-03-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/131-document-tabs/spec.md`

## Summary

Enable reliable multi-tab Google Docs support by fixing bugs in the existing tab infrastructure and adding comprehensive test coverage. The architecture (TabReference, tab_utils, MCP tool signatures) already exists — but code review revealed critical bugs (silent fallbacks returning wrong tab data, missing `includeTabsContent` API flag) and zero tests against real multi-tab documents.

**Scope**: Bug fixes + enhanced errors + tests. No new features, no MEBDF changes, no new MCP tools.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: google-api-python-client, mcp>=1.25.0 (existing)
**Storage**: N/A (stateless — reads from Google Docs API)
**Testing**: pytest (tier_a = unit/no creds, tier_b = integration/OAuth)
**Target Platform**: CLI / MCP server
**Project Type**: Single Python package
**Constraints**: Google Docs API does not support creating tabs programmatically — test document must be created manually

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with Extended Google Doc Utils Constitution v1.0.0:

- [x] **I. LLM-Friendly Format Design**: No MEBDF changes. Enhanced error messages include tab IDs/titles for LLM self-correction.
- [x] **II. Round-Trip Safety**: Bug fixes improve round-trip safety by preventing silent cross-tab data leaks.
- [x] **III. Minimal Verbosity**: No new syntax. Tab selection remains a parameter, not markup.
- [x] **IV. Backward Compatibility**: Single-tab documents behave identically. Only multi-tab documents (previously broken) change behavior.
- [x] **V. Specification-Driven Development**: Full spec written before implementation.

**Testing Standards**:
- [x] Contract tests planned for tab resolution and error handling
- [x] Round-trip tests planned for per-tab read/write cycles
- [x] LLM integration tests planned (discoverability suite multi-tab scenarios)
- [x] Edge case coverage identified (invalid tab_id, deleted tabs, single→multi transition)

## Project Structure

### Documentation (this feature)

```text
specs/131-document-tabs/
├── plan.md              # This file
├── research.md          # Phase 0: decisions on bugs, errors, test strategy
├── data-model.md        # Phase 1: entity changes (TabNotFoundError, enhanced MultipleTabsError)
├── quickstart.md        # Phase 1: setup and verification guide
├── contracts/api.md     # Phase 1: changed API contracts
└── tasks.md             # Phase 2 output (not yet created)
```

### Source Code (repository root)

```text
src/extended_google_doc_utils/
├── converter/
│   ├── tab_utils.py         # FIX: silent fallbacks → explicit errors
│   ├── converter.py          # FIX: add includeTabsContent=True
│   └── exceptions.py         # ADD: TabNotFoundError, enhance MultipleTabsError
├── mcp/
│   └── tools/
│       ├── tabs.py           # FIX: return resolved tab_id
│       ├── sections.py       # FIX: return resolved tab_id
│       └── navigation.py     # FIX: return resolved tab_id in hierarchy

tests/
├── tier_a/
│   └── test_tab_utils.py     # NEW: unit tests for all tab_utils functions
├── mcp/
│   ├── test_tab_tools.py     # UPDATE: multi-tab mock scenarios
│   ├── test_section_tools.py # UPDATE: multi-tab section scenarios
│   └── conftest.py           # UPDATE: multi-tab mock fixtures
└── tier_b/
    └── test_multi_tab_e2e.py # NEW: E2E tests against real multi-tab doc
```

**Structure Decision**: Existing single-project layout. All changes are modifications to existing files plus 2 new test files.

## Implementation Phases

### Phase A: Fix Critical Bugs (autonomous — no human input needed)

**Priority**: These bugs cause data corruption on multi-tab documents.

1. **`converter.py`** — Add `includeTabsContent=True` to `_get_document()` call
   - Without this, `document["tabs"]` is empty for multi-tab docs
   - Single-tab docs are unaffected (flag is additive)

2. **`tab_utils.py`** — Replace all silent fallbacks with explicit errors
   - `get_tab_content()`: Raise error instead of returning first tab's content
   - `get_tab_document_style()`: Same fix
   - `get_tab_named_styles()`: Same fix
   - `get_inline_objects()`: Same fix
   - `get_positioned_objects()`: Same fix
   - `resolve_tab_id()`: Raise `TabNotFoundError` instead of silently passing

3. **`exceptions.py`** — New `TabNotFoundError` + enhanced `MultipleTabsError`
   - Both include list of available `(tab_id, title, index)` tuples in message

### Phase B: MCP Tool Fixes (autonomous)

4. **`tabs.py`, `sections.py`, `navigation.py`** — Return resolved tab_id
   - After converter operations, extract the actual resolved tab_id
   - Return it in the response instead of echoing the input value
   - Catch and surface `TabNotFoundError` with helpful MCP error response

### Phase C: Unit Tests (autonomous — tier_a, no credentials)

5. **New `test_tab_utils.py`** — Comprehensive unit tests for tab_utils
   - Multi-tab document with valid tab_id → correct content returned
   - Multi-tab document with invalid tab_id → `TabNotFoundError`
   - Multi-tab document with empty tab_id → `MultipleTabsError` with tab list
   - Single-tab document with empty tab_id → resolves correctly
   - All five `get_tab_*` functions tested with multi-tab fixtures
   - Error messages contain tab IDs and titles

6. **Update `test_tab_tools.py`** — MCP tool contract tests
   - Verify resolved tab_id in responses
   - Verify `TabNotFoundError` handling
   - Multi-tab mock scenarios

7. **Update `conftest.py`** — Proper multi-tab mock fixtures
   - Mock document with full Google Docs API tab structure (`tabProperties`, `documentTab`)
   - Mock for invalid tab_id scenarios

### Phase D: Integration Tests (requires one human action)

**Human action required**: Create a multi-tab Google Doc with:
- 3 tabs: "Overview", "Timeline", "Budget"
- Each tab has 2-3 headings with distinct content
- At least one tab has formatted text (bold, italic)
- Share document ID

8. **New `test_multi_tab_e2e.py`** — E2E tests against real document
   - `get_metadata` returns all 3 tabs
   - `read_tab` with specific tab_id returns correct content
   - `read_tab` with empty tab_id raises error with tab list
   - `read_tab` with invalid tab_id raises `TabNotFoundError`
   - `read_section` within a specific tab
   - `get_hierarchy` for a specific tab
   - `write_tab` modifies only target tab (read other tabs before/after)
   - `write_section` within specific tab preserves other tabs
   - Style extraction from specific tab

### Phase E: Regression Verification (autonomous)

9. Run full existing test suite to confirm no regressions in single-tab behavior

## Human vs. Autonomous Split

| Task | Who | Effort |
|------|-----|--------|
| Phases A-C: Bug fixes + unit tests | Claude Code | ~95% of work |
| Create multi-tab test document | Human | ~5 minutes |
| Phase D: Write E2E test code | Claude Code | After doc ID provided |
| Phase E: Run regression suite | Claude Code | Automated |
