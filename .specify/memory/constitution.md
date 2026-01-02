<!--
Sync Impact Report:
- Version: None → 1.0.0 (MAJOR: Initial constitution creation)
- Principles established:
  1. LLM-Friendly Format Design (NEW)
  2. Round-Trip Safety (NEW)
  3. Minimal Verbosity (NEW)
  4. Backward Compatibility (NEW)
  5. Specification-Driven Development (NEW)
- Templates status:
  ✅ plan-template.md - Updated with constitution v1.0.0 compliance checklist
  ✅ spec-template.md - Reviewed, requirements sections compatible
  ✅ tasks-template.md - Reviewed, task organization compatible
  ✅ All commands/*.md - Reviewed, no agent-specific references found
- Follow-up: None required
-->

# Extended Google Doc Utils Constitution

## Core Principles

### I. LLM-Friendly Format Design

All markdown extensions MUST be designed for optimal LLM readability and generation. This means:
- Extensions use minimal, consistent syntax families (e.g., `{! }` for all formatting)
- Syntax is unambiguous and parseable without deep context
- Property names match common GUI terminology (Google Docs interface) for intuitive understanding
- Boolean properties default to sensible values (no value = true)
- Spacing flexibility allows natural variation (`{!mono}` and `{! mono }` are equivalent)

**Rationale**: LLMs are primary consumers and producers of these documents. Optimizing for LLM comprehension ensures reliable round-trip editing, reduces hallucination risk, and enables effective document transformation workflows.

### II. Round-Trip Safety

All document features MUST survive read-edit-write cycles without data loss. This includes:
- Formatting properties (inline and block-level)
- Anchor positions and IDs
- Document structure and hierarchy
- Semantic intent of markup

**Rationale**: Documents are living artifacts edited by both humans and LLMs over time. Loss of formatting or structural information during edits breaks workflows and erodes trust in the system.

### III. Minimal Verbosity

Extensions MUST NOT obscure content. Content-first design principles:
- Inline formatting wraps only what needs formatting
- Block formatting is stateful (format once, applies until changed)
- No repetitive annotations for continuous formatting
- Anchors are single tokens at their logical positions
- No verbose XML-style syntax or nested structures

**Rationale**: Markdown's success comes from readability. Extensions that clutter the text defeat the purpose and make documents harder for both humans and LLMs to work with.

### IV. Backward Compatibility

Changes to extension syntax or semantics MUST maintain backward compatibility or provide clear migration paths:
- Existing documents must parse correctly after specification updates
- New features use distinct syntax to avoid ambiguity with existing documents
- Breaking changes require MAJOR version bumps and documented migration procedures
- Deprecated syntax continues to parse for at least one MAJOR version

**Rationale**: Document corpora accumulate over time. Breaking changes create technical debt and force coordinated updates across multiple systems (editors, renderers, validators).

### V. Specification-Driven Development

All features MUST be fully specified before implementation:
- Syntax defined with formal grammar or unambiguous examples
- Behavior specified for normal and edge cases
- Round-trip examples demonstrating preservation guarantees
- LLM readability validated with example prompts and expected outputs

**Rationale**: Markdown extensions live at the intersection of human editing, LLM generation, and machine parsing. Ambiguity in specifications leads to divergent implementations, interoperability failures, and unpredictable LLM behavior.

## Implementation Standards

### Testing Requirements

All extension implementations MUST include:
- **Contract Tests**: Verify syntax parsing matches specification examples exactly
- **Round-Trip Tests**: Ensure parse-serialize cycles preserve document semantics
- **LLM Integration Tests**: Validate that LLMs can read and generate valid syntax
- **Edge Case Tests**: Cover boundary conditions (empty values, Unicode, nesting limits, etc.)

### Documentation Standards

Each extension MUST provide:
- **Syntax Summary Table**: Quick reference for all valid patterns
- **GUI Terminology Mapping**: Connect properties to familiar interface concepts
- **LLM Usage Examples**: Demonstrate how LLMs should generate and modify the syntax
- **Design Principles Section**: Explain the "why" behind syntax choices

### Version Control

Extensions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking syntax changes, incompatible parsing rules
- **MINOR**: New properties, new extension types (backward compatible)
- **PATCH**: Documentation clarifications, example additions, non-semantic fixes

## Governance

### Amendment Procedure

1. Propose change with rationale and compatibility analysis
2. Document impact on existing specifications and implementations
3. Obtain approval from project maintainers
4. Update constitution and increment version appropriately
5. Propagate changes to dependent templates (plan, spec, tasks)
6. Commit with clear change summary

### Compliance Review

All pull requests and design documents MUST verify:
- New extensions align with Core Principles I-V
- Syntax is LLM-friendly (validated with examples)
- Round-trip safety demonstrated with tests
- Backward compatibility maintained or migration path documented
- Specification written before implementation (no code-first features)

### Complexity Justification

Violations of simplicity (Principle III) or additions that increase cognitive load MUST be justified by documenting:
- What problem requires the complexity
- Why simpler alternatives were insufficient
- What trade-offs were accepted

**Version**: 1.0.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-02
