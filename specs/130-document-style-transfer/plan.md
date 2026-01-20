# Implementation Plan: Document Style Transfer

**Branch**: `130-document-style-transfer` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/130-document-style-transfer/spec.md`

## Summary

Enable reading and writing document-level properties (background, margins, page size) and effective/visible styles for all 9 named style types (NORMAL_TEXT, TITLE, SUBTITLE, HEADING_1-6). The system captures what users actually see—if paragraphs have inline overrides, those are returned as the effective style. Styles are transferred by applying formatting inline to each paragraph (flattening), since the Google Docs API does not support updating named style definitions. Feature exposed via Python API and MCP server with round-trip test coverage.

**Multi-Tab Support**: All style transfer tools support a `tab_id` parameter for multi-tab documents, consistent with all other MCP tools in the system. When `tab_id` is empty/omitted, the first/default tab is used. Document properties (background color, margins, page size) are read from the tab-level `documentStyle` to correctly handle multi-tab documents where each tab can have different page settings.

## Technical Context

**Language/Version**: Python 3.11+ (existing project requirement)
**Primary Dependencies**: google-api-python-client (existing), mcp>=1.25.0 (existing), dataclasses (stdlib)
**Storage**: N/A (stateless—reads from and writes to Google Docs API)
**Testing**: pytest with tier system (tier_a: unit/no credentials, tier_b: integration/requires credentials)
**Target Platform**: Linux/macOS CLI, MCP server for LLM integration
**Project Type**: Single project (src/extended_google_doc_utils)
**Performance Goals**: Read styles <5s, apply styles to 100+ paragraphs <30s (per spec SC-001, SC-002)
**Constraints**: Google Docs API rate limits, no UpdateNamedStyles API (read-only for definitions)
**Scale/Scope**: Documents up to 1000 paragraphs per assumptions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with Extended Google Doc Utils Constitution v1.0.0:

- [x] **I. LLM-Friendly Format Design**: Style data returned as structured JSON for MCP tools; clear property names matching Google Docs terminology
- [x] **II. Round-Trip Safety**: Effective styles capture complete formatting; round-trip tests verify 100% fidelity (SC-003)
- [x] **III. Minimal Verbosity**: API returns only relevant style properties; no verbose wrappers
- [x] **IV. Backward Compatibility**: New feature—no existing syntax to break; adds new API functions and MCP tools
- [x] **V. Specification-Driven Development**: Full spec with 30 functional requirements, acceptance scenarios, edge cases

**Testing Standards**:
- [x] Contract tests planned for style extraction logic
- [x] Round-trip tests planned for semantic preservation (User Story 5)
- [x] LLM integration tests planned via MCP tool testing (User Story 4)
- [x] Edge case coverage identified (8 edge cases in spec)

## Project Structure

### Documentation (this feature)

```text
specs/130-document-style-transfer/
├── plan.md              # This file
├── research.md          # Phase 0 output - API patterns, style flattening strategy
├── data-model.md        # Phase 1 output - DocumentStyles, EffectiveStyle entities
├── quickstart.md        # Phase 1 output - Usage examples
├── contracts/           # Phase 1 output - Python API signatures
│   └── api.md           # Function signatures and return types
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/extended_google_doc_utils/
├── converter/
│   ├── types.py              # Add DocumentStyles, EffectiveStyle, StyleTransferOptions
│   ├── style_reader.py       # NEW: Read document styles and effective paragraph styles
│   └── style_writer.py       # NEW: Apply styles to target document
├── mcp/
│   └── tools/
│       └── styles.py         # NEW: MCP tools for style operations

tests/
├── tier_a/
│   ├── test_style_reader.py  # NEW: Unit tests for style extraction (mocked)
│   └── test_style_writer.py  # NEW: Unit tests for style application (mocked)
└── tier_b/
    └── test_style_transfer.py # NEW: Integration + round-trip tests
```

**Structure Decision**: Single project structure matches existing codebase. New modules follow established patterns:
- Reader/writer separation mirrors `gdoc_to_mebdf.py`/`mebdf_to_gdoc.py` pattern
- New MCP tools added to `tools/` directory following `formatting.py` pattern
- Test tiers follow existing `tier_a`/`tier_b` organization

## Complexity Tracking

No constitution violations requiring justification. Design uses existing patterns and stays within project conventions.
