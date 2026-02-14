# API Contracts: MCP Discoverability Testing

**Feature**: 002-mcp-discoverability-testing
**Date**: 2026-02-13

This is a CLI/library tool, not a web service. Contracts are defined as Python module interfaces.

## Test Suite Loading

### `load_test_suite(path: str) -> TestSuite`

Load a test suite from a YAML file or directory of YAML files.

**Input**: Path to YAML file or directory
**Output**: TestSuite dataclass
**Errors**: FileNotFoundError, ValidationError (invalid YAML structure)

## Test Execution

### `run_test_suite(suite: TestSuite, config: RunConfig) -> TestRun`

Execute all intents and prompt variants in a test suite.

**Input**:
- `suite`: TestSuite to execute
- `config`: RunConfig with fields:
  - `model: str` — LLM model ID (default: "claude-sonnet-4-20250514")
  - `mode: Literal["mock", "live"]` — execution mode (default: "mock")
  - `trials: int` — trials per prompt (default: 10)
  - `max_attempts: int` — max tool calls per trial (default: 10)
  - `mcp_server_command: list[str]` — command to start MCP server
  - `credentials_path: str | None` — OAuth credentials (live mode only)

**Output**: TestRun dataclass with all results
**Errors**: ConnectionError (MCP server), AuthenticationError (Anthropic API)

### `run_intent(intent: UserIntent, config: RunConfig) -> IntentResult`

Execute a single intent (all its prompt variants).

### `run_prompt(prompt: PromptVariant, expected_tools: list[str], config: RunConfig) -> VariantResult`

Execute a single prompt variant across N trials.

## Scoring

### `compute_scores(run: TestRun) -> dict`

Compute aggregate scores from a test run.

**Output**:
```python
{
    "first_attempt_rate": 0.85,       # % of trials with correct first call
    "overall_success_rate": 0.92,     # % of trials that succeeded
    "failure_rate": 0.08,             # % of trials that never succeeded
    "avg_attempts_to_success": 1.3,   # mean attempts (excluding failures)
    "per_intent": {
        "edit-section": {"first_attempt_rate": 0.9, "success_rate": 0.95, ...},
        "transfer-styles": {"first_attempt_rate": 0.7, "success_rate": 0.85, ...},
        ...
    },
    "untested_tools": ["import_tab"]  # MCP tools with no test coverage
}
```

## Reporting

### `generate_report(run: TestRun, output_dir: str) -> str`

Generate a markdown desire-path report.

**Input**: TestRun with results, output directory path
**Output**: Path to generated report file
**Side effect**: Writes `desire-path-YYYY-MM-DD-HHMMSS.md` to output_dir

### Report Structure

```markdown
# MCP Discoverability Report

**Date**: YYYY-MM-DD HH:MM:SS
**Model**: claude-sonnet-4-20250514
**Mode**: mock
**Commit**: abc1234
**Trials per prompt**: 10

## Summary

| Metric | Value |
|--------|-------|
| First-attempt success rate | 85% |
| Overall success rate | 92% |
| Failure rate | 8% |
| Avg attempts to success | 1.3 |

## Per-Intent Results

### Intent: Edit a Specific Section
**Expected tools**: get_hierarchy → export_section → import_section
**Overall first-attempt rate**: 90% | **Success rate**: 95%

#### Variant: "Update the Introduction section in my report" (natural)
- First-attempt rate: 80% (8/10 trials)
- Most common first tool: `get_hierarchy` (9/10)
- Desire path: get_hierarchy → export_section → import_section

#### Variant: "I need to change some text under a heading" (indirect)
- First-attempt rate: 60% (6/10 trials)
- Most common first tool: `export_tab` (4/10) ← **DESIRE PATH MISMATCH**
- Desire path: export_tab (4), get_hierarchy (6) → export_section → import_section

[... more variants ...]

### Intent: Transfer Styles Between Documents
[... same structure ...]

## Desire Path Analysis

### Tools the LLM reaches for first (across all intents)
| Tool | Times called first | Expected first | Mismatch rate |
|------|-------------------|----------------|---------------|
| get_hierarchy | 45 | 30 | 0% |
| export_tab | 12 | 0 | 100% |
| list_documents | 8 | 5 | 37.5% |

### Recommendations
- `export_tab` is frequently called when `export_section` is expected. Consider adding guidance in export_section description about when to use it vs export_tab.
- [... more recommendations based on data ...]

## Tool Description Snapshot
[Full tool name + description for each of the 11 tools, frozen at test time]

## Untested Tools
- `import_tab` — no test intent covers this tool
```

## CLI Interface

### `python -m extended_google_doc_utils.discoverability run`

Run the full default test suite.

**Flags**:
- `--suite PATH` — path to test suite YAML (default: built-in suite)
- `--model MODEL` — LLM model ID
- `--mode mock|live` — execution mode (default: mock)
- `--trials N` — trials per prompt (default: 10)
- `--max-attempts N` — max tool calls per trial (default: 10)
- `--intent NAME` — run only one intent
- `--output-dir PATH` — report output directory (default: `reports/`)

**Output**: Prints summary scores to stdout, writes full report to file.

### `python -m extended_google_doc_utils.discoverability list`

List all intents and prompt variants in the test suite.

## YAML Test Definition Format

```yaml
# test_suites/default.yaml
suite:
  name: default
  defaults:
    trials: 10
    max_attempts: 10

intents:
  - name: edit-section
    description: "Edit a specific section of a document by heading"
    expected_tools:
      - get_hierarchy
      - export_section
      - import_section
    order_sensitive: true
    variants:
      - text: "Update the weekly status section in my project doc"
        style: natural
      - text: "I need to change the Introduction heading content"
        style: natural
      - text: "Edit the part under 'Budget Analysis'"
        style: indirect
      - text: "Can you modify a section of my Google Doc?"
        style: ambiguous
      - text: "Export the section with anchor ID h.abc123, modify it, then import it back"
        style: explicit

  - name: transfer-styles
    description: "Apply formatting styles from one document to another"
    expected_tools:
      - apply_document_styles
    order_sensitive: false
    variants:
      - text: "Make this document look like my company template"
        style: natural
      - text: "Apply the styles from document A to document B"
        style: natural
      - text: "Copy the formatting between two documents"
        style: indirect
      - text: "The fonts and heading styles should match the other doc"
        style: ambiguous
      - text: "Transfer document-level properties and named styles from source to target"
        style: explicit
```
