# Tasks: Document Style Transfer

**Input**: Design documents from `/specs/130-document-style-transfer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: REQUIRED per FR-025, FR-026, FR-027 (unit tests for extraction/application, round-trip integration tests)

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

## User Story Mapping

| Story | Title | Priority | Description |
|-------|-------|----------|-------------|
| US1 | Read Document Styles | P1 | Read document properties and effective styles |
| US2 | Apply Document-Level Properties | P1 | Apply background, margins, page size |
| US3 | Transfer Named Styles | P1 | Apply effective styles to matching paragraphs |
| US4 | MCP Server Style Operations | P2 | Expose style operations via MCP tools |
| US5 | Round Trip Style Preservation | P2 | Verify read-apply-read fidelity |

---

## Phase 1: Setup

**Purpose**: Project structure and shared types

- [x] T001 [P] Add style transfer data types (enums, dataclasses) to src/extended_google_doc_utils/converter/types.py
- [x] T002 [P] Add style transfer exceptions to src/extended_google_doc_utils/converter/exceptions.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: User story work cannot begin until this phase is complete

- [x] T003 Create style_reader.py module skeleton with API client setup in src/extended_google_doc_utils/converter/style_reader.py
- [x] T004 Implement helper function to extract RGB color from Google API color structures in src/extended_google_doc_utils/converter/style_reader.py
- [x] T005 Implement helper function to extract document properties from documentStyle in src/extended_google_doc_utils/converter/style_reader.py
- [x] T006 Implement helper function to extract named style definitions from namedStyles in src/extended_google_doc_utils/converter/style_reader.py
- [x] T007 Implement helper function to find paragraphs by namedStyleType in document body in src/extended_google_doc_utils/converter/style_reader.py
- [x] T008 Implement helper function to extract effective text/paragraph style from a paragraph element in src/extended_google_doc_utils/converter/style_reader.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Read Document Styles (Priority: P1) 🎯 MVP

**Goal**: Enable reading document properties and effective styles from any Google Doc

**Independent Test**: Call `read_document_styles()` on any existing Google Doc and verify returned data matches visible formatting

### Tests for User Story 1

- [x] T009 [P] [US1] Unit test for RGB color extraction in tests/tier_a/test_style_reader.py
- [x] T010 [P] [US1] Unit test for document properties extraction (background, margins, page size) in tests/tier_a/test_style_reader.py
- [x] T011 [P] [US1] Unit test for named style definition extraction in tests/tier_a/test_style_reader.py
- [x] T012 [P] [US1] Unit test for effective style extraction from paragraph with overrides in tests/tier_a/test_style_reader.py
- [x] T013 [P] [US1] Unit test for fallback to style definition when no paragraphs exist in tests/tier_a/test_style_reader.py

### Implementation for User Story 1

- [x] T014 [US1] Implement `read_document_styles()` function combining all helpers in src/extended_google_doc_utils/converter/style_reader.py
- [x] T015 [US1] Implement `read_effective_style()` for single style type in src/extended_google_doc_utils/converter/style_reader.py
- [x] T016 [US1] Add exports to src/extended_google_doc_utils/converter/__init__.py
- [x] T017 [US1] Integration test: read styles from real Google Doc in tests/tier_b/test_style_transfer.py

**Checkpoint**: User Story 1 complete - can read styles from any document

---

## Phase 4: User Story 2 - Apply Document-Level Properties (Priority: P1)

**Goal**: Enable applying document background, margins, and page size to target document

**Independent Test**: Read properties from Doc A, apply to Doc B, verify Doc B's properties match

### Tests for User Story 2

- [x] T018 [P] [US2] Unit test for building UpdateDocumentStyle request in tests/tier_a/test_style_writer.py
- [x] T019 [P] [US2] Unit test for partial property application (only set properties transferred) in tests/tier_a/test_style_writer.py

### Implementation for User Story 2

- [x] T020 [US2] Create style_writer.py module skeleton in src/extended_google_doc_utils/converter/style_writer.py
- [x] T021 [US2] Implement helper to build UpdateDocumentStyle request from DocumentProperties in src/extended_google_doc_utils/converter/style_writer.py
- [x] T022 [US2] Implement `apply_document_properties()` function in src/extended_google_doc_utils/converter/style_writer.py
- [x] T023 [US2] Add exports to src/extended_google_doc_utils/converter/__init__.py
- [x] T024 [US2] Integration test: apply document properties between real documents in tests/tier_b/test_style_transfer.py

**Checkpoint**: User Story 2 complete - can transfer document-level properties

---

## Phase 5: User Story 3 - Transfer Named Styles (Priority: P1)

**Goal**: Enable transferring effective styles to all matching paragraphs in target document

**Independent Test**: Create two documents with different heading styles, transfer, verify headings match

### Tests for User Story 3

- [x] T025 [P] [US3] Unit test for building updateParagraphStyle request in tests/tier_a/test_style_writer.py
- [x] T026 [P] [US3] Unit test for building updateTextStyle request in tests/tier_a/test_style_writer.py
- [x] T027 [P] [US3] Unit test for generating batch requests for all paragraphs of a style type in tests/tier_a/test_style_writer.py
- [x] T028 [P] [US3] Unit test for preserving character-level overrides (paragraph-range application) in tests/tier_a/test_style_writer.py

### Implementation for User Story 3

- [x] T029 [US3] Implement helper to build updateParagraphStyle request from ParagraphStyleProperties in src/extended_google_doc_utils/converter/style_writer.py
- [x] T030 [US3] Implement helper to build updateTextStyle request from TextStyleProperties in src/extended_google_doc_utils/converter/style_writer.py
- [x] T031 [US3] Implement helper to find all paragraph ranges by style type in target document in src/extended_google_doc_utils/converter/style_writer.py
- [x] T032 [US3] Implement `apply_effective_styles()` function for selected style types in src/extended_google_doc_utils/converter/style_writer.py
- [x] T033 [US3] Implement `apply_document_styles()` combining properties and effective styles in src/extended_google_doc_utils/converter/style_writer.py
- [x] T034 [US3] Add exports to src/extended_google_doc_utils/converter/__init__.py
- [x] T035 [US3] Integration test: transfer all 9 style types between real documents in tests/tier_b/test_style_transfer.py

**Checkpoint**: User Story 3 complete - can transfer effective styles between documents

---

## Phase 6: User Story 4 - MCP Server Style Operations (Priority: P2)

**Goal**: Expose style operations via MCP tools for LLM workflows

**Independent Test**: Call MCP tools directly and verify same results as Python API

### Tests for User Story 4

- [x] T036 [P] [US4] Unit test for get_document_styles MCP tool response format in tests/mcp/test_style_tools.py
- [x] T037 [P] [US4] Unit test for apply_document_styles MCP tool response format in tests/mcp/test_style_tools.py
- [x] T038 [P] [US4] Unit test for MCP error response format in tests/mcp/test_style_tools.py

### Implementation for User Story 4

- [x] T039 [US4] Create styles.py MCP tools module in src/extended_google_doc_utils/mcp/tools/styles.py
- [x] T040 [US4] Implement `get_document_styles` MCP tool wrapping Python API in src/extended_google_doc_utils/mcp/tools/styles.py
- [x] T041 [US4] Implement `apply_document_styles` MCP tool wrapping Python API in src/extended_google_doc_utils/mcp/tools/styles.py
- [x] T042 [US4] Implement JSON serialization helpers for MCP response format in src/extended_google_doc_utils/mcp/tools/styles.py
- [x] T043 [US4] Register style tools in MCP server initialization in src/extended_google_doc_utils/mcp/server.py
- [x] T044 [US4] Integration test: call MCP tools with real documents in tests/mcp/test_style_tools.py

**Checkpoint**: User Story 4 complete - MCP tools available for LLM workflows

---

## Phase 7: User Story 5 - Round Trip Style Preservation (Priority: P2)

**Goal**: Verify read-apply-read produces identical style values

**Independent Test**: Read from Doc A, apply to Doc B, read from Doc B, compare values

### Tests for User Story 5

- [x] T045 [P] [US5] Integration test for document properties round-trip fidelity in tests/tier_b/test_style_transfer.py
- [x] T046 [P] [US5] Integration test for effective styles round-trip fidelity in tests/tier_b/test_style_transfer.py
- [x] T047 [P] [US5] Integration test for full style transfer round-trip (all properties + all styles) in tests/tier_b/test_style_transfer.py
- [x] T048 [US5] Add numeric tolerance comparison helper (0.01pt per SC-003) in tests/tier_b/test_style_transfer.py

**Checkpoint**: User Story 5 complete - round-trip fidelity verified

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, edge cases, documentation

- [x] T049 [P] Handle edge case: source/target same document in src/extended_google_doc_utils/converter/style_writer.py
- [x] T050 [P] Handle edge case: protected ranges returning permission errors in src/extended_google_doc_utils/converter/style_writer.py
- [x] T051 [P] Handle edge case: inconsistent paragraph formatting (use first paragraph) in src/extended_google_doc_utils/converter/style_reader.py
- [x] T052 Run all tests and verify 100% pass rate
- [x] T053 Validate quickstart.md examples work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on Foundational; uses US1 for reading source properties
- **US3 (Phase 5)**: Depends on Foundational + US1 (reads source styles)
- **US4 (Phase 6)**: Depends on US1 + US2 + US3 (wraps Python API)
- **US5 (Phase 7)**: Depends on US1 + US2 + US3 (tests round-trip)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

```
US1 (Read) ─────────┬───► US4 (MCP)
                    │
US2 (Doc Props) ────┼───► US5 (Round Trip)
                    │
US3 (Named Styles) ─┘
```

- **US1**: Can start after Foundational - No dependencies on other stories
- **US2**: Can start after Foundational - Uses US1's read functions
- **US3**: Can start after Foundational - Uses US1's read functions
- **US4**: Depends on US1, US2, US3 being complete
- **US5**: Depends on US1, US2, US3 being complete

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:

- **Phase 1**: T001, T002 (different files)
- **Phase 3**: T009-T013 (test files), then T014-T015 (implementation)
- **Phase 4**: T018-T019 (tests)
- **Phase 5**: T025-T028 (tests)
- **Phase 6**: T036-T038 (tests)
- **Phase 7**: T045-T047 (integration tests)
- **Phase 8**: T049-T051 (edge cases)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task: "Unit test for RGB color extraction in tests/tier_a/test_style_reader.py"
Task: "Unit test for document properties extraction in tests/tier_a/test_style_reader.py"
Task: "Unit test for named style definition extraction in tests/tier_a/test_style_reader.py"
Task: "Unit test for effective style extraction from paragraph with overrides in tests/tier_a/test_style_reader.py"
Task: "Unit test for fallback to style definition when no paragraphs exist in tests/tier_a/test_style_reader.py"

# Then implementation sequentially (builds on helpers):
Task: "Implement read_document_styles() function in style_reader.py"
Task: "Implement read_effective_style() for single style type in style_reader.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3)

1. Complete Phase 1: Setup (types, exceptions)
2. Complete Phase 2: Foundational (helpers)
3. Complete Phase 3: User Story 1 - Read styles
4. Complete Phase 4: User Story 2 - Apply doc properties
5. Complete Phase 5: User Story 3 - Transfer named styles
6. **STOP and VALIDATE**: Core functionality complete

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Can inspect any document's styles (value delivered!)
3. Add US2 → Can transfer page settings
4. Add US3 → Can transfer full styles ("Apply styles from A to B" works!)
5. Add US4 → LLM workflows enabled
6. Add US5 → Round-trip verified

### Critical Path

```
Setup → Foundational → US1 → US3 → US4
                            ↘ US2 ↗
```

US1 (reading) is prerequisite for US2 and US3 (writing).
US4 wraps all of them for MCP.

---

## Phase 9: Multi-Tab Document Support

**Purpose**: Add tab_id support to all style transfer tools for consistency with other MCP tools

**Gap identified**: Style transfer tools don't support multi-tab documents, unlike other MCP tools

- [x] T054 [P] Add `tab_id` parameter to `read_document_styles()` in src/extended_google_doc_utils/converter/style_reader.py
- [x] T055 [P] Add `tab_id` parameter to `apply_document_styles()` in src/extended_google_doc_utils/converter/style_writer.py
- [x] T056 [P] Add `tab_id` parameter to `get_document_styles` MCP tool in src/extended_google_doc_utils/mcp/tools/styles.py
- [x] T057 [P] Add `tab_id` parameter to `apply_document_styles` MCP tool in src/extended_google_doc_utils/mcp/tools/styles.py

**Checkpoint**: Multi-tab support complete - consistent with all other MCP tools

---

## Phase 10: Tab-Level Document Properties

**Purpose**: Read document properties (background, margins, page size) from tab-level documentStyle instead of top-level

**Issue**: Multi-tab documents can have different page settings per tab; current code reads from top-level which may not reflect the specific tab's settings

- [x] T060 Add `get_tab_document_style()` helper to src/extended_google_doc_utils/converter/tab_utils.py
- [x] T061 Update `read_document_styles()` to use tab-level documentStyle in src/extended_google_doc_utils/converter/style_reader.py
- [x] T062 Verify style_writer.py handles tab-level properties correctly

**Checkpoint**: Tab-level document properties working correctly

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Tests MUST be written and FAIL before implementation (per FR-025, FR-026, FR-027)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Numeric comparisons use 0.01pt tolerance (SC-003)
