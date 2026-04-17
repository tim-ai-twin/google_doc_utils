# Implementation Plan: Large Document Editing

**Branch**: `132-large-doc-editing` | **Date**: 2026-03-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/132-large-doc-editing/spec.md`

## Summary

Add support for efficiently editing large Google Docs (50+ pages, multiple tabs) by:
1. Enhancing `get_hierarchy` with per-section word/character counts so the LLM can judge document size
2. Adding a `format="plain"` option to `read_tab` for cleaner disk-based search (strips MEBDF markers)
3. Creating a Claude Code skill that orchestrates the optimal workflow: discover → measure → export to disk → search → targeted edit

The MCP server remains a pure data-access layer. All filesystem operations (temp files, cleanup) are handled by the skill.

## Technical Context

**Language/Version**: Python 3.11+ (existing project requirement)
**Primary Dependencies**: google-api-python-client (existing), mcp>=1.25.0 (existing), FastMCP (existing)
**Storage**: N/A (stateless — reads from Google Docs API, temp files managed by skill)
**Testing**: pytest, Tier A (mocked, no credentials), Tier B (E2E, credentials required)
**Target Platform**: macOS / Linux (Claude Code CLI)
**Project Type**: Single Python package
**Performance Goals**: Section size computation adds <100ms to hierarchy call
**Constraints**: MCP server must not write to filesystem; backward compatibility required for all existing tools
**Scale/Scope**: Documents up to 50+ pages, 50+ tabs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with Extended Google Doc Utils Constitution v1.0.0:

- [x] **I. LLM-Friendly Format Design**: Plain markdown output optimizes for LLM content scanning. Hierarchy word counts give LLMs sizing context for budget decisions.
- [x] **II. Round-Trip Safety**: No changes to MEBDF read/write path. Plain markdown is read-only (for search, not editing). Section editing still uses MEBDF.
- [x] **III. Minimal Verbosity**: Plain markdown strips all MEBDF markers. Word count hints in hierarchy markdown are minimal (`(N words)`).
- [x] **IV. Backward Compatibility**: `format` defaults to `"mebdf"`. Hierarchy adds new optional fields. No existing behavior changes.
- [x] **V. Specification-Driven Development**: Full spec, research, data model, and contracts completed before implementation.

**Testing Standards**:
- [x] Contract tests planned for plain markdown serializer output
- [x] Round-trip tests planned: MEBDF read → edit → write preserves content (existing, unchanged)
- [x] LLM integration tests planned via discoverability harness (skill workflow)
- [x] Edge case coverage identified: empty docs, no headings, images, large sections

## Project Structure

### Documentation (this feature)

```text
specs/132-large-doc-editing/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research
├── data-model.md        # Data model changes
├── quickstart.md        # Implementation quickstart
├── contracts/
│   ├── mcp-tools.md     # MCP tool API contracts
│   └── skill-workflow.md # Skill orchestration contract
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/extended_google_doc_utils/
├── converter/
│   ├── types.py                  # MODIFY: Add word_count/char_count fields
│   ├── hierarchy.py              # MODIFY: Compute section sizes
│   ├── converter.py              # MODIFY: Add format param to read_tab
│   └── plain_serializer.py       # NEW: PlainMarkdownSerializer
├── mcp/
│   ├── schemas.py                # MODIFY: Add fields to response dataclasses
│   └── tools/
│       ├── navigation.py         # MODIFY: Wire up hierarchy size fields
│       └── tabs.py               # MODIFY: Add format param to read_tab tool

.claude/skills/
└── edit-google-doc.md            # NEW: Claude Code skill definition

tests/
├── tier_a/
│   ├── test_plain_serializer.py  # NEW: Plain markdown output
│   └── test_hierarchy_sizes.py   # NEW: Section size calculation
└── mcp/
    └── test_read_tab_format.py   # NEW: Format parameter
```

**Structure Decision**: Follows existing single-package layout. New serializer goes alongside existing `mebdf_serializer.py`. Skill file goes in Claude Code's standard `.claude/skills/` directory.
