# Implementation Plan: Google Docs to Markdown Converter

**Branch**: `126-gdoc-markdown-converter` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/126-gdoc-markdown-converter/spec.md`

## Summary

Implement bidirectional conversion between Google Docs native format and MEBDF (Markdown Extensions for Basic Doc Formatting) v1.4. The converter operates at the tab level, supports section-level operations via heading anchors, and preserves embedded objects through opaque placeholders. Key capabilities: hierarchy view for navigation, full-tab export/import, section-level export/import, and round-trip safety for formatting and anchors.

## Technical Context

**Language/Version**: Python 3.11+ (existing project requirement)
**Primary Dependencies**: google-api-python-client (existing), new: regex/re for MEBDF parsing
**Storage**: N/A (stateless conversion, no persistence)
**Testing**: pytest with tier_a/tier_b markers (existing pattern)
**Target Platform**: Library/package, consumed by MCP server
**Project Type**: Single project extending existing `extended_google_doc_utils` package
**Performance Goals**: 50 pages in 30s (SC-004), hierarchy in 2s (SC-005), sections in 5s (SC-006)
**Constraints**: Must maintain round-trip fidelity for all supported formatting
**Scale/Scope**: Documents up to 50 pages, sections up to 10 pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with Extended Google Doc Utils Constitution v1.0.0:

- [x] **I. LLM-Friendly Format Design**: MEBDF v1.4 uses minimal `{! }` and `{^ }` syntax families, consistent and unambiguous
- [x] **II. Round-Trip Safety**: Core requirement - all formatting/anchors preserved through cycles (SC-003, SC-007)
- [x] **III. Minimal Verbosity**: Content-first design, stateful block formatting, single-token anchors
- [x] **IV. Backward Compatibility**: MEBDF v1.4 is additive (new `{^= id type}` syntax), no breaking changes
- [x] **V. Specification-Driven Development**: Full spec complete with acceptance scenarios before implementation

**Testing Standards**:
- [x] Contract tests planned for MEBDF syntax parsing (parser validation)
- [x] Round-trip tests planned for semantic preservation (US6 acceptance scenarios)
- [x] LLM integration tests planned (MEBDF designed for LLM consumption)
- [x] Edge case coverage identified (spec Edge Cases section)

## Project Structure

### Documentation (this feature)

```text
specs/126-gdoc-markdown-converter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/extended_google_doc_utils/
├── converter/                    # NEW: Conversion module
│   ├── __init__.py
│   ├── gdoc_to_mebdf.py         # Google Docs → MEBDF export
│   ├── mebdf_to_gdoc.py         # MEBDF → Google Docs import
│   ├── mebdf_parser.py          # MEBDF syntax parser
│   ├── hierarchy.py             # Tab hierarchy extraction
│   └── section_utils.py         # Section boundary detection
├── google_api/
│   └── docs_client.py           # EXISTING: Extend with tab/anchor methods
├── auth/                         # EXISTING: No changes needed
└── utils/                        # EXISTING: No changes needed

tests/
├── tier_a/                       # Tests with mocked Google API
│   ├── test_mebdf_parser.py     # NEW: Parser unit tests
│   ├── test_gdoc_to_mebdf.py    # NEW: Export logic tests
│   ├── test_mebdf_to_gdoc.py    # NEW: Import logic tests
│   └── test_round_trip.py       # NEW: Round-trip preservation tests
├── tier_b/                       # Tests with real API (credentials required)
│   └── test_converter_e2e.py    # NEW: End-to-end with real docs
├── fixtures/
│   └── mebdf_samples/           # NEW: Sample MEBDF documents
└── conftest.py                   # Existing
```

**Structure Decision**: Extend existing `extended_google_doc_utils` package with new `converter/` module. Follows existing patterns (google_api/, auth/, utils/). No new top-level packages needed.

## Complexity Tracking

No constitution violations requiring justification. Design follows established patterns.
