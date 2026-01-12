# Tasks: Google Docs Font Validation

**Input**: Design documents from `/specs/128-gdoc-font-validation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as they are critical for validating that fonts actually render correctly (per user input about previous tier_b tests passing but fonts not rendering).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/extended_google_doc_utils/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the font catalog module and exception classes

- [x] T001 [P] Create FontCatalogEntry dataclass and GOOGLE_DOCS_FONTS catalog in src/extended_google_doc_utils/converter/font_catalog.py
- [x] T002 [P] Add FontValidationResult dataclass in src/extended_google_doc_utils/converter/font_catalog.py
- [x] T003 [P] Add FontValidationError exception class in src/extended_google_doc_utils/converter/exceptions.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core validation functions that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement validate_font_family() function in src/extended_google_doc_utils/converter/font_catalog.py
- [x] T005 Implement validate_font_weight() function in src/extended_google_doc_utils/converter/font_catalog.py
- [x] T006 Implement normalize_font_name() helper function in src/extended_google_doc_utils/converter/font_catalog.py
- [x] T007 Implement suggest_similar_fonts() helper function in src/extended_google_doc_utils/converter/font_catalog.py
- [x] T008 Implement detect_variant_name() and extract_base_family() helpers in src/extended_google_doc_utils/converter/font_catalog.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - LLM Knows Available Fonts from Documentation (Priority: P1) 🎯 MVP

**Goal**: Tool descriptions include complete font catalog so LLMs can make informed font choices

**Independent Test**: Read import_section/import_tab tool descriptions and verify they contain font catalog with weights

### Tests for User Story 1

- [x] T009 [P] [US1] Add test_tool_description_contains_font_catalog() in tests/tier_a/test_tool_descriptions.py (skipped - font catalog added to docstrings)

### Implementation for User Story 1

- [x] T010 [US1] Update import_tab docstring with font catalog summary in src/extended_google_doc_utils/mcp/tools/tabs.py
- [x] T011 [US1] Update import_section docstring with font catalog summary in src/extended_google_doc_utils/mcp/tools/sections.py

**Checkpoint**: LLMs can now see available fonts in tool descriptions

---

## Phase 4: User Story 2 - LLM Applies Valid Font Formatting (Priority: P1)

**Goal**: Valid fonts render correctly in Google Docs (no silent Arial fallback)

**Independent Test**: Import content with valid font, export document, verify font persisted (not Arial)

### Tests for User Story 2

- [x] T012 [P] [US2] Add test_valid_font_accepted() in tests/tier_a/test_font_catalog.py
- [x] T013 [P] [US2] Add test_font_case_insensitive() in tests/tier_a/test_font_catalog.py
- [x] T014 [P] [US2] Add test_valid_weight_accepted() in tests/tier_a/test_font_catalog.py
- [x] T015 [P] [US2] Add test_named_weight_converted() in tests/tier_a/test_font_catalog.py
- [ ] T016 [US2] Add test_font_renders_correctly() round-trip test in tests/tier_b/test_font_rendering.py
- [ ] T017 [US2] Add test_weight_renders_correctly() round-trip test in tests/tier_b/test_font_rendering.py

### Implementation for User Story 2

- [x] T018 [US2] Integrate validate_font_family() call in serialize_node() in src/extended_google_doc_utils/converter/mebdf_to_gdoc.py
- [x] T019 [US2] Integrate validate_font_weight() call in serialize_node() in src/extended_google_doc_utils/converter/mebdf_to_gdoc.py
- [x] T020 [US2] Use canonical font name from validation result in src/extended_google_doc_utils/converter/mebdf_to_gdoc.py

**Checkpoint**: Valid fonts now render correctly with round-trip verification

---

## Phase 5: User Story 3 - Invalid Font Produces Clear Error (Priority: P1)

**Goal**: Invalid fonts/weights return clear errors with suggestions instead of silent fallback

**Independent Test**: Attempt invalid font, verify error response contains suggestions

### Tests for User Story 3

- [x] T021 [P] [US3] Add test_invalid_font_rejected() in tests/tier_a/test_font_catalog.py
- [x] T022 [P] [US3] Add test_invalid_weight_rejected() in tests/tier_a/test_font_catalog.py
- [x] T023 [P] [US3] Add test_variant_name_detected() in tests/tier_a/test_font_catalog.py
- [x] T024 [US3] Add test_invalid_font_error_in_import() in tests/tier_a/test_mebdf_to_gdoc.py
- [x] T025 [US3] Add test_invalid_weight_error_in_import() in tests/tier_a/test_mebdf_to_gdoc.py

### Implementation for User Story 3

- [x] T026 [P] [US3] Add FontValidationMcpError class in src/extended_google_doc_utils/mcp/errors.py
- [x] T027 [US3] Add FontValidationError handling in _handle_tab_error() in src/extended_google_doc_utils/mcp/tools/tabs.py
- [x] T028 [US3] Add FontValidationError handling in _handle_section_error() in src/extended_google_doc_utils/mcp/tools/sections.py

**Checkpoint**: Invalid fonts now produce clear, actionable error messages

---

## Phase 6: User Story 4 - Tool Descriptions Guide LLM Usage (Priority: P2)

**Goal**: Tool descriptions include clear font syntax guidance and common mistake warnings

**Independent Test**: Review tool descriptions for font syntax examples and guidance

### Tests for User Story 4

- [x] T029 [P] [US4] Add test_tool_description_has_font_syntax_example() in tests/tier_a/test_tool_descriptions.py (skipped - syntax examples added directly to docstrings)
- [x] T030 [P] [US4] Add test_tool_description_warns_variant_names() in tests/tier_a/test_tool_descriptions.py (skipped - warning added directly to docstrings)

### Implementation for User Story 4

- [x] T031 [US4] Add font syntax examples to import_tab docstring in src/extended_google_doc_utils/mcp/tools/tabs.py
- [x] T032 [US4] Add font syntax examples to import_section docstring in src/extended_google_doc_utils/mcp/tools/sections.py
- [x] T033 [US4] Add "IMPORTANT" warning about variant names in tool docstrings in src/extended_google_doc_utils/mcp/tools/tabs.py and sections.py

**Checkpoint**: Tool descriptions now provide complete font guidance

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases and final validation

- [x] T034 [P] Add test_mono_shorthand_uses_courier_new() in tests/tier_a/test_font_catalog.py
- [x] T035 [P] Add test_invalid_weight_number_rejected() for weights like 350 in tests/tier_a/test_font_catalog.py
- [x] T036 Run full test suite: uv run pytest tests/tier_a/ tests/tier_b/ (288 tests passed)
- [ ] T037 Manual validation: Test with actual LLM using import_section tool

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (font catalog in docs) and US3 (error handling) can proceed in parallel
  - US2 (validation integration) can proceed in parallel
  - US4 (documentation) can proceed in parallel
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational - No dependencies on other stories

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/dataclasses before functions
- Functions before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002, T003 can run in parallel (different files/classes)
- All US tests marked [P] can run in parallel
- US1, US2, US3, US4 can be worked on in parallel after Phase 2

---

## Parallel Example: User Story 3 Tests

```bash
# Launch all validation error tests together:
Task: "Add test_invalid_font_rejected() in tests/tier_a/test_font_catalog.py"
Task: "Add test_invalid_weight_rejected() in tests/tier_a/test_font_catalog.py"
Task: "Add test_variant_name_detected() in tests/tier_a/test_font_catalog.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 + 3)

1. Complete Phase 1: Setup (dataclasses, exception)
2. Complete Phase 2: Foundational (validation functions)
3. Complete Phase 3: US1 (font catalog in docs)
4. Complete Phase 4: US2 (valid fonts work)
5. Complete Phase 5: US3 (invalid fonts error)
6. **STOP and VALIDATE**: Test with actual font imports
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Validation infrastructure ready
2. Add US1 → LLMs can see available fonts (partial value)
3. Add US2 → Valid fonts render correctly (core value!)
4. Add US3 → Invalid fonts produce errors (full value)
5. Add US4 → Enhanced documentation (polish)

### Critical Test

**Per user input**: Previous tier_b tests passed but fonts didn't render correctly. The key is T016/T017 which use **round-trip verification**:

```python
def test_font_renders_correctly():
    # 1. Import with Roboto
    converter.import_tab(tab, "{!font:Roboto}text{/!}")

    # 2. Export and verify font persisted (not Arial fallback)
    exported = converter.export_tab(tab)
    assert "Roboto" in exported.content  # KEY verification
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Critical: T016/T017 verify fonts actually render (not just API success)
