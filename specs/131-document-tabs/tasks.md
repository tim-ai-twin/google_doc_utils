# Tasks: Document Tabs Support

**Input**: Design documents from `/specs/131-document-tabs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Included — this feature is primarily a bug-fix + validation effort where tests are the main deliverable.

**Organization**: Tasks grouped by user story. User stories share foundational bug fixes (Phase 2) but are independently testable thereafter.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/extended_google_doc_utils/`
- **Tests**: `tests/` (tier_a = unit, mcp = contract, tier_b = integration)

---

## Phase 1: Setup

**Purpose**: Test infrastructure for multi-tab scenarios

- [x] T001 Add multi-tab test document ID constant in tests/conftest.py — `MULTI_TAB_DOCUMENT_ID = "1iRhQ21xWUJ9GIrn-G_67_gBth5e4s_tBA2Vp8hOb0a0"` with tabs: Alabama, Britain, California
- [ ] T002 [P] Add multi-tab mock document fixture in tests/mcp/conftest.py — full Google Docs API structure with `tabProperties` and `documentTab` for 3 tabs, each with distinct body content, named styles, and inline objects
- [x] T003 [P] Create test file tests/tier_a/test_tab_utils.py with test class skeleton and multi-tab document fixture dicts (no API calls, pure unit tests)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix critical bugs that affect ALL user stories. No story can work correctly until these are resolved.

**CRITICAL**: These bugs cause silent data corruption on multi-tab documents.

- [x] T004 Add `TabNotFoundError` exception class in src/extended_google_doc_utils/converter/exceptions.py — accepts `tab_id` and `available_tabs` list of `(tab_id, title, index)` tuples; message format per contracts/api.md. Note: `mcp/errors.py` already has a separate `TabNotFoundError` for the MCP layer — the converter exception is caught and mapped to MCP error responses by each tool
- [x] T005 Enhance `MultipleTabsError` in src/extended_google_doc_utils/converter/exceptions.py — accept `available_tabs` list; include tab IDs, titles, and indices in error message per contracts/api.md. Note: `mcp/errors.py` has a parallel `MultipleTabsError` — ensure converter-layer errors are caught and mapped correctly by MCP tools
- [x] T006 Add `includeTabsContent=True` to `_get_document()` call in src/extended_google_doc_utils/converter/converter.py — ensures multi-tab documents return tab content instead of empty `tabs` array
- [x] T007 Fix `resolve_tab_id()` in src/extended_google_doc_utils/converter/tab_utils.py — raise `TabNotFoundError` (with available tabs list) when provided tab_id doesn't match any tab, instead of silently passing
- [x] T008 Fix `get_tab_content()` in src/extended_google_doc_utils/converter/tab_utils.py — raise `TabNotFoundError` instead of silently returning first tab's content when tab_id not found
- [x] T009 [P] Fix `get_tab_document_style()` in src/extended_google_doc_utils/converter/tab_utils.py — same pattern: raise error instead of silent fallback
- [x] T010 [P] Fix `get_tab_named_styles()` in src/extended_google_doc_utils/converter/tab_utils.py — same pattern: raise error instead of silent fallback
- [x] T011 [P] Fix `get_inline_objects()` in src/extended_google_doc_utils/converter/tab_utils.py — same pattern: raise error instead of silent fallback
- [x] T012 [P] Fix `get_positioned_objects()` in src/extended_google_doc_utils/converter/tab_utils.py — same pattern: raise error instead of silent fallback
- [x] T013 Update `resolve_tab_id()` to pass available tabs list to `MultipleTabsError` in src/extended_google_doc_utils/converter/tab_utils.py — extract `(tab_id, title, index)` from document tabs and pass to enhanced error

**Checkpoint**: All silent-fallback bugs fixed. Multi-tab documents now fail explicitly instead of returning wrong data.

---

## Phase 3: User Story 1 - Read Content from a Specific Tab (Priority: P1) MVP

**Goal**: Users can discover tabs and read content from any specific tab in a multi-tab document.

**Independent Test**: Call `get_metadata` to list tabs, then `read_tab` with a specific tab_id — correct content returned. Call without tab_id — helpful error with tab list.

### Tests for User Story 1

- [x] T014 [P] [US1] Unit test `resolve_tab_id` in tests/tier_a/test_tab_utils.py — multi-tab with valid tab_id resolves correctly; multi-tab with invalid tab_id raises `TabNotFoundError` with available tabs; multi-tab with empty tab_id raises `MultipleTabsError` with tab list; single-tab with empty tab_id resolves correctly
- [x] T015 [P] [US1] Unit test `get_tab_content` in tests/tier_a/test_tab_utils.py — returns correct body for each tab in multi-tab doc; raises `TabNotFoundError` for invalid tab_id
- [x] T016 [P] [US1] Unit test error message content in tests/tier_a/test_tab_utils.py — `MultipleTabsError` message contains all tab IDs and titles; `TabNotFoundError` message contains requested tab_id and available tabs
- [ ] T017 [P] [US1] Contract test `read_tab` with multi-tab mock in tests/mcp/test_tab_tools.py — verify resolved tab_id in response (not empty string echo); verify `TabNotFoundError` returns helpful MCP error; verify `MultipleTabsError` returns tab list in error
- [x] T018 [US1] E2E test `get_metadata` on multi-tab document in tests/tier_b/test_multi_tab_e2e.py — verify 3 tabs returned (Alabama, Britain, California) with correct tab_ids and titles using document `1iRhQ21xWUJ9GIrn-G_67_gBth5e4s_tBA2Vp8hOb0a0`
- [x] T019 [US1] E2E test `read_tab` on multi-tab document in tests/tier_b/test_multi_tab_e2e.py — read each tab by tab_id and verify distinct content returned; verify empty tab_id raises error with tab list

### Implementation for User Story 1

- [ ] T020 [US1] Fix `read_tab` MCP tool to return resolved tab_id in src/extended_google_doc_utils/mcp/tools/tabs.py — after converter.read_tab() succeeds, return the resolved tab_id from TabReference instead of echoing input
- [x] T021 [US1] Add `TabNotFoundError` handling to `read_tab` MCP tool in src/extended_google_doc_utils/mcp/tools/tabs.py — catch and return helpful MCP error response with available tabs
- [x] T022 [US1] Fix `get_hierarchy` MCP tool to return resolved tab_id in src/extended_google_doc_utils/mcp/tools/navigation.py — same pattern as T020

**Checkpoint**: `get_metadata` → `read_tab(tab_id)` workflow works end-to-end on multi-tab documents.

---

## Phase 4: User Story 2 - Write/Edit Content in a Specific Tab (Priority: P1)

**Goal**: Users can write content to a specific tab without affecting other tabs.

**Independent Test**: Read all tabs, write to one tab, re-read all tabs — only the targeted tab changed.

### Tests for User Story 2

- [ ] T023 [P] [US2] Contract test `write_tab` with multi-tab mock in tests/mcp/test_tab_tools.py — verify resolved tab_id in response; verify `TabNotFoundError` handling; verify `MultipleTabsError` handling
- [x] T024 [US2] E2E test `write_tab` tab isolation in tests/tier_b/test_multi_tab_e2e.py — read all 3 tabs, write new content to one tab, re-read all 3 tabs, verify only target tab changed and other 2 tabs unchanged

### Implementation for User Story 2

- [ ] T025 [US2] Fix `write_tab` MCP tool to return resolved tab_id in src/extended_google_doc_utils/mcp/tools/tabs.py — same pattern as T020
- [x] T026 [US2] Add `TabNotFoundError` handling to `write_tab` MCP tool in src/extended_google_doc_utils/mcp/tools/tabs.py — same pattern as T021

**Checkpoint**: Full read/write cycle works on multi-tab documents with tab isolation verified.

---

## Phase 5: User Story 3 - Formatting and Style Operations on Tabs (Priority: P2)

**Goal**: Style extraction and application work correctly on individual tabs.

**Independent Test**: Extract styles from one tab, apply to another — target tab's formatting changes, other tabs unaffected.

### Tests for User Story 3

- [x] T027 [P] [US3] Unit test `get_tab_document_style` and `get_tab_named_styles` in tests/tier_a/test_tab_utils.py — returns correct styles per tab; raises error for invalid tab_id
- [x] T028 [P] [US3] E2E test style extraction per tab in tests/tier_b/test_multi_tab_e2e.py — extract styles from each tab, verify styles are tab-specific (not mixed across tabs)

### Implementation for User Story 3

- [x] T029 [US3] Add `TabNotFoundError` handling to formatting MCP tools in src/extended_google_doc_utils/mcp/tools/formatting.py — `normalize_formatting`, `extract_styles`, `apply_styles` all catch converter-layer `TabNotFoundError` and return helpful MCP error. Note: these tools go through `converter.read_tab()`/`converter.write_tab()` so they inherit foundational fixes; their response schemas (`NormalizeFormattingResponse`, `ExtractStylesResponse`, `ApplyStylesResponse`) don't have a `tab_id` field — no resolved tab_id return needed
- [x] T030 [US3] Add `TabNotFoundError` handling to style transfer MCP tools in src/extended_google_doc_utils/mcp/tools/styles.py — `get_document_styles` and `apply_document_styles` both accept `tab_id`/`source_tab_id`/`target_tab_id` and go through `style_reader.py`/`style_writer.py` (separate code path from converter). These already use `includeTabsContent=True` in their `_fetch_document`. Catch converter-layer `TabNotFoundError` and `MultipleTabsError`, return helpful MCP error responses
- [x] T031_a [P] [US3] E2E test `get_document_styles` per tab in tests/tier_b/test_multi_tab_e2e.py — call on each of the 3 tabs, verify styles returned are tab-specific; verify empty tab_id raises error with tab list
- [ ] T031_b [P] [US3] Contract test style transfer tools with multi-tab mock in tests/mcp/test_style_tools.py — verify `TabNotFoundError` and `MultipleTabsError` handling for `get_document_styles` and `apply_document_styles`

**Checkpoint**: All style and formatting operations are tab-aware — both the `formatting.py` tools (which go through the converter) and the `styles.py` tools (which go through style_reader/style_writer directly).

---

## Phase 6: User Story 4 - Heading Hierarchy within a Tab (Priority: P2)

**Goal**: Heading hierarchy retrieval returns correct headings for a specific tab only.

**Independent Test**: Request hierarchy for each tab — each returns only its own headings.

### Tests for User Story 4

- [x] T031 [P] [US4] E2E test `get_hierarchy` per tab in tests/tier_b/test_multi_tab_e2e.py — request hierarchy for each of the 3 tabs, verify distinct heading structures returned
- [ ] T032 [P] [US4] Contract test `read_section` with multi-tab mock in tests/mcp/test_section_tools.py — verify resolved tab_id in response; verify `TabNotFoundError` handling

### Implementation for User Story 4

- [x] T033 [US4] Fix `read_section` and `write_section` MCP tools to return resolved tab_id in src/extended_google_doc_utils/mcp/tools/sections.py
- [x] T034 [US4] Add `TabNotFoundError` handling to section MCP tools in src/extended_google_doc_utils/mcp/tools/sections.py

**Checkpoint**: Section-level operations (read_section, write_section, get_hierarchy) work correctly within specific tabs.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Regression verification and cleanup

- [x] T035 Run full existing test suite (tier_a + mcp) to verify no regressions in single-tab behavior
- [ ] T036 Run tier_b tests against single-tab test document (`19LesxcFk6C72A6L5V8MCfOmf7RK975p5kuO4WM7kDmI`) to confirm backward compatibility
- [ ] T037 [P] Update mock fixtures in src/extended_google_doc_utils/discoverability/mock.py — add `TabNotFoundError` mock response for discoverability test completeness
- [x] T038 Run linter (`ruff check .`) and fix any issues across all modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) — BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Phase 2 completion
  - US1 and US2 (both P1): Can proceed in parallel after Phase 2
  - US3 and US4 (both P2): Can proceed in parallel after Phase 2 (independent of US1/US2)
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (Read)**: After Phase 2 — no dependencies on other stories
- **US2 (Write)**: After Phase 2 — no dependencies on other stories (US1 tests may validate write side-effects, but implementation is independent)
- **US3 (Styles)**: After Phase 2 — independent of US1/US2
- **US4 (Hierarchy/Sections)**: After Phase 2 — independent of other stories

### Within Each User Story

- Tests written first → implementation → verify tests pass
- Unit/contract tests before E2E tests
- MCP tool fixes after foundational bug fixes

### Parallel Opportunities

- T002, T003 can run in parallel (different test files)
- T009, T010, T011, T012 can run in parallel (same file but independent functions)
- T014, T015, T016, T017 can run in parallel (different test scenarios)
- All four user story phases can run in parallel after Phase 2

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Sequential first (dependencies):
T004 → T005 → T007 → T013  (exception classes → resolve_tab_id → enhanced error)
T006                         (converter.py — independent)

# Then parallel (independent functions, same file):
T008  (get_tab_content)
T009  (get_tab_document_style)
T010  (get_tab_named_styles)
T011  (get_inline_objects)
T012  (get_positioned_objects)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (test fixtures)
2. Complete Phase 2: Foundational (bug fixes — CRITICAL)
3. Complete Phase 3: User Story 1 (read operations)
4. **STOP and VALIDATE**: Run `get_metadata` + `read_tab` against multi-tab document
5. Verify single-tab tests still pass

### Incremental Delivery

1. Setup + Foundational → Bugs fixed, infrastructure ready
2. Add US1 (Read) → Test independently → Core tab reading works
3. Add US2 (Write) → Test independently → Full read/write cycle validated
4. Add US3 (Styles) + US4 (Hierarchy) → Test independently → Complete tab support
5. Polish → Regression verification → Feature complete

---

## Notes

- Multi-tab test document: `1iRhQ21xWUJ9GIrn-G_67_gBth5e4s_tBA2Vp8hOb0a0` (tabs: Alabama, Britain, California)
- Single-tab test document: `19LesxcFk6C72A6L5V8MCfOmf7RK975p5kuO4WM7kDmI` (for regression)
- E2E tests (T018, T019, T024, T028, T031, T031_a) require Google OAuth credentials (tier_b)
- All unit/contract tests (T014-T017, T023, T027, T031_b, T032) run without credentials (tier_a/mcp)
- Total: 40 tasks across 7 phases
- Two error class hierarchies exist: `converter/exceptions.py` (converter layer) and `mcp/errors.py` (MCP layer). Converter exceptions are caught by MCP tools and mapped to structured error responses.
- Two style code paths: `formatting.py` tools go through `converter.read_tab()`/`write_tab()`; `styles.py` tools go through `style_reader.py`/`style_writer.py` directly (which already use `includeTabsContent=True`)
