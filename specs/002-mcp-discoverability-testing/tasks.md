# Tasks: MCP Discoverability Testing

**Input**: Design documents from `/specs/002-mcp-discoverability-testing/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package structure and install dependencies

- [x] T001 Create discoverability package structure: `src/extended_google_doc_utils/discoverability/__init__.py`, `__main__.py`, and empty module files (`models.py`, `loader.py`, `runner.py`, `mock.py`, `scorer.py`, `reporter.py`) per plan.md project structure
- [x] T002 Add `anthropic>=0.40.0` and `pyyaml` to project dependencies (test harness only — check pyproject.toml or requirements.txt for existing dependency management pattern)
- [x] T003 [P] Add `reports/` directory to `.gitignore` and create empty `reports/.gitkeep`
- [x] T004 [P] Create `src/extended_google_doc_utils/discoverability/test_suites/` directory with empty `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data models, YAML loader, and MCP-to-Anthropic bridge — MUST be complete before any user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement all dataclasses in `src/extended_google_doc_utils/discoverability/models.py`: RunConfig, TestSuite, UserIntent, PromptVariant, TestRun, IntentResult, VariantResult, TrialResult, AttemptRecord, DesirePathEntry — per data-model.md entity definitions. Use `@dataclass` with type hints. Include enum for classification ("correct", "right_tool_wrong_params", "wrong_tool", "no_tool_call") and prompt style ("explicit", "natural", "indirect", "ambiguous").
- [x] T006 Implement YAML test suite loader in `src/extended_google_doc_utils/discoverability/loader.py`: `load_test_suite(path: str) -> TestSuite` that parses YAML files matching the format in contracts/api.md. Validate required fields (intent name, expected_tools, variant text/style). Raise `ValidationError` for malformed input. Support loading a single file or a directory of YAML files.
- [x] T007 Implement MCP-to-Anthropic tool bridge in `src/extended_google_doc_utils/discoverability/runner.py` (partial — connection logic only): async function that starts the MCP server as a subprocess via `mcp.client.stdio.stdio_client`, calls `session.list_tools()`, and converts MCP tool definitions to Anthropic tool format (`{"name": ..., "description": ..., "input_schema": ...}`). Per research.md Decision 2.

**Checkpoint**: Foundation ready — models can be instantiated, YAML can be loaded, MCP server can be connected to

---

## Phase 3: User Story 1 — Run Discoverability Tests (Priority: P1) MVP

**Goal**: Execute a single prompt against the MCP server through Claude and capture every tool call the LLM makes, classifying each as correct/wrong_tool/right_tool_wrong_params.

**Independent Test**: Run one prompt, one trial, verify the harness captures the complete tool call sequence with correct classifications.

### Implementation for User Story 1

- [x] T008 [US1] Implement mock tool responses in `src/extended_google_doc_utils/discoverability/mock.py`: `get_mock_response(tool_name: str, parameters: dict) -> dict` returning canned success responses for each of the 12 MCP tools. Responses should be realistic enough that the LLM can continue its workflow (e.g., `get_hierarchy` returns a fake heading list with anchor IDs). Per research.md Decision 3.
- [x] T009 [US1] Implement single-trial execution in `src/extended_google_doc_utils/discoverability/runner.py`: `async run_single_trial(prompt_text: str, tools: list[dict], expected_tools: list[str], config: RunConfig) -> TrialResult`. Core agentic loop: send prompt to Anthropic `client.messages.create()` with MCP tools, while `stop_reason == "tool_use"` capture each `tool_use` block as an AttemptRecord, return tool result, continue. Enforce `max_attempts` limit. **Mock mode**: call `get_mock_response()` from mock.py. **Live mode**: call `session.call_tool()` to execute against real MCP server. Mode is determined by `config.mode`. Per FR-006, FR-006a, FR-006b, FR-007, FR-008.
- [x] T010 [US1] Implement tool call classification in `src/extended_google_doc_utils/discoverability/runner.py`: evaluate each AttemptRecord against expected_tools using subset-match logic (FR-009). Track which expected steps have been satisfied. Classify as "correct" (matches next expected step), "right_tool_wrong_params" (tool name matches but params don't validate), "wrong_tool" (tool not in expected sequence), or "no_tool_call" (LLM responded with text only). Only "correct" counts as a successful step for scoring; all other classifications are failures. The classification detail is retained for diagnostic reporting. Per FR-009, FR-010.
- [x] T011 [US1] Implement trial success evaluation: after the agentic loop completes, determine if all expected_tools were called in order (subset match — extra tools allowed, per clarification). Set `TrialResult.success` accordingly.

**Checkpoint**: Can run `run_single_trial()` with a prompt and get back a TrialResult with classified AttemptRecords. This is the MVP — proves the core capture mechanism works.

---

## Phase 4: User Story 2 — Multi-Variant Multi-Trial Execution (Priority: P1)

**Goal**: Run multiple prompt variants per intent, each with 10 independent trials, and aggregate results.

**Independent Test**: Define an intent with 3 prompt variants, run with 3 trials each, verify per-variant and per-intent aggregate statistics.

### Implementation for User Story 2

- [x] T012 [US2] Implement multi-trial execution in `src/extended_google_doc_utils/discoverability/runner.py`: `async run_prompt(prompt: PromptVariant, expected_tools: list[str], config: RunConfig) -> VariantResult`. Run `config.trials` independent trials (default 10) for a single prompt variant. Each trial is a fresh conversation. Aggregate into VariantResult with first_attempt_rate, success_rate, avg_attempts, most_common_first_tool. Per FR-008a, FR-008b.
- [x] T013 [US2] Implement intent-level execution in `src/extended_google_doc_utils/discoverability/runner.py`: `async run_intent(intent: UserIntent, config: RunConfig) -> IntentResult`. Iterate through all prompt variants, calling `run_prompt()` for each. Aggregate into IntentResult with cross-variant statistics. Per FR-014.
- [x] T014 [US2] Implement suite-level execution in `src/extended_google_doc_utils/discoverability/runner.py`: `async run_test_suite(suite: TestSuite, config: RunConfig) -> TestRun`. Iterate through all intents, capture git commit hash, snapshot tool descriptions, populate TestRun. Support `--intent` filter for running a single intent. Per FR-011.
- [x] T015 [US2] Compute DesirePathEntry aggregation in `src/extended_google_doc_utils/discoverability/runner.py` (or models.py): after all trials for a variant complete, aggregate tool selection patterns — frequency, avg_position, as_first_call — into `VariantResult.desire_path`.

**Checkpoint**: Can run a full test suite and get back a TestRun with complete results for all intents × variants × trials.

---

## Phase 5: User Story 3 — Generate Desire-Path Report (Priority: P1)

**Goal**: After a test run completes, generate a self-contained markdown report showing tool call sequences, desire-path mismatches, and per-intent breakdowns.

**Independent Test**: Feed a TestRun with known data to the reporter and verify the output markdown matches the expected report structure from contracts/api.md.

### Implementation for User Story 3

- [x] T016 [US3] Implement report header and summary section in `src/extended_google_doc_utils/discoverability/reporter.py`: `generate_report(run: TestRun, output_dir: str) -> str`. Write report header (date, model, mode, commit, trials) and summary table (first-attempt rate, overall success rate, failure rate, avg attempts). Per FR-017, FR-018, FR-022.
- [x] T017 [US3] Implement per-intent results section in `src/extended_google_doc_utils/discoverability/reporter.py`: for each intent, write expected tools, overall rates, then per-variant detail (first-attempt rate, most common first tool, tool call sequence). Highlight **DESIRE PATH MISMATCH** when the most common first tool differs from expected. Per FR-019, FR-020.
- [x] T018 [US3] Implement desire-path analysis section in `src/extended_google_doc_utils/discoverability/reporter.py`: aggregate "tools the LLM reaches for first" across all intents. Output table with tool name, times called first, expected first count, mismatch rate. Per FR-020.
- [x] T019 [US3] Implement tool description snapshot section in `src/extended_google_doc_utils/discoverability/reporter.py`: write full tool name + description for each MCP tool from `TestRun.tool_descriptions`. Per FR-021, FR-023.
- [x] T020 [US3] Implement file output in `src/extended_google_doc_utils/discoverability/reporter.py`: save report as `desire-path-YYYY-MM-DD-HHMMSS.md` in output_dir. Return the file path. Per FR-022.

**Checkpoint**: Can generate a complete desire-path markdown report from test run data. The three P1 stories (execute + variants + report) are now functional end-to-end.

---

## Phase 6: User Story 4 — Scoring (Priority: P2)

**Goal**: Compute quantitative discoverability metrics from test run data.

**Independent Test**: Feed known test data (e.g., 8/10 first-attempt successes) to the scorer and verify computed metrics match expected values.

### Implementation for User Story 4

- [x] T021 [P] [US4] Implement score computation in `src/extended_google_doc_utils/discoverability/scorer.py`: `compute_scores(run: TestRun) -> dict` computing first_attempt_rate, overall_success_rate, failure_rate, avg_attempts_to_success per contracts/api.md output format. Per FR-012, FR-013, FR-015, FR-016.
- [x] T022 [P] [US4] Implement per-intent breakdown in `src/extended_google_doc_utils/discoverability/scorer.py`: per-intent success rates and untested tools detection (compare test suite tool coverage against MCP server tool list). Per FR-014, FR-025.
- [x] T023 [US4] Integrate scorer output into reporter: call `compute_scores()` from `generate_report()` and populate the summary table and per-intent statistics from scorer output rather than inline calculation.

**Checkpoint**: Scores are computed programmatically and embedded in reports.

---

## Phase 7: User Story 5 + 6 — Tracking & Test Suite Definition (Priority: P2)

**Goal (US5)**: Reports contain enough metadata (commit hash, tool descriptions, timestamps) to enable comparison across runs.

**Goal (US6)**: A default test suite covers all 6 core intents with 5 variants each, and the CLI provides `run` and `list` commands.

**Independent Test (US5)**: Run the suite twice, verify reports have different timestamps and can be compared.

**Independent Test (US6)**: Add a new intent YAML file, verify the harness loads and executes it without code changes.

### Implementation for User Story 5

- [x] T024 [US5] Capture git commit hash in `src/extended_google_doc_utils/discoverability/runner.py`: at start of `run_test_suite()`, run `git rev-parse --short HEAD` via subprocess and store in `TestRun.commit_hash`. Per FR-021, FR-024.
- [x] T025 [US5] Capture tool description snapshot in `src/extended_google_doc_utils/discoverability/runner.py`: after `session.list_tools()`, store `{tool.name: tool.description}` dict in `TestRun.tool_descriptions`. Per FR-021, FR-024.

### Implementation for User Story 6

- [x] T026 [US6] Author default test suite in `src/extended_google_doc_utils/discoverability/test_suites/default.yaml`: 6 intents (edit-section, read-document, cleanup-formatting, transfer-styles, find-document, understand-structure) with 5 prompt variants each (one per style: explicit, natural, indirect, ambiguous, plus one additional natural variant). Expected tool sequences per research.md "Default Test Suite" section. Per FR-001, FR-002, FR-003, FR-004, FR-005.
- [x] T027 [US6] Implement CLI entry point in `src/extended_google_doc_utils/discoverability/__main__.py`: `run` command (loads suite, runs harness, generates report, prints summary to stdout) and `list` command (loads suite, prints intents and variants). Support all flags from contracts/api.md CLI section (--suite, --model, --mode, --trials, --max-attempts, --intent, --output-dir). Use argparse. Per FR-011.
- [x] T028 [US6] Wire CLI to runner + reporter pipeline in `src/extended_google_doc_utils/discoverability/__main__.py`: `run` command calls `load_test_suite()` → `run_test_suite()` → `compute_scores()` → `generate_report()`. Print summary scores to stdout after report is written.

**Checkpoint**: Full feature functional — can run `python -m extended_google_doc_utils.discoverability run` and get a complete desire-path report.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Tests, validation, and cleanup

- [x] T029 [P] Unit tests for loader in `tests/unit/test_loader.py`: valid YAML parsing, missing fields validation, directory loading, malformed YAML error handling
- [x] T030 [P] Unit tests for scorer in `tests/unit/test_scorer.py`: known-data tests for first-attempt rate (8/10 = 80%), avg attempts (1.375), failure rate (10%), untested tools detection
- [x] T031 [P] Unit tests for reporter in `tests/unit/test_reporter.py`: verify report structure from known TestRun data — header fields, summary table, per-intent sections, desire-path analysis table, tool description snapshot section
- [x] T032 [P] Unit tests for mock in `tests/unit/test_mock.py`: verify each of the 12 tools returns a well-formed response, verify unknown tool raises error
- [x] T033 Integration test in `tests/integration/test_harness_e2e.py`: full mock-mode run with a minimal test suite (1 intent, 2 variants, 2 trials) — requires ANTHROPIC_API_KEY. Verify TestRun is populated and report file is generated. **Note**: Test written and architecture verified (tool loading + API call succeed), blocked on Anthropic API credit balance.
- [x] T034 Add rate-limit backoff handling to `src/extended_google_doc_utils/discoverability/runner.py`: catch Anthropic rate-limit errors, apply exponential backoff, log affected tests. Per edge case in spec.
- [x] T035 Run quickstart.md validation: execute the commands from quickstart.md and verify they work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — core execution engine
- **US2 (Phase 4)**: Depends on US1 — extends runner with multi-variant/trial loop
- **US3 (Phase 5)**: Depends on US2 — needs TestRun data to generate reports
- **US4 (Phase 6)**: Depends on US2 — needs TestRun data for scoring. Can run in parallel with US3.
- **US5+US6 (Phase 7)**: Depends on US3 and US4 — metadata goes in reports, CLI wires everything together
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — the MVP
- **US2 (P1)**: Depends on US1 — extends the runner
- **US3 (P1)**: Depends on US2 — generates reports from results
- **US4 (P2)**: Depends on US2 — can be built in parallel with US3
- **US5 (P2)**: Depends on US3 — adds metadata to reports
- **US6 (P2)**: Depends on US3 + US4 — CLI wires the full pipeline

### Within Each User Story

- Models → Services → Integration
- Each phase ends with a checkpoint validating that story independently

### Parallel Opportunities

- T003 and T004 can run in parallel with T001/T002
- T021 and T022 (US4 scorer) can run in parallel with T016-T020 (US3 reporter)
- T024/T025 (US5 metadata) can start once US2 runner exists
- All Phase 8 unit tests (T029-T032) can run in parallel

---

## Parallel Example: Phase 6 + Phase 5

```bash
# US4 scorer tasks can run in parallel with US3 reporter tasks
# since they operate on different files:
Task: T021 "Implement score computation in scorer.py"
Task: T016 "Implement report header and summary in reporter.py"

# Within Phase 8, all unit tests can run in parallel:
Task: T029 "Unit tests for loader"
Task: T030 "Unit tests for scorer"
Task: T031 "Unit tests for reporter"
Task: T032 "Unit tests for mock"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (models, loader, MCP bridge)
3. Complete Phase 3: US1 (single trial execution with mock mode)
4. **STOP and VALIDATE**: Run one prompt, verify tool calls captured correctly
5. This proves the core mechanism works before investing in the full pipeline

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Single trial execution works (MVP!)
3. Add US2 → Full suite with 10 trials per prompt
4. Add US3 → Desire-path reports generated
5. Add US4 → Quantitative scores computed
6. Add US5+US6 → CLI, default test suite, improvement tracking
7. Polish → Tests, rate-limit handling, validation

### Key Decision

The primary goal is to generate desire-path reports that reveal actionable improvements to MCP tool descriptions. The fastest path to that insight is: Setup → Foundational → US1 → US2 → US3. Everything after that (scoring, CLI, tracking) refines the workflow but isn't needed for the first actionable report.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All runner code is async (uses `mcp` async client + `anthropic` sync client)
- Mock mode is the default — no Google credentials needed for development
- Each trial is a fresh LLM conversation (no context carried between trials)
- The Anthropic API key is required for all modes (even mock — the LLM still needs to decide which tools to call)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
