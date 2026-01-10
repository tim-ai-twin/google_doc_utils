# Tasks: Google Docs to Markdown Converter

**Input**: Design documents from `/specs/126-gdoc-markdown-converter/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per existing project pattern (pytest with tier_a/tier_b markers).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md, this extends the existing `extended_google_doc_utils` package:
- Source: `src/extended_google_doc_utils/converter/`
- Tests: `tests/tier_a/` (mocked) and `tests/tier_b/` (real API)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create converter module structure and base classes

- [X] T001 Create converter module directory structure: `src/extended_google_doc_utils/converter/__init__.py`
- [X] T002 [P] Create data classes and enums in `src/extended_google_doc_utils/converter/types.py` (TabReference, HeadingAnchor, EmbeddedObjectType, ExportResult, ImportResult, HierarchyResult)
- [X] T003 [P] Create custom exceptions in `src/extended_google_doc_utils/converter/exceptions.py` (ConverterError, MultipleTabsError, AnchorNotFoundError, EmbeddedObjectNotFoundError, MebdfParseError)
- [X] T004 [P] Create test fixtures directory `tests/fixtures/mebdf_samples/` with sample MEBDF documents

---

## Phase 2: Foundational (MEBDF Parser - Blocking Prerequisite)

**Purpose**: MEBDF parser that ALL user stories depend on

**CRITICAL**: No user story work can begin until parser is complete

- [X] T005 Implement MEBDF tokenizer in `src/extended_google_doc_utils/converter/mebdf_parser.py` - Token types for all MEBDF syntax
- [X] T006 Implement MEBDF AST nodes in `src/extended_google_doc_utils/converter/mebdf_parser.py` - TextNode, HeadingNode, FormattingNode, AnchorNode, EmbeddedObjectNode, etc.
- [X] T007 Implement inline parser in `src/extended_google_doc_utils/converter/mebdf_parser.py` - Parse `{!props}text{/!}`, `{^ id}`, standard markdown inline
- [X] T008 Implement block parser in `src/extended_google_doc_utils/converter/mebdf_parser.py` - Parse `{!props}` standalone, `{^= id type}`, headings, paragraphs
- [X] T009 Implement full document parser in `src/extended_google_doc_utils/converter/mebdf_parser.py` - Combine inline/block, handle stateful block formatting
- [X] T010 [P] Implement MEBDF serializer in `src/extended_google_doc_utils/converter/mebdf_serializer.py` - AST back to MEBDF string
- [X] T011 [P] Create parser unit tests in `tests/tier_a/test_mebdf_parser.py` - All token types, edge cases, malformed input handling
- [X] T012 [P] Create serializer unit tests in `tests/tier_a/test_mebdf_serializer.py` - Round-trip AST preservation

**Checkpoint**: MEBDF parser complete - user story implementation can begin

---

## Phase 3: User Story 1 - Get Tab Hierarchy (Priority: P1) - MVP

**Goal**: Retrieve document structure as pure markdown headings with anchor IDs

**Independent Test**: Request hierarchy of a multi-heading doc, verify output contains only `# {^ id}Heading` lines

### Implementation for User Story 1

- [X] T013 [US1] Implement tab resolution in `src/extended_google_doc_utils/converter/tab_utils.py` - Resolve empty tab_id for single-tab docs, raise MultipleTabsError
- [X] T014 [US1] Implement heading extractor in `src/extended_google_doc_utils/converter/hierarchy.py` - Extract headingId from paragraphStyle for HEADING_1-6
- [X] T015 [US1] Implement hierarchy formatter in `src/extended_google_doc_utils/converter/hierarchy.py` - Convert headings to `## {^ id}Text` markdown format
- [X] T016 [US1] Implement `get_hierarchy()` method in `src/extended_google_doc_utils/converter/converter.py` - Main entry point returning HierarchyResult
- [X] T017 [P] [US1] Create hierarchy unit tests in `tests/tier_a/test_hierarchy.py` - Mock API responses, verify heading extraction
- [ ] T018 [P] [US1] Create hierarchy e2e test in `tests/tier_b/test_converter_e2e.py` - Real doc with multiple heading levels

**Checkpoint**: Hierarchy API functional - can navigate document structure

---

## Phase 4: User Story 2 - Export Full Tab (Priority: P1)

**Goal**: Convert entire tab to MEBDF markdown with all formatting and anchors

**Independent Test**: Export a tab with various formatting, verify MEBDF output represents all elements

### Implementation for User Story 2

- [X] T019 [US2] Implement text run extractor in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` - Extract textRun elements with formatting
- [X] T020 [US2] Implement inline formatting converter in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` - Bold/italic to markdown, highlight/underline/color/mono to `{!...}`
- [X] T021 [US2] Implement anchor extractor in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` - Extract comment anchors, bookmarks, heading anchors as `{^ id}`
- [X] T022 [US2] Implement embedded object detector in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` - Detect image/drawing/chart/video from inlineObjects, output `{^= id type}`
- [X] T023 [US2] Implement paragraph converter in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` - Handle lists, headings, block formatting state
- [X] T024 [US2] Implement table converter in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` - Convert Google Docs tables to markdown table syntax
- [X] T025 [US2] Implement `export_tab()` method in `src/extended_google_doc_utils/converter/converter.py` - Orchestrate full tab export
- [ ] T026 [P] [US2] Create export unit tests in `tests/tier_a/test_gdoc_to_mebdf.py` - Mock API, test each formatting type
- [ ] T027 [P] [US2] Create export e2e test in `tests/tier_b/test_converter_e2e.py` - Real doc with mixed formatting

**Checkpoint**: Full tab export functional - can read entire document as MEBDF

---

## Phase 5: User Story 3 - Export Section by Anchor (Priority: P1)

**Goal**: Export specific section identified by heading anchor ID

**Independent Test**: Export section by anchor, verify only content between that heading and next same-level heading

### Implementation for User Story 3

- [X] T028 [US3] Implement section boundary calculator in `src/extended_google_doc_utils/converter/section_utils.py` - Find start/end indices for section by anchor ID
- [X] T029 [US3] Implement preamble extractor in `src/extended_google_doc_utils/converter/section_utils.py` - Handle empty string anchor_id for content before first heading
- [X] T030 [US3] Implement `export_section()` method in `src/extended_google_doc_utils/converter/converter.py` - Use section boundaries with export logic
- [ ] T031 [P] [US3] Create section export unit tests in `tests/tier_a/test_section_export.py` - Various heading levels, preamble, last section
- [ ] T032 [P] [US3] Create section export e2e test in `tests/tier_b/test_converter_e2e.py` - Real doc section extraction

**Checkpoint**: Section export functional - can read specific document sections

---

## Phase 6: User Story 4 - Import Full Tab (Priority: P2)

**Goal**: Convert MEBDF markdown to Google Docs format and replace tab content

**Independent Test**: Create MEBDF with various formatting, import to tab, verify all formatting applied

### Implementation for User Story 4

- [X] T033 [US4] Implement text insertion builder in `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py` - Build InsertTextRequest from AST
- [X] T034 [US4] Implement formatting request builder in `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py` - Build UpdateTextStyleRequest for bold/italic/highlight/etc.
- [X] T035 [US4] Implement anchor insertion builder in `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py` - Handle `{^ id}` existing anchors, `{^}` proposed anchors
- [X] T036 [US4] Implement embedded object preservation in `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py` - Match `{^= id type}` to existing objects, validate existence
- [X] T037 [US4] Implement paragraph style builder in `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py` - Headings, lists, block formatting properties
- [X] T038 [US4] Implement table insertion builder in `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py` - Convert markdown tables to Google Docs table requests
- [X] T039 [US4] Implement `import_tab()` method in `src/extended_google_doc_utils/converter/converter.py` - Orchestrate full tab replacement via batchUpdate
- [ ] T040 [P] [US4] Create import unit tests in `tests/tier_a/test_mebdf_to_gdoc.py` - Mock API, test each formatting type
- [ ] T041 [P] [US4] Create import e2e test in `tests/tier_b/test_converter_e2e.py` - Real doc import with formatting verification

**Checkpoint**: Full tab import functional - can write MEBDF to document

---

## Phase 7: User Story 5 - Import Section by Anchor (Priority: P2)

**Goal**: Replace specific section while preserving rest of document

**Independent Test**: Modify section content, import by anchor, verify only that section changed

### Implementation for User Story 5

- [X] T042 [US5] Implement section replacement strategy in `src/extended_google_doc_utils/converter/section_utils.py` - Delete range, insert new content, preserve surrounding
- [X] T043 [US5] Implement preamble replacement in `src/extended_google_doc_utils/converter/section_utils.py` - Handle empty string anchor_id
- [X] T044 [US5] Implement `import_section()` method in `src/extended_google_doc_utils/converter/converter.py` - Combine section utils with import logic
- [ ] T045 [P] [US5] Create section import unit tests in `tests/tier_a/test_section_import.py` - Various scenarios, boundary preservation
- [ ] T046 [P] [US5] Create section import e2e test in `tests/tier_b/test_converter_e2e.py` - Real doc section replacement

**Checkpoint**: Section import functional - can surgically edit document sections

---

## Phase 8: User Story 6 - Round-Trip Preservation (Priority: P3)

**Goal**: Validate export→edit→import preserves all formatting and anchors

**Independent Test**: Export tab, re-import unchanged, verify semantic equivalence

### Implementation for User Story 6

- [ ] T047 [US6] Implement round-trip test framework in `tests/tier_a/test_round_trip.py` - Compare pre/post conversion formatting
- [ ] T048 [US6] Create anchor preservation tests in `tests/tier_a/test_round_trip.py` - Verify anchor IDs survive round-trip
- [ ] T049 [US6] Create formatting preservation tests in `tests/tier_a/test_round_trip.py` - All supported formatting types
- [ ] T050 [US6] Create embedded object preservation tests in `tests/tier_a/test_round_trip.py` - Images, drawings, charts preserved
- [ ] T051 [P] [US6] Create round-trip e2e test in `tests/tier_b/test_converter_e2e.py` - Real doc full cycle verification

**Checkpoint**: Round-trip validation complete - conversion is semantically lossless

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, public API, and cleanup

- [X] T052 [P] Create public API exports in `src/extended_google_doc_utils/converter/__init__.py` - Export GoogleDocsConverter, TabReference, exceptions, result types
- [X] T053 [P] Update package `__init__.py` at `src/extended_google_doc_utils/__init__.py` - Export converter module
- [X] T054 Add warning logging for unsupported formatting in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py`
- [ ] T055 [P] Validate quickstart.md code examples work end-to-end
- [X] T056 Code review and cleanup across all converter modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1) can proceed in parallel after Foundational
  - US4, US5 (P2) can proceed in parallel after Foundational
  - US6 (P3) depends on US2 and US4 for round-trip testing
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Hierarchy)**: Foundational only - independent
- **US2 (Export Tab)**: Foundational only - independent
- **US3 (Export Section)**: Shares section_utils with US5, but can develop independently
- **US4 (Import Tab)**: Foundational only - independent
- **US5 (Import Section)**: Shares section_utils with US3, but can develop independently
- **US6 (Round-Trip)**: Requires US2 (export) and US4 (import) for testing

### Within Each User Story

- Parser (Phase 2) must complete first
- Models/utilities before service logic
- Core implementation before integration
- Tests can run in parallel within story

### Parallel Opportunities

Within Setup (Phase 1):
- T002, T003, T004 can all run in parallel

Within Foundational (Phase 2):
- T010, T011, T012 can run in parallel (after T005-T009 complete)

After Foundational completes:
- US1, US2, US3 can all start in parallel
- US4, US5 can start in parallel
- All test tasks marked [P] within a story can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# After T005-T009 (parser core) complete, launch in parallel:
Task: T010 "Implement MEBDF serializer"
Task: T011 "Create parser unit tests"
Task: T012 "Create serializer unit tests"
```

## Parallel Example: User Stories After Foundational

```bash
# Once Phase 2 complete, launch P1 stories in parallel:
Task: T013-T018 (US1 - Hierarchy)
Task: T019-T027 (US2 - Export Tab)
Task: T028-T032 (US3 - Export Section)

# Or with multiple developers:
# Developer A: US1 + US2 (export operations)
# Developer B: US4 + US5 (import operations - after foundational)
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (MEBDF Parser)
3. Complete Phase 3: User Story 1 (Hierarchy)
4. Complete Phase 4: User Story 2 (Export Tab)
5. Complete Phase 5: User Story 3 (Export Section)
6. **STOP and VALIDATE**: Can read any document as MEBDF
7. Deploy/demo read-only capabilities

### Incremental Delivery

1. Setup + Foundational → Parser ready
2. Add US1 (Hierarchy) → Can navigate documents
3. Add US2 + US3 (Export) → Full read capability (MVP!)
4. Add US4 + US5 (Import) → Full write capability
5. Add US6 (Round-Trip) → Validation complete

### Suggested MVP Scope

**MVP = Phase 1-5 (Setup + Foundational + US1 + US2 + US3)**

This delivers:
- Document navigation via hierarchy
- Full tab export to MEBDF
- Section-level export

Import capabilities (US4, US5) can follow as second release.

---

## Summary

| Phase | Story | Tasks | Parallel Tasks |
|-------|-------|-------|----------------|
| 1. Setup | - | T001-T004 | 3 |
| 2. Foundational | - | T005-T012 | 3 |
| 3. US1 Hierarchy | P1 | T013-T018 | 2 |
| 4. US2 Export Tab | P1 | T019-T027 | 2 |
| 5. US3 Export Section | P1 | T028-T032 | 2 |
| 6. US4 Import Tab | P2 | T033-T041 | 2 |
| 7. US5 Import Section | P2 | T042-T046 | 2 |
| 8. US6 Round-Trip | P3 | T047-T051 | 1 |
| 9. Polish | - | T052-T056 | 3 |
| **Total** | | **56 tasks** | **20 parallel** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently completable and testable
- Commit after each task or logical group
- MEBDF parser (Phase 2) is the critical path
- Export stories (US1-3) can complete without import stories (US4-5)
