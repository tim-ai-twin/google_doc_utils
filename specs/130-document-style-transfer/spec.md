# Feature Specification: Document Style Transfer

**Feature Branch**: `130-document-style-transfer`
**Created**: 2026-01-19
**Status**: Draft
**Input**: User description: "Add ability to read document level properties and apply them to a document. Add ability to read all 9 style types, even though they must be applied for every single block of text. This feature should be exposed in the API and in the MCP server. It should have round trip test coverage. It should support user requests like 'Apply the styles from document A to document B'. You do not need to deal with all caps, super/sub-script, or strikethrough."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Document Styles (Priority: P1)

A user wants to inspect the styling of an existing Google Doc to understand its formatting conventions. They request to see the document-level properties (background, margins, page size) and the **effective/visible styles** for all 9 style types (Normal Text, Title, Subtitle, Heading 1-6).

**Key Concept - Effective Styles**: The system captures what the user actually sees, not just style definitions. If paragraphs use their named style definition, return that. If paragraphs have consistent inline overrides that differ from the style definition, return those overrides as the "effective" style. The goal is to enable "copy what I see" behavior.

**Why this priority**: Reading styles is the foundation for all other operations. Without being able to read styles, you cannot transfer them.

**Independent Test**: Can be fully tested by reading styles from any existing Google Doc and verifying the returned data matches what's visible in the document. Delivers immediate value for understanding document formatting.

**Acceptance Scenarios**:

1. **Given** a Google Doc with custom document-level settings (background color, custom margins), **When** the user requests document styles, **Then** the system returns the background color, all four margins, and page size.

2. **Given** a Google Doc where HEADING_1 paragraphs use the named style definition (no overrides), **When** the user requests styles, **Then** the system returns the HEADING_1 style definition values.

3. **Given** a Google Doc where all HEADING_1 paragraphs have been manually formatted to "Roboto 20pt blue" (overriding the style definition of "Arial 24pt black"), **When** the user requests styles, **Then** the system returns "Roboto 20pt blue" as the effective HEADING_1 style.

4. **Given** a Google Doc using default styles with no overrides, **When** the user requests styles, **Then** the system returns the default style values.

5. **Given** a Google Doc with no paragraphs of a particular style type (e.g., no TITLE), **When** the user requests styles, **Then** the system returns the named style definition for that type (since there are no paragraphs to sample).

---

### User Story 2 - Apply Document-Level Properties (Priority: P1)

A user wants to apply document-level settings from a source document to a target document. This includes background color, page margins, and page size.

**Why this priority**: Document-level properties are global settings that can be applied once via a single API request, making this the simplest form of style transfer.

**Independent Test**: Can be tested by reading document properties from Document A, applying them to Document B, then verifying Document B's properties match Document A's.

**Acceptance Scenarios**:

1. **Given** a source document with a light gray background, **When** the user applies document styles to a target document, **Then** the target document's background becomes light gray.

2. **Given** a source document with 1-inch margins on all sides, **When** the user applies document styles to a target, **Then** the target document's margins become 1 inch on all sides.

3. **Given** a source document with Letter page size, **When** the user applies document styles to a target with A4 page size, **Then** the target document's page size becomes Letter.

---

### User Story 3 - Transfer Named Styles Between Documents (Priority: P1)

A user says "Apply the styles from document A to document B." The system reads the **effective/visible styles** from the source document (what the user actually sees) and applies them to all matching paragraphs in the target document.

**Why this priority**: This is the core use case that enables brand consistency across documents and is the primary user request the feature must support.

**Independent Test**: Can be tested by creating two documents with different heading styles, transferring styles, and verifying all headings in the target now match what was visible in the source.

**Acceptance Scenarios**:

1. **Given** Document A has HEADING_1 paragraphs displaying as "Roboto, 24pt, bold, blue" (whether from style definition or overrides), and Document B has three HEADING_1 paragraphs using default styling, **When** the user transfers styles from A to B, **Then** all three headings in Document B display as "Roboto, 24pt, bold, blue".

2. **Given** Document A has HEADING_1 defined as "Arial 24pt" but all actual HEADING_1 paragraphs are overridden to "Georgia 18pt red", **When** styles are transferred to Document B, **Then** Document B's headings become "Georgia 18pt red" (the effective style, not the definition).

3. **Given** Document A has NORMAL_TEXT paragraphs with 1.15 line spacing and 6pt space after (whether from definition or overrides), **When** styles are transferred to Document B, **Then** all normal text paragraphs in Document B have 1.15 line spacing and 6pt space after.

4. **Given** Document A has custom effective styles for all 9 style types, **When** styles are transferred to Document B, **Then** paragraphs of each style type in Document B are updated to match their corresponding effective style from Document A.

5. **Given** Document B has some paragraphs with inline formatting overrides (e.g., a bold word within a heading), **When** styles are transferred, **Then** the paragraph-level style properties are applied while character-level overrides within the paragraph are preserved.

---

### User Story 4 - MCP Server Style Operations (Priority: P2)

An LLM using the MCP server needs to read styles from one document and apply them to another as part of a larger workflow (e.g., "Make this report match our company template").

**Why this priority**: MCP exposure is required by the feature description but builds on the core API functionality.

**Independent Test**: Can be tested by calling MCP tools directly to read and apply styles, verifying the same results as the programmatic API.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an LLM calls the "get document styles" tool with a document ID, **Then** it receives a structured response containing document-level properties and effective styles for all 9 style types (reflecting what the user actually sees).

2. **Given** a document where HEADING_1 paragraphs have been manually overridden to use different formatting than the style definition, **When** an LLM calls "get document styles", **Then** it receives the overridden formatting as the effective HEADING_1 style.

3. **Given** the MCP server is running, **When** an LLM calls the "apply document styles" tool with source and target document IDs, **Then** the target document is updated with effective styles from the source.

4. **Given** an LLM wants to apply only document-level properties (not named styles), **When** it calls the apply tool with appropriate parameters, **Then** only document-level properties are transferred.

---

### User Story 5 - Round Trip Style Preservation (Priority: P2)

A developer wants to verify that reading styles from a document and applying them back produces identical results (round-trip integrity).

**Why this priority**: Round-trip testing ensures data fidelity and catches edge cases in serialization/deserialization.

**Independent Test**: Can be tested by reading styles from Document A, applying to Document B, reading from Document B, and comparing the two style sets.

**Acceptance Scenarios**:

1. **Given** a document with complex custom styles, **When** styles are read, applied to a new document, and read again, **Then** the style values match (within acceptable floating-point tolerance for numeric values).

2. **Given** a document with default styles, **When** round-trip is performed, **Then** default values are preserved correctly.

---

### Edge Cases

- What happens when the source document has styles that reference fonts not available in the target user's account? Answer: Pass through font names as-is; Google Docs handles fallback.
- How does the system handle a target document that has no paragraphs of a particular style type (e.g., no TITLE paragraph)? Answer: Those style definitions are simply not applied since there are no matching paragraphs.
- What happens when document-level properties are partially defined (some margins set, others default)? Answer: Apply only the defined properties, leaving others unchanged.
- How does the system behave when transferring styles to a document with protected ranges or suggestions mode? Answer: API may return permission errors for protected content; system should report these gracefully.
- What happens if the source and target are the same document? Answer: This is a valid operation (re-applying styles); system should handle it without error.
- How are colors handled when source uses theme colors vs explicit RGB? Answer: Convert all colors to explicit RGB values for consistent transfer.
- What happens when paragraphs of the same style type have inconsistent formatting (e.g., some HEADING_1s are blue, others are red)? Answer: Use the formatting from the first paragraph of that type encountered, or the most common formatting (implementation may choose). The system should handle this gracefully rather than failing.
- What happens when a paragraph has partial overrides (e.g., font is overridden but size uses the style definition)? Answer: Capture the complete effective/resolved formatting - merge style definition with overrides to get what the user sees.
- How do multi-tab documents work? Answer: Users can specify a `tab_id` to target a specific tab. If no tab_id is provided, the first/default tab is used. This is consistent with all other MCP tools in the system.

## Google Docs Style Hierarchy

Google Docs uses a 3-level style inheritance model that the API exposes differently than what users see visually. Understanding this is critical for correct style extraction.

1. **Named Style Definitions** (`namedStyles.styles[]`): Template-level defaults for HEADING_1, NORMAL_TEXT, etc. Contains complete style properties. When a user clicks "Update 'Heading 1' to match", this is what gets modified.

2. **Paragraph Style** (`paragraph.paragraphStyle`): Per-paragraph settings. The API only returns **overrides** from the named style, not the full resolved style. An empty object means "inherit everything from the named style."

3. **Text Run Style** (`textRun.textStyle`): Inline formatting on specific text within a paragraph. Again, the API only returns **overrides**, not resolved values. Selecting text and changing its color creates an override here.

To get the "effective style" (what the user sees), you must merge all three levels: Named Definition + Paragraph Overrides + Text Run Overrides. The API does not provide a pre-merged "resolved" style—this must be computed by the client. This feature handles this merging automatically when reading styles.

---

## Requirements *(mandatory)*

### Functional Requirements

**Document-Level Properties:**

- **FR-001**: System MUST read document background color from any Google Doc
- **FR-002**: System MUST read page margins (top, bottom, left, right) from any Google Doc
- **FR-003**: System MUST read page size (width, height) from any Google Doc
- **FR-004**: System MUST apply document background color to a target Google Doc
- **FR-005**: System MUST apply page margins to a target Google Doc
- **FR-006**: System MUST apply page size to a target Google Doc

**Named Styles (Effective Style Extraction):**

- **FR-007**: System MUST determine the effective/visible style for all 9 style types (NORMAL_TEXT, TITLE, SUBTITLE, HEADING_1 through HEADING_6)
- **FR-008**: For each style type, system MUST analyze actual paragraphs in the document to determine the predominant formatting (what the user sees)
- **FR-009**: If paragraphs of a style type use the named style definition (no overrides), system MUST return the style definition values
- **FR-010**: If paragraphs of a style type have consistent inline overrides, system MUST return those override values as the effective style
- **FR-011**: If no paragraphs of a style type exist in the document, system MUST fall back to the named style definition
- **FR-012**: For each effective style, system MUST capture these text properties: font family, font size, font weight, text color, highlight color, bold, italic, underline
- **FR-013**: For each effective style, system MUST capture these paragraph properties: alignment, line spacing, space before, space after, indentation (start, end, first line)
- **FR-014**: System MUST apply effective style text properties to all paragraphs of matching type in target document
- **FR-015**: System MUST apply effective style paragraph properties to all paragraphs of matching type in target document
- **FR-016**: System MUST preserve character-level inline formatting overrides (e.g., a bold word) when applying paragraph-level styles

**API Exposure:**

- **FR-017**: System MUST provide a Python API function to read effective document styles (both document-level and effective named styles)
- **FR-018**: System MUST provide a Python API function to apply document styles from one document to another
- **FR-019**: API MUST support applying only document-level properties, only effective named styles, or both
- **FR-020**: API MUST return a summary of changes made (number of paragraphs updated per style type)

**MCP Server:**

- **FR-021**: MCP server MUST expose a tool to read effective document styles
- **FR-022**: MCP server MUST expose a tool to apply document styles between documents
- **FR-023**: MCP tools MUST return structured data suitable for LLM consumption
- **FR-024**: MCP tools MUST provide clear error messages when operations fail

**Multi-Tab Document Support:**

- **FR-031**: All style transfer tools MUST support a `tab_id` parameter for multi-tab documents
- **FR-032**: When `tab_id` is empty or omitted, tools MUST use the first/default tab
- **FR-033**: Python API functions MUST accept an optional `tab_id` parameter
- **FR-034**: MCP tools MUST expose `tab_id` as an optional parameter with clear documentation
- **FR-035**: Document properties (background, margins, page size) MUST be read from the tab-level `documentStyle`, not the top-level document style, to correctly handle multi-tab documents where each tab can have different page settings

**Testing:**

- **FR-025**: System MUST have unit tests for effective style extraction (mocked API responses)
- **FR-026**: System MUST have unit tests for style application request building
- **FR-027**: System MUST have round-trip integration tests verifying style fidelity

**Exclusions:**

- **FR-028**: System is NOT required to support small caps in this feature
- **FR-029**: System is NOT required to support superscript or subscript in this feature
- **FR-030**: System is NOT required to support strikethrough in this feature

### Key Entities

- **DocumentStyle**: Represents document-level formatting including background color, page margins (top, bottom, left, right), and page size (width, height)
- **EffectiveStyle**: Represents the visible/actual style for a style type as seen by the user - derived either from the named style definition or from inline overrides on actual paragraphs
- **NamedStyleDefinition**: The style template from the document's namedStyles (what Google Docs stores as the style definition)
- **TextStyle**: Character-level formatting including font family, font size, font weight, text color, highlight color, bold, italic, underline
- **ParagraphStyle**: Block-level formatting including alignment, line spacing, space before, space after, and indentation properties
- **StyleTransferOptions**: Configuration for transfer operation specifying whether to include document-level properties, effective named styles, or both

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can read complete style information from any Google Doc in under 5 seconds
- **SC-002**: Users can apply styles from one document to another with 100+ paragraphs in under 30 seconds
- **SC-003**: Round-trip style transfer preserves all supported style properties with 100% fidelity (exact match for text values, within 0.01pt tolerance for numeric values)
- **SC-004**: MCP tools successfully complete style operations when called by automated LLM workflows
- **SC-005**: All 9 named style types can be read and their properties transferred to matching paragraphs
- **SC-006**: Test coverage includes unit tests for all read/write operations and integration tests for round-trip scenarios

## Assumptions

- Users have appropriate permissions (edit access) on target documents
- Source documents are accessible (at least view access) by the user
- The Google Docs API rate limits are sufficient for typical document sizes (documents under 1000 paragraphs)
- Font names in source documents are valid Google Docs fonts; invalid fonts will be passed through as-is (Google Docs handles fallback)
