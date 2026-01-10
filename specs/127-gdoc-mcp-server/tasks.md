# Tasks: Google Docs MCP Server

**Input**: Design documents from `/specs/127-gdoc-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included as the plan.md explicitly requires contract tests, round-trip tests, and LLM integration tests per the Testing Standards section.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and MCP module structure

- [x] T001 Add `mcp>=1.25.0` dependency to pyproject.toml with optional [mcp] extra
- [x] T002 Create MCP module structure with __init__.py in src/extended_google_doc_utils/mcp/__init__.py
- [x] T003 [P] Create tools subpackage with __init__.py in src/extended_google_doc_utils/mcp/tools/__init__.py
- [x] T004 [P] Create test directory structure in tests/mcp/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement response dataclasses (DocumentSummary, TabInfo, HeadingInfo, etc.) in src/extended_google_doc_utils/mcp/schemas.py
- [x] T006 [P] Implement structured error types (ErrorDetail, ErrorResponse, all error classes) in src/extended_google_doc_utils/mcp/errors.py
- [x] T007 Create FastMCP server skeleton with credential loading in src/extended_google_doc_utils/mcp/server.py
- [x] T008 Implement server startup that initializes CredentialManager and GoogleDocsConverter in src/extended_google_doc_utils/mcp/server.py
- [x] T009 Add __main__.py entry point for `python -m extended_google_doc_utils.mcp.server` in src/extended_google_doc_utils/mcp/__main__.py
- [x] T010 [P] Create MCP test client fixture using SDK in-memory transport in tests/mcp/conftest.py

**Checkpoint**: Foundation ready - MCP server starts and is ready for tool registration

---

## Phase 3: User Story 1 - Read and Edit a Specific Section (Priority: P1) 🎯 MVP

**Goal**: Enable LLMs to safely read and edit specific sections of Google Docs without affecting other content

**Independent Test**: Select a section, modify its content, verify only that section changed while others remain identical

### Tests for User Story 1

- [x] T011 [P] [US1] Contract test for get_hierarchy tool using MCP test client in tests/mcp/test_navigation_tools.py
- [x] T012 [P] [US1] Contract test for export_section tool using MCP test client in tests/mcp/test_section_tools.py
- [x] T013 [P] [US1] Contract test for import_section tool using MCP test client in tests/mcp/test_section_tools.py
- [x] T014 [US1] Integration test for section round-trip (export → modify → import → verify isolation) in tests/mcp/test_section_tools.py

### Implementation for User Story 1

- [x] T015 [P] [US1] Implement get_hierarchy tool in src/extended_google_doc_utils/mcp/tools/navigation.py
- [x] T016 [P] [US1] Implement export_section tool in src/extended_google_doc_utils/mcp/tools/sections.py
- [x] T017 [US1] Implement import_section tool in src/extended_google_doc_utils/mcp/tools/sections.py
- [x] T018 [US1] Register navigation and section tools with FastMCP server in src/extended_google_doc_utils/mcp/server.py
- [x] T019 [US1] Add error handling for AnchorNotFoundError, MultipleTabsError in section tools

**Checkpoint**: User Story 1 complete - LLM can get hierarchy, export a section, and import back with isolation

---

## Phase 4: User Story 2 - Discover Available Tools (Priority: P1)

**Goal**: Ensure all tools have clear descriptions enabling LLMs to select correct tools on first attempt

**Independent Test**: Use MCP inspector to list tools, verify schema completeness and description quality

### Tests for User Story 2

- [x] T020 [P] [US2] Test that all tools have descriptions using MCP test client in tests/mcp/test_server.py
- [x] T021 [P] [US2] Test that all tool parameters have descriptions using MCP test client in tests/mcp/test_server.py
- [x] T022 [US2] Test tool listing and schema completeness via MCP inspector protocol in tests/mcp/test_server.py

### Implementation for User Story 2

- [x] T023 [P] [US2] Implement list_documents tool with detailed docstring in src/extended_google_doc_utils/mcp/tools/navigation.py
- [x] T024 [P] [US2] Implement get_metadata tool with detailed docstring in src/extended_google_doc_utils/mcp/tools/navigation.py
- [x] T025 [P] [US2] Implement export_tab tool in src/extended_google_doc_utils/mcp/tools/tabs.py
- [x] T026 [P] [US2] Implement import_tab tool with WARNING about full replacement in src/extended_google_doc_utils/mcp/tools/tabs.py
- [x] T027 [US2] Review and enhance all tool docstrings for LLM clarity (purpose, when to use, parameter semantics)
- [x] T028 [US2] Register tab tools with FastMCP server in src/extended_google_doc_utils/mcp/server.py
- [x] T029 [US2] Validate all tools return structured responses (success/failure, data, or error) in src/extended_google_doc_utils/mcp/server.py

**Checkpoint**: User Story 2 complete - All 7 navigation/section/tab tools registered with clear documentation

---

## Phase 5: User Story 3 - Apply Consistent Formatting (Priority: P2)

**Goal**: Enable document formatting cleanup with consistent fonts and styles

**Independent Test**: Export document, apply formatting rules, reimport, verify all paragraphs conform to specified styles

### Tests for User Story 3

- [x] T030 [P] [US3] Contract test for normalize_formatting tool using MCP test client in tests/mcp/test_formatting_tools.py
- [x] T031 [US3] Integration test for formatting normalization (mixed fonts → consistent) in tests/mcp/test_formatting_tools.py

### Implementation for User Story 3

- [x] T032 [US3] Implement normalize_formatting tool (export → transform MEBDF → import) in src/extended_google_doc_utils/mcp/tools/formatting.py
- [x] T033 [US3] Implement MEBDF block formatting transformation for font normalization in src/extended_google_doc_utils/mcp/tools/formatting.py
- [x] T034 [US3] Ensure embedded objects are preserved during formatting transformation
- [x] T035 [US3] Register normalize_formatting tool with FastMCP server in src/extended_google_doc_utils/mcp/server.py

**Checkpoint**: User Story 3 complete - LLM can normalize document formatting

---

## Phase 6: User Story 4 - Match Formatting from Reference Document (Priority: P2)

**Goal**: Enable style matching between documents (apply template styles to target)

**Independent Test**: Extract styles from source, apply to target, verify target formatting matches source patterns

### Tests for User Story 4

- [x] T036 [P] [US4] Contract test for extract_styles tool using MCP test client in tests/mcp/test_formatting_tools.py
- [x] T037 [P] [US4] Contract test for apply_styles tool using MCP test client in tests/mcp/test_formatting_tools.py
- [x] T038 [US4] Integration test for style matching workflow (extract → apply) in tests/mcp/test_formatting_tools.py

### Implementation for User Story 4

- [x] T039 [P] [US4] Implement extract_styles tool in src/extended_google_doc_utils/mcp/tools/formatting.py
- [x] T040 [US4] Implement apply_styles tool in src/extended_google_doc_utils/mcp/tools/formatting.py
- [x] T041 [US4] Register extract_styles and apply_styles tools with FastMCP server in src/extended_google_doc_utils/mcp/server.py

**Checkpoint**: User Story 4 complete - LLM can match formatting between documents

---

## Phase 7: User Story 5 - Update Section with Rich Content (Priority: P2)

**Goal**: Ensure sections can be updated with hyperlinks, bold/italic, highlights, and image placeholders

**Independent Test**: Write section with various formatting types, verify each renders correctly in Google Docs

### Tests for User Story 5

- [x] T042 [US5] Integration test for rich content round-trip (links, bold, italic, highlights) in tests/mcp/test_section_tools.py
- [x] T043 [US5] Integration test for image placeholder preservation during section update in tests/mcp/test_section_tools.py

### Implementation for User Story 5

- [x] T044 [US5] Verify import_section correctly handles MEBDF formatting extensions in src/extended_google_doc_utils/mcp/tools/sections.py
- [x] T045 [US5] Add validation for embedded object placeholders in import_section
- [x] T046 [US5] Ensure warnings are returned for unsupported formatting types

**Checkpoint**: User Story 5 complete - Rich content (links, formatting, images) works in section updates

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, documentation, and final validation

### Automated MCP Testing

- [x] T047 [P] Add MCP inspector-based test that calls each tool and validates response structure in tests/mcp/test_inspector.py
- [x] T048 [P] Add server lifecycle tests (startup, shutdown) using MCP test client in tests/mcp/test_server.py
- [x] T049 [P] Add performance validation for tool discovery (<1s) in tests/mcp/test_server.py
- [x] T050 [P] Add performance validation for hierarchy retrieval (<3s) in tests/mcp/test_navigation_tools.py

### Documentation

- [x] T051 Update quickstart.md with Claude Desktop configuration instructions
- [x] T052 [P] Update quickstart.md with Claude Code configuration instructions
- [x] T053 [P] Add troubleshooting section to quickstart.md for common errors
- [x] T054 Add MCP server installation instructions to project README.md
- [x] T055 Document all 10 tools with usage examples in quickstart.md

### Final Validation

- [x] T056 Run quickstart.md validation (verify all documented workflows work via MCP test client)
- [x] T057 Final code review for docstring completeness and LLM discoverability

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 but can run in parallel
  - US3, US4, US5 are P2 and can run in parallel after US1/US2
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Requires schemas.py, errors.py, server skeleton, test fixture → Delivers core section editing
- **User Story 2 (P1)**: Requires server skeleton, test fixture → Delivers full tool catalog with discoverability
- **User Story 3 (P2)**: Requires export/import working (US1) → Delivers formatting normalization
- **User Story 4 (P2)**: Requires formatting infrastructure (US3) → Delivers style matching
- **User Story 5 (P2)**: Requires section import working (US1) → Validates rich content handling

### Within Each User Story

- Tests MUST be written first (TDD for contract tests)
- Tests use MCP test client fixture for in-process validation
- Infrastructure (schemas, errors) before tools
- Tools before server registration
- Story complete before declaring checkpoint

### Parallel Opportunities

Within Phase 2 (Foundational):
- T005 (schemas.py), T006 (errors.py), T010 (test fixture) can run in parallel

Within Phase 3 (US1):
- T011, T012, T013 (tests) can run in parallel
- T015, T016 (get_hierarchy, export_section) can run in parallel

Within Phase 4 (US2):
- T020, T021 (tests) can run in parallel
- T023, T024, T025, T026 (list_documents, get_metadata, export_tab, import_tab) can run in parallel

Within Phase 8 (Polish):
- T047, T048, T049, T050 (automated tests) can run in parallel
- T051, T052, T053 (documentation) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together:
Task: "Contract test for get_hierarchy tool using MCP test client"
Task: "Contract test for export_section tool using MCP test client"
Task: "Contract test for import_section tool using MCP test client"

# Then launch parallel tool implementations:
Task: "Implement get_hierarchy tool in navigation.py"
Task: "Implement export_section tool in sections.py"
```

---

## Parallel Example: Phase 8 Documentation

```bash
# Launch documentation tasks together:
Task: "Update quickstart.md with Claude Desktop configuration"
Task: "Update quickstart.md with Claude Code configuration"
Task: "Add troubleshooting section to quickstart.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (6 tasks)
3. Complete Phase 3: User Story 1 (9 tasks)
4. **STOP and VALIDATE**: Test section export/import/isolation via MCP test client
5. Deploy/demo if ready - LLM can now safely edit document sections

### Incremental Delivery

1. Setup + Foundational → Server starts, MCP test client works
2. Add US1 → Section editing MVP
3. Add US2 → Full tool catalog with all navigation/tab tools
4. Add US3 → Formatting normalization
5. Add US4 → Style matching
6. Add US5 → Rich content validation
7. Polish → MCP inspector tests, documentation, final review

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers:
- Working MCP server
- get_hierarchy tool
- export_section tool
- import_section tool
- Section isolation guarantee
- MCP test client for validation

Total MVP tasks: 19 tasks (T001-T019)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests use MCP SDK in-memory transport for fast, reliable testing
- Tests use tier_b markers for mocked tests, tier_a for real API tests
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
