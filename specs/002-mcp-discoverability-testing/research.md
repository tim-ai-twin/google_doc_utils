# Research: MCP Discoverability Testing

**Feature**: 002-mcp-discoverability-testing
**Date**: 2026-02-13

## Decision 1: L-Qun/mcp-testing-framework vs Custom Build

**Decision**: Build a custom Python test harness from scratch.

**Rationale**: L-Qun/mcp-testing-framework is not suitable for this use case:
- **TypeScript only** — this is a Python project
- **Single-turn XML-based evaluation** — the LLM is asked to output XML selecting one tool per prompt. It does not use native tool-calling APIs and cannot capture multi-turn tool call sequences
- **No desire-path capture** — there is no concept of "what the LLM tried first" because each trial is a single request-response with no retry or agentic loop
- **No multi-step workflow support** — cannot evaluate sequences like get_hierarchy → export_section → import_section
- **Dormant** — 28 stars, last commit April 2025, single contributor, no community

**Alternatives considered**:
- **DeepEval MCPUseMetric** — Python, has precision/recall metrics, but focused on correctness scoring rather than desire-path capture. Could complement but not replace a custom harness.
- **MCP Inspector** — debugging tool, not an evaluation harness. Useful for ad-hoc testing but not automated test suites.
- **Claude Agent SDK** — too heavy (spawns Claude Code CLI process). The lightweight `mcp` + `anthropic` SDK combination provides equivalent tool-call capture with less overhead.

## Decision 2: LLM-to-MCP Connection Architecture

**Decision**: Use `mcp` Python package (client) + `anthropic` Python SDK with a manual agentic loop.

**Rationale**: This is the lightest-weight approach that gives full control over tool call capture:
1. `mcp.client.stdio.stdio_client` starts the MCP server as a subprocess and connects via stdio
2. `session.list_tools()` discovers all tool definitions
3. Tool definitions are converted to Anthropic tool format and passed to `client.messages.create()`
4. A manual while-loop handles `stop_reason == "tool_use"`, capturing every `tool_use` block
5. In mock mode, tool calls return canned success responses instead of calling `session.call_tool()`

**Alternatives considered**:
- **claude-agent-sdk** — wraps Claude Code CLI, much heavier. Hooks (PreToolUse/PostToolUse) are nice but not worth the dependency for this use case.
- **mcp-use (LangChain)** — adds LangChain dependency, less control over tool call capture.
- **anthropic beta tool_runner** — automates the loop but tools must be Python functions, not direct MCP session calls. Less control over capture.

**Dependencies**:
- `mcp>=1.25.0` (already in project)
- `anthropic>=0.40.0` (new dependency for test harness only)

## Decision 3: Mock vs Live Execution Mode

**Decision**: Two modes — mock (primary) and live (secondary).

**Rationale** (from clarification session):
- **Mock mode**: MCP server starts normally but tool calls return canned success responses. The LLM sees real tool definitions and makes real tool selections, but no Google Docs API calls are made. This is fast, cheap, and needs no credentials. Primary mode for desire-path iteration.
- **Live mode**: MCP server executes tools against real Google Docs API. Used for a small set of end-to-end validation tests. Requires Google OAuth credentials and test documents.

**Implementation**: Mock mode intercepts at the `session.call_tool()` level, returning pre-defined successful responses per tool. The LLM's tool selection behavior is identical in both modes since it only sees tool schemas.

## Decision 4: Test Definition Format

**Decision**: YAML files in a `test_suites/` directory.

**Rationale**: YAML is human-readable, version-controllable, and already familiar from the L-Qun framework's approach (even though we're not using that framework). Each file defines one or more intents with their prompt variants and expected tool sequences.

**Alternatives considered**:
- **Python test files (pytest)** — too coupled to test framework; non-developers can't easily add prompts
- **JSON** — less readable for multi-line prompt strings
- **TOML** — less natural for nested structures like tool sequences

## Decision 5: Statistical Trials

**Decision**: 10 independent trials per prompt variant (configurable).

**Rationale** (from clarification session): LLM behavior is non-deterministic. Running each prompt 10 times provides statistical reliability for metrics like first-attempt success rate. Each trial is a fresh conversation (no context carried between trials).

## Decision 6: Report Format

**Decision**: Self-contained markdown files with timestamped filenames.

**Rationale**: Markdown is human-readable, version-controllable, and can be reviewed in any text editor or rendered in GitHub. Each report includes:
- Aggregate scores
- Per-intent breakdown with desire-path analysis
- Tool description snapshot (for reproducibility)
- Git commit hash

Filename pattern: `reports/desire-path-YYYY-MM-DD-HHMMSS.md`

## Existing MCP Server Tools (12 tools)

For reference, these are the tools the test suite must cover:

| Module | Tool | Description |
|--------|------|-------------|
| Navigation | `list_documents` | Discover accessible Google Docs by name |
| Navigation | `get_metadata` | Get document info including tabs |
| Navigation | `get_hierarchy` | Extract heading structure with anchor IDs |
| Sections | `export_section` | Read a specific section by anchor ID |
| Sections | `import_section` | Replace a section's content (safe edit) |
| Tabs | `export_tab` | Read entire tab content |
| Tabs | `import_tab` | Replace entire tab content (destructive) |
| Formatting | `normalize_formatting` | Apply consistent formatting |
| Formatting | `extract_styles` | Extract formatting patterns from source doc |
| Formatting | `apply_styles` | Apply extracted styles to target doc |
| Styles | `get_document_styles` | Get document properties + effective styles |
| Styles | `apply_document_styles` | Transfer styles between documents |

## Default Test Suite: Core User Intents

Based on the MCP server's user stories (spec 127, 130), these are the 6 core intents:

1. **Edit a specific section** — get_hierarchy → export_section → import_section
2. **Read a document** — list_documents → export_tab (or get_hierarchy → export_section)
3. **Clean up formatting** — normalize_formatting
4. **Transfer styles between documents** — get_document_styles → apply_document_styles (or extract_styles → apply_styles)
5. **Find a document** — list_documents
6. **Understand document structure** — get_hierarchy (or get_metadata)
