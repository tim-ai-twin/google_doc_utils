# Feature Specification: MCP Discoverability Testing

**Feature Branch**: `002-mcp-discoverability-testing`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "Optimize MCP server discoverability by building an LLM test harness that evaluates how well LLMs discover and call the correct MCP tools, generates desire-path reports, and enables incremental improvement tracking."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Discoverability Tests Against MCP Server (Priority: P1)

A developer wants to evaluate how well an LLM can discover and correctly use the MCP server's tools for common user intents. They run the test harness, which sends natural-language prompts to an LLM connected to the MCP server and records every tool call the LLM makes—including incorrect attempts—until it either succeeds or exhausts a maximum number of attempts.

**Why this priority**: This is the core capability. Without the ability to run tests and capture tool call sequences, no other feature (reporting, scoring, improvement tracking) is possible.

**Independent Test**: Can be fully tested by running a single test prompt against the MCP server through an LLM and verifying that the harness captures the full sequence of tool calls made.

**Acceptance Scenarios**:

1. **Given** a test prompt like "Update the weekly status section in my project doc," **When** the harness runs this prompt against an LLM connected to the MCP server, **Then** the harness records every tool call the LLM attempted (tool name, parameters, success/failure) in order.
2. **Given** an LLM that selects the correct tool on its first attempt, **When** the test completes, **Then** the harness records a single tool call and marks the attempt count as 1.
3. **Given** an LLM that initially tries an incorrect tool before finding the correct one, **When** the test completes, **Then** the harness records all attempted tool calls in sequence, including the incorrect ones.
4. **Given** an LLM that fails to find the correct tool within the maximum allowed attempts, **When** the attempt limit is reached, **Then** the harness records all attempts and marks the test as failed.
5. **Given** a multi-step intent requiring a sequence of tools (e.g., get_hierarchy then export_section then import_section), **When** the test runs, **Then** the harness evaluates whether the LLM discovered and executed the correct sequence, recording each step.

---

### User Story 2 - Test Multiple Prompt Variants Per Intent (Priority: P1)

A developer wants to understand how robust tool discovery is across different phrasings of the same user intent. For each core user intent (e.g., "edit a section"), the harness runs multiple prompt variants (formal, casual, indirect, ambiguous) to measure consistency of tool selection.

**Why this priority**: A single prompt phrasing can mask discoverability issues. If the LLM succeeds with "export section by anchor ID" but fails with "show me what's under the Introduction heading," the tool descriptions need improvement. Variant testing is essential for meaningful evaluation.

**Independent Test**: Can be tested by defining 3+ prompt variants for a single intent and verifying the harness runs all of them and reports per-variant results.

**Acceptance Scenarios**:

1. **Given** 5 prompt variants for the intent "edit a specific section," **When** the harness runs all variants, **Then** results are recorded separately for each variant.
2. **Given** prompt variants ranging from explicit ("call export_section with anchor ID h.abc123") to natural ("update the Introduction in my report"), **When** results are compared, **Then** the report shows which phrasings succeeded and which failed or required extra attempts.
3. **Given** a test suite with variants for all core intents, **When** the full suite runs, **Then** each intent has an aggregate success rate across its variants.

---

### User Story 3 - Generate Desire-Path Report (Priority: P1)

After a test run completes, the developer receives a markdown report showing what the LLM tried before it successfully called the correct MCP tool for each intent. This report reveals the LLM's "desire path"—the natural tool-calling behavior the MCP server should be optimized to meet.

**Why this priority**: The report is the primary output that drives improvement decisions. Without it, the test data has no actionable form.

**Independent Test**: Can be tested by running a test suite and verifying the output .md file contains the required sections and data.

**Acceptance Scenarios**:

1. **Given** a completed test run, **When** the report is generated, **Then** it is saved as a markdown file with a timestamped filename.
2. **Given** a test where the LLM tried `normalize_formatting` before discovering `apply_document_styles` for a style transfer intent, **When** the report is generated, **Then** it shows the full attempt sequence: (1) normalize_formatting (incorrect), (2) apply_document_styles (correct).
3. **Given** a completed test run across all intents, **When** the report is generated, **Then** it includes per-intent summaries showing: intent name, prompt variant used, number of attempts, tool call sequence, and success/failure status.
4. **Given** multiple test runs over time, **When** reports are collected, **Then** each report is self-contained and can be compared to previous reports to identify trends.

---

### User Story 4 - Score MCP Server Discoverability (Priority: P2)

A developer wants quantitative metrics to track how discoverable the MCP server is. The harness computes scores including first-attempt success rate, average attempts to success, and per-intent breakdown.

**Why this priority**: Scores enable objective comparison between MCP server versions. Depends on the test execution (P1) being functional first.

**Independent Test**: Can be tested by running a test suite and verifying the computed scores match expected calculations based on the raw test data.

**Acceptance Scenarios**:

1. **Given** a test run where 8 of 10 prompt variants succeeded on the first attempt, **When** the score is computed, **Then** the first-attempt success rate is reported as 80%.
2. **Given** a test run where attempts-to-success were [1, 1, 3, 1, 2, 1, 1, FAIL, 1, 1], **When** the score is computed, **Then** the average attempts-to-success (excluding failures) is reported as 1.375 and the failure rate is 10%.
3. **Given** a test run covering 6 intents with 5 variants each, **When** scores are computed, **Then** the report includes a per-intent breakdown showing which intents are most and least discoverable.

---

### User Story 5 - Track Improvement Over Time (Priority: P2)

A developer makes changes to MCP tool descriptions, then re-runs the test suite and compares the new report against previous reports to see whether discoverability improved or regressed.

**Why this priority**: Without comparison capability, developers cannot evaluate whether their changes helped. Depends on the reporting (P1) being in place.

**Independent Test**: Can be tested by running the suite twice (with and without a tool description change) and verifying the reports show different scores.

**Acceptance Scenarios**:

1. **Given** a previous report showing 70% first-attempt success rate and a new report showing 85%, **When** the developer reviews both reports, **Then** they can identify which intents improved and which regressed.
2. **Given** multiple historical reports, **When** the developer reviews the collection, **Then** report filenames and headers include timestamps and MCP server version/commit information enabling chronological ordering.
3. **Given** a report, **When** the developer reads it, **Then** it contains enough context (tool descriptions snapshot, test prompts used) to understand what was tested and how.

---

### User Story 6 - Define Test Suite from User Intents (Priority: P2)

A developer defines the set of user intents to test, each with its expected tool call sequence and multiple prompt variants. The test definitions are stored in a structured, human-readable format that can be version-controlled alongside the MCP server code.

**Why this priority**: The test suite definition is the input to the harness. While a default suite ships with the feature, the ability to modify and extend it is important for ongoing optimization.

**Independent Test**: Can be tested by writing a test definition for a new intent and verifying the harness can load and execute it.

**Acceptance Scenarios**:

1. **Given** a test definition specifying the intent "transfer styles between documents" with expected tool sequence [get_document_styles, apply_document_styles] and 5 prompt variants, **When** loaded by the harness, **Then** the harness executes all 5 variants and validates against the expected sequence.
2. **Given** a test definition file, **When** a developer adds a new intent with new prompt variants, **Then** the harness picks up the new intent on the next run without code changes.
3. **Given** a test definition, **When** the expected tool sequence is defined, **Then** it supports both single-tool intents and multi-tool workflow intents (sequences of 2+ tool calls).

---

### Edge Cases

- What happens when the LLM produces a tool call with valid tool name but incorrect parameters? The harness classifies this as "right tool, wrong parameters" for diagnostic purposes, but treats it as a failure for scoring—same as calling the wrong tool or not calling any tool.
- What happens when the LLM refuses to call any tool (e.g., responds with text instead)? The harness records this as a "no tool call" attempt and counts it toward the attempt limit.
- What happens when the MCP server is unreachable or returns errors during testing? The harness distinguishes between LLM-side failures (wrong tool selection) and server-side failures (tool exists but server error), logging both separately.
- What happens when the LLM calls tools in a different order than expected but achieves the same result? The harness supports marking tool sequences as either order-sensitive or order-insensitive per intent definition.
- What happens when a new tool is added to the MCP server but no test covers it? The harness reports untested tools as a gap in the test suite, encouraging coverage.
- How does the system handle rate limits from the LLM provider during large test runs? The harness respects rate limits with appropriate backoff and reports which tests were affected by throttling.

## Requirements *(mandatory)*

### Functional Requirements

**Test Definition:**

- **FR-001**: System MUST support defining user intents, each with a name, description, expected tool call sequence, and multiple prompt variants
- **FR-002**: System MUST ship with a default test suite covering the core user intents of the existing MCP server (section editing, document export, formatting cleanup, style transfer, document discovery, hierarchy navigation)
- **FR-003**: Test definitions MUST be stored in a structured, human-readable format that can be version-controlled
- **FR-004**: Each prompt variant MUST be tagged with a style category (e.g., explicit, natural, indirect, ambiguous) to enable analysis by prompt style
- **FR-005**: Expected tool sequences MUST support both single-tool intents and multi-step workflow intents

**Test Execution:**

- **FR-006**: System MUST connect an LLM to the MCP server and send test prompts programmatically
- **FR-006a**: System MUST support a mock execution mode where MCP tools expose their schemas but return canned success responses without calling the Google Docs API. This is the primary mode for desire-path iteration.
- **FR-006b**: System MUST support a live execution mode where MCP tools execute against the real Google Docs API for a small set of end-to-end validation tests proving the full pipeline works
- **FR-007**: System MUST capture every tool call the LLM makes during a test (tool name, parameters provided, success/failure)
- **FR-008**: System MUST enforce a configurable maximum number of attempts per prompt before marking a test as failed
- **FR-008a**: System MUST run each prompt variant 10 times (independent trials) to account for LLM non-determinism, reporting aggregate statistics (success rate, most common first tool called, attempt distribution) across trials
- **FR-008b**: The number of trials per prompt MUST be configurable, defaulting to 10
- **FR-009**: System MUST evaluate tool call correctness by comparing against the expected tool sequence defined for each intent. Expected tools must appear in order within the LLM's call sequence; additional tool calls beyond the expected sequence are recorded for desire-path analysis but do not penalize the score.
- **FR-010**: System MUST classify each tool call as "correct" (tool name and parameters match expectations), "right tool, wrong parameters" (correct tool name but parameter errors), "wrong tool" (completely incorrect selection), or "no tool call" (LLM responded with text only). For scoring purposes, only "correct" counts as a successful step; all other classifications are failures. The classification detail exists for diagnostic reporting (understanding *what* went wrong).
- **FR-011**: System MUST support running individual intents, individual prompts, or the full test suite

**Scoring:**

- **FR-012**: System MUST compute first-attempt success rate (percentage of prompts where the LLM called the correct tool on the first try)
- **FR-013**: System MUST compute average attempts-to-success for prompts that eventually succeeded
- **FR-014**: System MUST compute per-intent success rate (across all variants for a given intent)
- **FR-015**: System MUST compute overall test suite pass rate
- **FR-016**: System MUST report failure rate (percentage of prompts where the LLM never found the correct tool)

**Reporting:**

- **FR-017**: System MUST generate a markdown report file after each test run
- **FR-018**: Reports MUST include a summary section with aggregate scores (first-attempt rate, average attempts, failure rate)
- **FR-019**: Reports MUST include a per-intent section showing each prompt variant, the tool call sequence attempted, attempt count, and success/failure
- **FR-020**: Reports MUST include the "desire path" for failed or multi-attempt cases: what the LLM tried first and why it may have chosen incorrectly
- **FR-021**: Reports MUST include a snapshot of the MCP server version (git commit hash) and the tool descriptions that were active during the test
- **FR-022**: Reports MUST be saved with timestamped filenames in a designated reports directory
- **FR-023**: Reports MUST be self-contained markdown files that can be read and compared without the test harness

**Improvement Tracking:**

- **FR-024**: Each report MUST contain sufficient metadata (timestamp, commit hash, tool description snapshot) to enable chronological comparison
- **FR-025**: System MUST flag untested tools—MCP tools that have no test coverage in the current test suite

### Key Entities

- **UserIntent**: A named user goal with an expected tool call sequence. Represents what a user wants to accomplish (e.g., "edit a section," "transfer styles"). Contains prompt variants and expected tool calls.
- **PromptVariant**: A specific phrasing of a user intent, tagged with a style category (explicit, natural, indirect, ambiguous). Multiple variants exist per intent.
- **TestRun**: A single execution of the test suite (or subset). Contains timestamp, MCP server version, and results for all executed prompts.
- **AttemptRecord**: A single tool call made by the LLM during a test. Contains tool name, parameters, correctness classification (wrong tool / right tool wrong params / correct), and sequence position.
- **DesirePathReport**: The markdown output file from a test run. Contains scores, per-intent results, tool call sequences, and metadata for comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The default test suite covers all core user intents of the existing MCP server (minimum 6 intents with 3+ prompt variants each)
- **SC-002**: The test harness can execute the full default test suite and produce a report in a single command
- **SC-003**: Reports clearly identify which intents have the lowest discoverability scores, enabling targeted improvement
- **SC-004**: After making an improvement to MCP tool descriptions, re-running the suite and comparing reports shows measurable change in scores (positive or negative)
- **SC-005**: The desire-path data in reports identifies at least one actionable improvement to MCP tool descriptions in the baseline run (proving the tool produces useful insights)
- **SC-006**: Test definitions can be extended with new intents or prompt variants without modifying harness code

## Clarifications

### Session 2026-02-13

- Q: Should the harness test against a live MCP server or mock? → A: Mock mode is the primary mode for desire-path iteration (no Google credentials needed, fast/cheap). Live e2e mode is also needed for a small set of complete tests to prove the whole system works end-to-end.
- Q: Should each prompt be run multiple times for statistical reliability? → A: Yes, 10 independent trials per prompt (configurable). Report aggregate statistics across trials.
- Q: For multi-step intents, should extra tool calls beyond the expected sequence count as failures? → A: No. Expected tools must appear in order (subset match), but extra tools are recorded for desire-path analysis without penalizing the score.

## Assumptions

- An LLM with tool-calling capabilities is available for testing (e.g., Claude via Anthropic API)
- The existing MCP server (feature 127) is functional and can be connected to by the test harness
- API costs for running LLM-based tests are acceptable for the development workflow
- The MCP server's tool list and descriptions are accessible programmatically (standard MCP protocol)
- Test results may vary between runs due to LLM non-determinism; the harness accounts for this by running 10 independent trials per prompt (configurable)

## Dependencies

- Feature 127 (Google Docs MCP Server) must be functional
- Feature 130 (Document Style Transfer) for complete tool coverage
- LLM API access (Anthropic API or equivalent) for test execution
- MCP client library for programmatic server connection

## Out of Scope

- Automatically modifying MCP tool descriptions (the harness identifies problems; humans decide fixes)
- Testing non-tool MCP features (resources, prompts)
- Performance benchmarking of MCP server response times (this feature focuses on discoverability, not speed)
- Testing with multiple LLM providers simultaneously (single LLM per test run)
- Synthetic prompt generation (prompt variants are manually authored for quality)
- A/B testing of tool description variants in a single run (run the suite once per variant, compare reports)
