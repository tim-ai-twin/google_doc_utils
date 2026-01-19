# Feature Specification: Google Docs Font Validation

**Feature Branch**: `128-gdoc-font-validation`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Fix the fonts. The LLM should know what fonts and weights are available in a default Google Doc. The MCP should expose a reasonable interface to the LLM so that it can write the correct fonts. If the LLM writes a font that doesn't exist the MCP server should either correct it or return an error and not silently set an incorrect font. We only need to worry about fonts in the default Google Doc (we don't need to extend fonts beyond the default)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - LLM Knows Available Fonts from Documentation (Priority: P1)

An LLM uses the MCP server to write content to a Google Doc. The tool descriptions include the complete list of available fonts and their supported weights, so the LLM can make informed formatting decisions without needing to call a separate discovery tool.

**Why this priority**: Without knowing what fonts are available, the LLM cannot reliably apply font formatting. Embedding this in tool descriptions ensures LLMs see it when they need it.

**Independent Test**: Can be fully tested by reading the import_section/import_tab tool descriptions and verifying they contain the complete font catalog.

**Acceptance Scenarios**:

1. **Given** an LLM reads the import_section or import_tab tool description, **When** it examines the formatting documentation, **Then** it finds a complete list of all fonts available in a default Google Doc with their supported weights.

2. **Given** an LLM has read the tool description, **When** it looks for font weight information, **Then** it can determine which specific weights (thin, light, normal, bold, etc.) each font family supports.

3. **Given** an LLM needs to format text with a light-weight font, **When** it checks the tool description, **Then** it can identify which font families support weight 300 (light).

---

### User Story 2 - LLM Applies Valid Font Formatting (Priority: P1)

An LLM writes content to a Google Doc with font formatting. The LLM uses the MEBDF format to specify fonts and weights that exist in the available fonts list.

**Why this priority**: This is the core use case - applying fonts that actually work. Without this, the entire font feature is broken.

**Independent Test**: Can be fully tested by writing content with valid font/weight combinations and verifying the resulting Google Doc displays the correct fonts.

**Acceptance Scenarios**:

1. **Given** an LLM specifies a valid font family and weight, **When** the content is imported to Google Docs, **Then** the text displays in the correct font and weight.

2. **Given** an LLM specifies font "Roboto" with weight 300 (light), **When** the content is imported, **Then** the text displays in Roboto Light (not Arial or any fallback).

3. **Given** an LLM combines font with other formatting (color, size), **When** the content is imported, **Then** all formatting is correctly applied.

---

### User Story 3 - Invalid Font Produces Clear Error (Priority: P1)

An LLM attempts to apply a font that doesn't exist or a weight that isn't supported by the specified font family. The MCP server detects this and returns a clear error instead of silently falling back to Arial.

**Why this priority**: Silent failures cause confusion and unpredictable results. Clear errors enable the LLM to self-correct.

**Independent Test**: Can be fully tested by attempting to apply invalid fonts/weights and verifying the server returns appropriate error messages.

**Acceptance Scenarios**:

1. **Given** an LLM specifies a non-existent font family like "FakeFont", **When** the import is attempted, **Then** the server returns an error identifying the invalid font.

2. **Given** an LLM specifies an unsupported weight for a valid font (e.g., Roboto with weight 200), **When** the import is attempted, **Then** the server returns an error identifying the unsupported weight.

3. **Given** an LLM specifies a font variant name instead of family + weight (e.g., "Roboto Light" as font family), **When** the import is attempted, **Then** the server returns an error explaining the correct format.

---

### User Story 4 - Tool Descriptions Guide LLM Usage (Priority: P2)

The MCP tool descriptions include clear documentation about font formatting syntax, available fonts, and common mistakes to avoid.

**Why this priority**: Good documentation prevents errors before they happen, reducing failed requests.

**Independent Test**: Can be tested by reviewing tool descriptions and verifying they contain font usage guidance.

**Acceptance Scenarios**:

1. **Given** an LLM reads the import_section or import_tab tool description, **When** it processes the formatting documentation, **Then** it finds clear instructions about font syntax including examples.

2. **Given** an LLM reads the tool description, **When** it looks for font information, **Then** it finds guidance that font family and weight must be specified separately.

---

### Edge Cases

- What happens when a font is valid but the requested weight rounds to a different value (e.g., weight 350)?
- How does the system handle mixed valid/invalid formatting in the same request (some fonts valid, some invalid)?
- What happens when the font name has different casing than expected (e.g., "roboto" vs "Roboto")?
- How does the system handle the "mono" shorthand vs explicit font specification?

---

### User Story 5 - Heading Text Formatting (Priority: P1) [FIXED]

An LLM writes content to a Google Doc where headings contain custom text formatting (fonts, colors, bold/italic). The formatting should be preserved when the content is imported.

**Why this priority**: Headings often have custom styling distinct from the document's default heading style.

**Bug Status**: FIXED

**Root Cause Analysis**:

When headings are serialized to Google Docs API requests in `mebdf_to_gdoc.py:434-463`, the `updateParagraphStyle` request (which sets `namedStyleType` to `HEADING_1`, etc.) is appended to the styles list AFTER child text style requests. When Google Docs processes these requests:

1. Text styles (font, color, bold) are applied first
2. Then `namedStyleType` is applied, which includes the heading's default text style
3. The heading's default text style OVERWRITES the previously applied inline formatting

**Fix Required**: In `HeadingNode` serialization, the `updateParagraphStyle` request must be inserted BEFORE the child text style requests, not after. This ensures:
1. Heading paragraph style (namedStyleType) is applied first
2. Inline text formatting (font, color, etc.) is applied second, overriding the heading defaults

**Location**: `src/extended_google_doc_utils/converter/mebdf_to_gdoc.py`, lines 434-463, `HeadingNode` branch in `serialize_node()`

**Fix Applied**: Changed `styles.append(...)` to `styles.insert(0, ...)` for the paragraph style request, ensuring it comes before any child text styles.

**Acceptance Scenarios**:

1. **Given** an LLM specifies a heading with custom font, **When** the content is imported, **Then** the heading displays in the specified font (not the heading's default font).

2. **Given** an LLM specifies a heading with colored text, **When** the content is imported, **Then** the heading displays in the specified color.

3. **Given** an LLM specifies a heading with bold/italic text within it, **When** the content is imported, **Then** the bold/italic formatting is preserved.

**Test Coverage Added**:
- `tests/tier_a/test_gdoc_to_mebdf.py::TestHeadingFormatting` - Reading formatting from headings (PASSING)
- `tests/tier_a/test_mebdf_to_gdoc.py::TestHeadingTextFormatting` - Writing formatting to headings (includes XFAIL test documenting bug)
- `tests/tier_a/test_round_trip.py::TestRoundTripHeadingFormatting` - MEBDF round-trip for heading formatting (PASSING)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Tool descriptions MUST include the complete list of fonts available in a default Google Doc with their supported weights.
- **FR-002**: Tool descriptions MUST document the font syntax (font family + weight as separate properties).
- **FR-003**: MCP server MUST validate font family names against the available fonts list before sending to Google Docs API.
- **FR-004**: MCP server MUST validate font weights against the supported weights for the specified font family.
- **FR-005**: MCP server MUST return a clear error message when an invalid font family is specified.
- **FR-006**: MCP server MUST return a clear error message when an unsupported weight is specified for a valid font family.
- **FR-007**: Error messages MUST identify the specific invalid font/weight and suggest valid alternatives.
- **FR-008**: System MUST accept font family names case-insensitively (normalizing to correct casing).
- **FR-009**: System MUST accept named weights (thin, light, normal, bold, etc.) in addition to numeric weights.

### Key Entities

- **Default Font Catalog**: The complete list of fonts available in a default Google Doc, including font family names and their supported weights.
- **Font Family**: A typeface available in Google Docs (e.g., Roboto, Arial, Times New Roman).
- **Font Weight**: A numeric value (100-900) or named value (thin, light, normal, bold, etc.) indicating the thickness of the font.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: LLMs can find the complete font catalog in tool descriptions without calling additional tools.
- **SC-002**: 100% of valid font/weight combinations specified by LLMs render correctly in Google Docs (no silent fallback to Arial).
- **SC-003**: 100% of invalid font/weight specifications produce clear error messages rather than silent fallback.
- **SC-004**: Error messages enable LLMs to self-correct on the next attempt (include valid alternatives).
- **SC-005**: No new MCP tools are added (font info is in documentation only).

## Assumptions

- The "default Google Doc fonts" refers to the fonts available in the Font menu of a new Google Doc without adding custom fonts.
- Font validation will be performed before sending requests to the Google Docs API, not by catching API errors.
- The font catalog will be hardcoded based on research of default Google Docs fonts (not dynamically queried).
- Case-insensitive matching is acceptable for font family names to improve usability.
- Named weights (thin, light, bold, etc.) will be normalized to numeric values internally.

## Out of Scope

- Supporting fonts beyond the default Google Docs font menu (e.g., fonts added via "More fonts").
- Dynamic font discovery from Google Fonts API.
- Custom/user-uploaded fonts.
- Font availability differences across Google Workspace editions.
