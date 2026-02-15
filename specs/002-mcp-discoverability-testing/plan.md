# Implementation Plan: MCP Discoverability Testing

**Branch**: `002-mcp-discoverability-testing` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-mcp-discoverability-testing/spec.md`

## Summary

Build a Python test harness that evaluates how well LLMs discover and correctly call the existing MCP server's tools. The harness sends natural-language prompts to Claude via the Anthropic SDK, with MCP tool definitions available, captures every tool call the LLM makes (including incorrect attempts), runs 10 independent trials per prompt for statistical reliability, and generates markdown "desire-path" reports showing what the LLM tried first. This enables iterative improvement of MCP tool descriptions by revealing the gap between what the LLM naturally reaches for and what the tools are named/described as.

**Key technical approach**: Custom Python harness using `mcp` (client) + `anthropic` SDK with a manual agentic loop. L-Qun/mcp-testing-framework was evaluated and rejected (TypeScript, single-turn XML, no desire-path capture, dormant). See [research.md](research.md) for full analysis.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing project)
**Primary Dependencies**: `mcp>=1.25.0` (existing), `anthropic>=0.40.0` (new, test harness only), `pyyaml` (test definitions)
**Storage**: Filesystem — YAML test definitions, markdown reports
**Testing**: pytest (existing project test framework)
**Target Platform**: macOS/Linux (developer workstation)
**Project Type**: Single project (extends existing src/ structure)
**Performance Goals**: Full test suite (6 intents × 5 variants × 10 trials = 300 LLM calls) completes within LLM API latency constraints (no local performance target)
**Constraints**: Anthropic API rate limits; API cost proportional to trial count
**Scale/Scope**: 12 MCP tools, 6 intents, ~30 prompt variants, developer-only usage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with Extended Google Doc Utils Constitution v1.0.0:

- [x] **I. LLM-Friendly Format Design**: N/A — this feature does not define new syntax or markup. It tests existing MCP tool descriptions.
- [x] **II. Round-Trip Safety**: N/A — this feature does not process document content. Test definitions (YAML) and reports (markdown) are write-once artifacts.
- [x] **III. Minimal Verbosity**: YAML test definitions are minimal. Reports are structured markdown with no unnecessary markup.
- [x] **IV. Backward Compatibility**: N/A — new feature, no existing data to migrate. Does not modify existing MCP server code.
- [x] **V. Specification-Driven Development**: Feature fully specified in spec.md with clarifications resolved before implementation.

**Testing Standards**:
- [x] Contract tests planned for YAML test definition parsing and validation
- [x] Round-trip tests planned: N/A (no document round-trip in this feature)
- [x] LLM integration tests planned — the entire feature IS an LLM integration test harness
- [x] Edge case coverage identified — wrong tool, right tool wrong params, no tool call, server errors, rate limits

## Project Structure

### Documentation (this feature)

```text
specs/002-mcp-discoverability-testing/
├── plan.md              # This file
├── research.md          # Phase 0: framework evaluation, architecture decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: usage guide
├── contracts/           # Phase 1: API contracts
│   └── api.md           # Python module interfaces, CLI, YAML format, report structure
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/extended_google_doc_utils/
├── mcp/                          # Existing MCP server (feature 127)
│   ├── server.py
│   └── tools/
│       ├── navigation.py
│       ├── sections.py
│       ├── tabs.py
│       ├── formatting.py
│       └── styles.py
└── discoverability/              # NEW: Test harness (this feature)
    ├── __init__.py
    ├── __main__.py               # CLI entry point
    ├── models.py                 # Dataclasses (TestSuite, TestRun, etc.)
    ├── loader.py                 # YAML test definition loading & validation
    ├── runner.py                 # Test execution engine (MCP client + Anthropic SDK loop)
    ├── mock.py                   # Mock MCP tool responses for mock mode
    ├── scorer.py                 # Score computation from test results
    ├── reporter.py               # Markdown report generation
    └── test_suites/              # Default test definitions
        └── default.yaml          # 6 intents × 5 variants

tests/
├── unit/
│   ├── test_loader.py            # YAML parsing, validation
│   ├── test_scorer.py            # Score computation from known data
│   ├── test_reporter.py          # Report generation from known data
│   └── test_mock.py              # Mock response generation
├── integration/
│   └── test_harness_e2e.py       # Full harness run with mock mode (requires API key)
└── reports/                      # Generated reports (gitignored)

reports/                          # Top-level report output directory (gitignored)
```

**Structure Decision**: Extends the existing single-project `src/extended_google_doc_utils/` structure with a new `discoverability/` subpackage. Follows the same pattern as the existing `mcp/` subpackage. Test suites are bundled within the package for discoverability, reports output to a top-level `reports/` directory.
