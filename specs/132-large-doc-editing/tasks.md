# Tasks: Large Document Editing

**Input**: Design documents from `/specs/132-large-doc-editing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included because the spec and plan explicitly call for contract tests, edge case tests, and tier A tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — this feature extends an existing codebase. This phase handles prerequisite data model changes that multiple stories share.

- [x] T001 [P] Add `word_count: int = 0` and `char_count: int = 0` fields to `HeadingAnchor` in `src/extended_google_doc_utils/converter/types.py`
- [x] T002 Add `total_word_count: int = 0` and `total_char_count: int = 0` fields to `HierarchyResult` in `src/extended_google_doc_utils/converter/types.py`
- [x] T003 [P] Add `word_count: int = 0` and `char_count: int = 0` fields to `HeadingInfo` dataclass in `src/extended_google_doc_utils/mcp/schemas.py`
- [x] T004 Add `total_word_count: int = 0` and `total_char_count: int = 0` fields to `HierarchyResponse` dataclass in `src/extended_google_doc_utils/mcp/schemas.py`
- [x] T005 Add `format: str = "mebdf"` field to `ReadTabResponse` dataclass in `src/extended_google_doc_utils/mcp/schemas.py`

**Checkpoint**: All shared data model changes in place. User story implementation can begin.

---

## Phase 2: User Story 2 - Understand Document Structure with Sizes (Priority: P1) 🎯 MVP

**Goal**: `get_hierarchy` returns word/character counts per section so users can judge document size before reading.

**Independent Test**: Call `get_hierarchy` on a document with sections of varying sizes. Verify word counts are returned per heading and totals are accurate.

### Tests for User Story 2

- [x] T006 [P] [US2] Create test file `tests/tier_a/test_hierarchy_sizes.py` with tests: section word/char count accuracy for multi-heading document, preamble counting, empty document returns zeros, document with no headings counts all content as preamble total

### Implementation for User Story 2

- [x] T007 [US2] Add `_count_section_text()` helper to `src/extended_google_doc_utils/converter/hierarchy.py` — extracts plain text from body elements within a `[start_index, end_index)` range and returns `(word_count, char_count)` tuple. Skip non-text elements (inlineObjectElement, etc.). Count words by splitting on whitespace, chars by len of stripped text.
- [x] T008 [US2] Modify `get_hierarchy()` in `src/extended_google_doc_utils/converter/hierarchy.py` — after extracting headings, use `get_all_sections()` from `section_utils.py` to get section boundaries, call `_count_section_text()` for each section, populate `word_count`/`char_count` on each `HeadingAnchor`, and set `total_word_count`/`total_char_count` on the `HierarchyResult`
- [x] T009 [US2] Update `format_hierarchy()` in `src/extended_google_doc_utils/converter/hierarchy.py` — append `(N words)` hint after each heading text in the markdown output
- [x] T010 [US2] Wire up new fields in `get_hierarchy` tool in `src/extended_google_doc_utils/mcp/tools/navigation.py` — map `word_count`, `char_count` from `HeadingAnchor` to `HeadingInfo`, and `total_word_count`, `total_char_count` from `HierarchyResult` to `HierarchyResponse`
- [x] T011 [US2] Run tests: `cd src && pytest ../tests/tier_a/test_hierarchy_sizes.py -v`

**Checkpoint**: `get_hierarchy` returns section sizes. Users can see document structure with word counts.

---

## Phase 3: User Story 5 - Read Tab in Plain Markdown (Priority: P3, but foundational for US1)

**Goal**: `read_tab` supports `format="plain"` returning clean markdown without MEBDF markers. This is listed as P3 in the spec but is a prerequisite for US1's export workflow, so it's implemented here.

**Independent Test**: Read the same tab in both `"plain"` and `"mebdf"` formats. Verify plain version has no `{!...}`, `{/!}`, `{^...}` markers but preserves all text, headings, lists, and links.

### Tests for User Story 5

- [x] T012 [P] [US5] Create test file `tests/tier_a/test_plain_serializer.py` with tests: plain text passthrough, bold/italic preserved as standard markdown, MEBDF formatting markers stripped (`{!color:red}text{/!}` → `text`), heading anchors stripped (`{^ h.abc}` removed), embedded objects become `[image]` placeholder, links preserved, lists preserved, empty document produces empty string

### Implementation for User Story 5

- [x] T013 [US5] Create `src/extended_google_doc_utils/converter/plain_serializer.py` — implement `PlainMarkdownSerializer` class with `serialize(document: DocumentNode) -> str` method. Walk AST nodes: `TextNode` → emit content, `BoldNode` → `**text**`, `ItalicNode` → `*text*`, `HeadingNode` → `# text` (no anchor), `FormattingNode` → emit child text only (strip formatting wrapper), `EmbeddedObjectNode` → `[image]`, `ListNode`/`ListItemNode` → standard markdown lists, `ParagraphNode` → join children with double newline
- [x] T014 [US5] Add `format: str = "mebdf"` parameter to `read_tab()` method in `src/extended_google_doc_utils/converter/converter.py` — when `format="plain"`, import and use `PlainMarkdownSerializer` instead of `MebdfSerializer` in `export_body()`. Pass format through to `export_body()` which selects the serializer.
- [x] T015 [US5] Add `format: str = "mebdf"` parameter to `export_body()` in `src/extended_google_doc_utils/converter/gdoc_to_mebdf.py` — accept format param, use `PlainMarkdownSerializer` when `format="plain"`, default to `MebdfSerializer`
- [x] T016 [US5] Add `format` parameter to `read_tab` MCP tool in `src/extended_google_doc_utils/mcp/tools/tabs.py` — add `format: Annotated[str, Field(...)] = "mebdf"` parameter, pass through to converter, echo `format` back in `ReadTabResponse`
- [x] T017 [P] [US5] Create test file `tests/mcp/test_read_tab_format.py` with tests: `format="mebdf"` returns MEBDF (backward compat), `format="plain"` returns plain markdown, invalid format value returns error, default format is `"mebdf"`
- [x] T018 [US5] Run tests: `cd src && pytest ../tests/tier_a/test_plain_serializer.py ../tests/mcp/test_read_tab_format.py -v`

**Checkpoint**: `read_tab(format="plain")` works. Users can get clean markdown for search purposes.

---

## Phase 4: User Story 1 - Edit a Specific Paragraph in a Large Document (Priority: P1)

**Goal**: End-to-end targeted editing: read plain → save to disk → grep → read section → write section. This story is primarily about the skill orchestration (US4) using US2 and US5 as building blocks.

**Independent Test**: Export a large document to a file, grep for a known phrase, identify the section, read that section in MEBDF, edit it, write it back, verify only the target section changed.

**Note**: The MCP tool work for this story is already done in US2 (hierarchy sizes) and US5 (plain format). The remaining work is validating the full flow works together.

### Implementation for User Story 1

- [x] T019 [US1] Create a manual integration test script at `tests/tier_b/test_large_doc_workflow.py` — end-to-end test that: calls `get_metadata`, calls `get_hierarchy` and verifies sizes, calls `read_tab(format="plain")` and writes to temp file, greps the file for a known term, calls `read_section` for the matching section, verifies content is MEBDF. Requires Tier B credentials. Mark with `@pytest.mark.tier_b`.

**Checkpoint**: The MCP tool pipeline for large doc editing is validated end-to-end.

---

## Phase 5: User Story 4 - Guided Workflow via Skill (Priority: P2)

**Goal**: A Claude Code skill that orchestrates the large-document editing workflow step by step.

**Independent Test**: Invoke `/edit-google-doc` and verify it guides through metadata → hierarchy → export → search → edit → cleanup.

### Implementation for User Story 4

- [x] T020 [US4] Create `.claude/skills/` directory if it doesn't exist
- [x] T021 [US4] Create skill definition at `.claude/skills/edit-google-doc.md` — include: skill description and trigger instructions, step-by-step workflow (get_metadata → get_hierarchy with sizes → read_tab plain → Write to /tmp/gdoc-{doc_id}-{tab_id}.md → guide user to Grep/Read file → read_section for target → write_section → cleanup temp file), decision logic (skip export for small docs <2000 words, repeat for multi-tab), error handling guidance, MEBDF formatting reference for the edit step
- [x] T022 [US4] Update tool descriptions in `src/extended_google_doc_utils/mcp/tools/tabs.py` — enhance `read_tab` docstring to mention `format="plain"` is useful for large-document workflows where content will be saved to disk for searching
- [x] T023 [US4] Update tool descriptions in `src/extended_google_doc_utils/mcp/tools/navigation.py` — enhance `get_hierarchy` docstring to mention word counts help judge section size before deciding what to read

**Checkpoint**: Skill is defined and discoverable. Tool descriptions guide toward the optimal workflow.

---

## Phase 6: User Story 3 - Search Across Multiple Tabs (Priority: P2)

**Goal**: Support searching across all tabs of a multi-tab document by exporting each tab to a separate file.

**Independent Test**: Export 3 tabs to separate files, search across all files for a term, verify results identify which tab contains the match.

### Implementation for User Story 3

- [x] T024 [US3] Enhance skill definition in `.claude/skills/edit-google-doc.md` — add multi-tab workflow section: after get_metadata shows tabs, export each tab to `/tmp/gdoc-{doc_id}-{tab_title}.md` (using tab title in filename for identification), guide user to Grep across all exported files, identify matching tab and section, proceed with read_section/write_section for the target

**Checkpoint**: Multi-tab search workflow is documented in the skill. Users can search across tabs on disk.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T025 Verify backward compatibility: run existing test suite `cd src && pytest ../tests/tier_a/ -v` — all existing tests must still pass with no changes
- [x] T026 Run ruff linter on all modified/new files: `cd src && .venv/bin/ruff check .`
- [x] T027 Verify `HeadingAnchor` frozen dataclass compatibility — ensure adding defaulted fields doesn't break existing constructor calls (fields have defaults, so positional args still work)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — data model changes only, can start immediately
- **Phase 2 (US2)**: Depends on T001-T004 from Phase 1 (type fields must exist)
- **Phase 3 (US5)**: Depends on T005 from Phase 1 (ReadTabResponse format field). Independent of Phase 2.
- **Phase 4 (US1)**: Depends on Phase 2 + Phase 3 (needs both hierarchy sizes and plain format)
- **Phase 5 (US4)**: Depends on Phase 2 + Phase 3 (skill references enhanced tools)
- **Phase 6 (US3)**: Depends on Phase 5 (extends the skill definition)
- **Phase 7 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US2 (hierarchy sizes)**: Independent — can start after Phase 1 setup
- **US5 (plain format)**: Independent — can start after Phase 1 setup
- **US1 (targeted editing)**: Depends on US2 + US5 (uses both features)
- **US4 (skill)**: Depends on US2 + US5 (skill references both features)
- **US3 (multi-tab)**: Depends on US4 (extends the skill)

### Within Each User Story

- Tests written first (T006, T012, T017)
- Core implementation (serializer, hierarchy logic)
- MCP tool wiring
- Integration validation

### Parallel Opportunities

- **Phase 1**: All tasks (T001-T005) can run in parallel (different files)
- **Phase 2 + Phase 3**: Can run in parallel (US2 and US5 are independent)
- **Within Phase 3**: T012 and T017 (test files) can run in parallel
- **Phase 5 + Phase 4**: Can overlap (skill definition doesn't block integration test)

---

## Parallel Example: Phase 2 + Phase 3

```bash
# These two phases can run in parallel after Phase 1:

# Phase 2 (US2 - hierarchy sizes):
Task: T006 "Create test_hierarchy_sizes.py"
Task: T007 "Add _count_section_text() helper"
Task: T008 "Modify get_hierarchy() to compute sizes"

# Phase 3 (US5 - plain format) — simultaneously:
Task: T012 "Create test_plain_serializer.py"
Task: T013 "Create PlainMarkdownSerializer"
Task: T014 "Add format param to converter.read_tab()"
```

---

## Implementation Strategy

### MVP First (US2 + US5)

1. Complete Phase 1: Data model changes (5 tasks, ~15 min)
2. Complete Phase 2: Hierarchy sizes (6 tasks) — in parallel with →
3. Complete Phase 3: Plain format (7 tasks)
4. **STOP and VALIDATE**: Both features work independently
5. The MCP tools now support large-document workflows even without the skill

### Incremental Delivery

1. Phase 1 → Data model ready
2. Phase 2 (US2) → Users can see section sizes in hierarchy
3. Phase 3 (US5) → Users can read tabs in plain markdown
4. Phase 4 (US1) → Validated end-to-end workflow
5. Phase 5 (US4) → Skill guides the workflow automatically
6. Phase 6 (US3) → Multi-tab search in skill
7. Phase 7 → Polish and verify

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US5 (P3 in spec) is implemented before US1 (P1) because US1 depends on plain format
- The skill (US4) is a markdown file, not Python code — no unit tests needed
- Tier B tests (T019) require Google OAuth credentials and a test document
