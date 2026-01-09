# Feature Specification: Google Docs to Markdown Converter

**Feature Branch**: `126-gdoc-markdown-converter`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Build the ability to convert documents back and forth between Google Docs native format and the Markdown-like format with extensions for formatting and anchors"

## Design Constraints

**The Tab is the top-level unit of operation.** Multi-tab Google Docs cannot be handled as a single unit because MEBDF has no syntax to represent tab boundaries. All read and write operations target a specific tab within a Google Doc.

**Tab ID handling:**
- If a document has only one tab, the tab ID may be omitted (empty string)
- If a document has multiple tabs and no tab ID is provided, an error is returned
- This provides a simple default for single-tab documents while requiring explicit selection for multi-tab documents

**Section ID handling:**
- An empty string section ID refers to content before the first heading (the "preamble")
- This allows reading/writing introductory content that precedes any headings

## Research Questions (Validate Early)

Before implementation, the following Google Docs API behaviors must be validated:

1. **Heading Anchors**: Do Google Docs headings have implicit/automatic anchor IDs that can be retrieved via the API? If so, what format are they in?

2. **Anchor Stability**: When content before a heading is modified, does the heading's anchor ID remain stable? Or does it change based on position?

*These questions should be answered through API experimentation before committing to the detailed design.*

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get Tab Hierarchy (Priority: P1)

An MCP client needs to understand the structure of a Google Doc tab before deciding which sections to read or edit. The client requests the tab hierarchy and receives a lightweight outline showing only headings as pure markdown (`#`, `##`, `###`, etc.) with their anchor IDs. This enables efficient navigation and section-by-section editing workflows.

**Why this priority**: This is the essential navigation operation. Before reading or editing content, clients need to understand tab structure and obtain heading anchors for targeted section access. This is lightweight and fast, enabling efficient workflows without loading full content.

**Independent Test**: Can be fully tested by requesting hierarchy of a tab with multiple heading levels and verifying the output contains only heading lines with correct markdown levels and anchor IDs.

**Acceptance Scenarios**:

1. **Given** a tab with Heading 1, 2, and 3 styles, **When** hierarchy is requested, **Then** output contains only those headings as `#`, `##`, `###` markdown lines
2. **Given** a tab with headings, **When** hierarchy is requested, **Then** each heading includes its anchor ID using `{^ id}` syntax
3. **Given** a tab with no headings (only body text), **When** hierarchy is requested, **Then** an empty hierarchy is returned (no error)
4. **Given** a hierarchy response with anchor IDs, **When** an anchor ID is used to request that section, **Then** the section content is successfully retrieved
5. **Given** multiple headings with identical text, **When** hierarchy is requested, **Then** each heading has a unique anchor ID distinguishing them

---

### User Story 2 - Export Full Tab to Extended Markdown (Priority: P1)

An MCP client retrieves an entire Google Doc tab and needs to work with its content in a text-based format. The client requests a conversion of the full tab to extended markdown, receiving a clean text representation that preserves formatting semantics (highlights, underlines, colors, monospace) and anchor points for comments/bookmarks/headings.

**Why this priority**: This is the foundational read operation for full-tab workflows. Without the ability to export tabs to a workable text format, no downstream editing or analysis can occur.

**Independent Test**: Can be fully tested by converting a tab with various formatting (headers, bold, italic, highlights, colored text, monospace blocks, comments) and verifying the output markdown accurately represents all elements.

**Acceptance Scenarios**:

1. **Given** a tab with standard markdown elements (headers, bold, italic, lists, links), **When** full tab conversion is requested, **Then** the output contains valid standard markdown for these elements
2. **Given** a tab with highlighted text, **When** converted, **Then** the output contains `{!highlight:color}text{/!}` syntax with correct colors
3. **Given** a tab with underlined text, **When** converted, **Then** the output contains `{!underline}text{/!}` syntax
4. **Given** a tab with colored text, **When** converted, **Then** the output contains `{!color:#hexcode}text{/!}` syntax with accurate color values
5. **Given** a tab with monospace/code font spans, **When** converted, **Then** the output contains `{!mono}text{/!}` syntax for inline or `{!mono}` block syntax as appropriate
6. **Given** a tab with comments or bookmarks, **When** converted, **Then** anchor markers `{^ id}` appear at the correct positions in the text
7. **Given** a tab with headings, **When** converted, **Then** each heading line includes its anchor marker after the `#` markers: `## {^ id}Heading Text`
8. **Given** a tab with combined formatting (e.g., highlighted AND underlined), **When** converted, **Then** the output uses combined property syntax `{!highlight:yellow, underline}text{/!}`
9. **Given** a tab with embedded objects (images, drawings, charts), **When** converted, **Then** each embedded object is represented as `{^= id type}` placeholder
10. **Given** a single-tab document with no tab ID provided, **When** export is requested, **Then** the operation succeeds using the only tab
11. **Given** a multi-tab document with no tab ID provided, **When** export is requested, **Then** an error is returned indicating tab selection is required

---

### User Story 3 - Export Section by Heading Anchor (Priority: P1)

An MCP client needs to read only a specific section of a tab (for efficiency or focused editing). Using a heading anchor ID obtained from the hierarchy, the client requests just that section's content as extended markdown. The section includes all content from the specified heading until the next heading of equal or higher level.

**Why this priority**: Section-level access is essential for working with large documents efficiently. AI tools often need to focus on specific sections rather than processing entire tabs, reducing token usage and improving response quality.

**Independent Test**: Can be fully tested by requesting a section by anchor ID and verifying only content between that heading and the next same-or-higher-level heading is returned.

**Acceptance Scenarios**:

1. **Given** an anchor ID for a `## Section A` heading, **When** section export is requested, **Then** content from `## Section A` through all its subsections (###, ####) until the next `##` or `#` is returned
2. **Given** an anchor ID for the last section in a tab, **When** section export is requested, **Then** content from that heading to the end of the tab is returned
3. **Given** an anchor ID for a top-level `# Heading`, **When** section export is requested, **Then** all content under that heading (including all `##`, `###` subsections) is returned
4. **Given** an anchor ID, **When** section export is requested, **Then** all formatting extensions and anchors within that section are preserved
5. **Given** an invalid or non-existent anchor ID, **When** section export is requested, **Then** an appropriate error is returned
6. **Given** an empty string as the section ID, **When** section export is requested, **Then** content before the first heading (preamble) is returned
7. **Given** a tab with no content before the first heading, **When** empty string section is requested, **Then** empty content is returned (no error)

---

### User Story 4 - Import Extended Markdown to Full Tab (Priority: P2)

An MCP client has modified content in extended markdown format and needs to write it back to a Google Doc tab. The client submits the markdown content and the system converts it to Google Docs native format, replacing the entire tab content.

**Why this priority**: This completes the round-trip capability for full-tab workflows. Depends on P1 for the format definition validation.

**Independent Test**: Can be fully tested by creating extended markdown with various formatting extensions and converting to a Google Doc tab, then verifying all formatting is correctly applied.

**Acceptance Scenarios**:

1. **Given** extended markdown with `{!highlight:yellow}text{/!}`, **When** imported to a tab, **Then** the text appears with yellow highlight
2. **Given** extended markdown with `{!underline}text{/!}`, **When** imported, **Then** the text appears underlined
3. **Given** extended markdown with `{!color:#cc0000}text{/!}`, **When** imported, **Then** the text appears in the specified color
4. **Given** extended markdown with `{!mono}` block syntax, **When** imported, **Then** following paragraphs use monospace font until `{!mono:false}` or style change
5. **Given** extended markdown with existing anchor markers `{^ id}`, **When** imported, **Then** anchors are positioned at the marker locations with their original IDs preserved
6. **Given** extended markdown with proposed anchor markers `{^}`, **When** imported, **Then** new anchors are created at those positions
7. **Given** extended markdown with standard markdown elements (headers, bold, italic, lists), **When** imported, **Then** appropriate Google Docs formatting is applied
8. **Given** extended markdown with embedded object placeholders `{^= id type}` referencing objects that exist in the document, **When** imported, **Then** the original embedded object is preserved at that position unchanged
9. **Given** extended markdown with an embedded object placeholder `{^= id type}` where the ID does not exist in the document, **When** imported, **Then** an error is returned (embedded objects cannot be created via placeholder)

---

### User Story 5 - Import Section by Heading Anchor (Priority: P2)

An MCP client has modified a specific section and needs to write only that section back to the tab. Using the heading anchor ID, the client submits extended markdown that replaces just that section's content while preserving the rest of the tab.

**Why this priority**: Section-level writes enable surgical edits without risking changes to unrelated parts of the tab. Essential for safe AI-assisted editing of large documents.

**Independent Test**: Can be fully tested by exporting a section, modifying it, re-importing by anchor ID, and verifying only that section changed while other sections remain untouched.

**Acceptance Scenarios**:

1. **Given** an anchor ID and new section content, **When** section import is requested, **Then** only content between that heading and the next same-or-higher-level heading is replaced
2. **Given** section content with a different heading text than the original, **When** imported, **Then** the heading text is updated to match the new content
3. **Given** section content with additional subsections not in the original, **When** imported, **Then** the new subsections are added within that section
4. **Given** section content with fewer subsections than the original, **When** imported, **Then** removed subsections are deleted from the tab
5. **Given** a section import, **When** completed, **Then** content outside the target section (before and after) remains unchanged
6. **Given** section content with formatting and anchors, **When** imported, **Then** all formatting extensions and anchors are applied correctly
7. **Given** a section containing an embedded image and surrounding text, **When** the text is modified but the `{^= id image}` placeholder is preserved, **Then** the image remains in place and only the text changes (common business document workflow)

---

### User Story 6 - Round-Trip Preservation (Priority: P3)

An MCP client exports content (full tab or section), makes targeted text edits while preserving formatting markers and anchors, then imports the modified content back. The tab retains all original formatting and anchor associations on unchanged content.

**Why this priority**: This validates the complete workflow and ensures the format is truly round-trip safe. Critical for the use case of AI-assisted editing where only content changes while formatting is preserved.

**Independent Test**: Can be tested by exporting content, making a small text change, re-importing, and verifying unchanged portions retain exact formatting.

**Acceptance Scenarios**:

1. **Given** a tab exported to markdown and re-imported without changes, **When** compared to original, **Then** all formatting and anchor positions are identical
2. **Given** exported markdown where only text within a formatted span is edited (keeping markers), **When** imported, **Then** the formatting applies to the edited text
3. **Given** exported markdown where an anchor marker `{^ id}` is moved to a new position in the text, **When** imported, **Then** the anchor and its associated comment/bookmark attach to the new position
4. **Given** exported markdown where formatting markers are removed from text, **When** imported, **Then** that text appears without the previously applied formatting
5. **Given** a section exported and re-imported without changes, **When** the full tab is examined, **Then** that section and all other sections remain unchanged

---

### Edge Cases

- What happens when a Google Doc contains formatting not covered by the extension spec (e.g., strikethrough, superscript, subscript)?
  - *Assumption: Unsupported formatting passes through as plain text with no markers; a warning is logged*
- How does the system handle nested formatting (bold text that is also highlighted)?
  - *Standard markdown handles bold/italic; extension handles highlight/underline/color separately*
- What happens when malformed extension syntax is encountered during import?
  - *Malformed syntax is treated as literal text and not interpreted as formatting*
- How are empty anchor markers `{^}` handled if the tab already has anchors with sequential IDs?
  - *New unique IDs are generated that don't conflict with existing anchors*
- What happens with very large tabs (100+ pages)?
  - *System processes the tab; performance targets defined in Success Criteria*
- What happens when a section import changes the heading level (e.g., `##` to `###`)?
  - *The heading level is updated as specified; subsection boundaries may shift accordingly*
- What happens when an anchor ID references a heading that was deleted?
  - *An error is returned indicating the anchor ID is no longer valid*

## Requirements *(mandatory)*

### Functional Requirements

#### Tab-Level Operations

- **FR-001**: System MUST operate at the tab level; a tab is the highest-level unit for all operations
- **FR-002**: System MUST support reading entire tabs
- **FR-003**: System MUST support writing to entire tabs (full replacement)
- **FR-004**: System MUST NOT support multi-tab operations in a single call (MEBDF cannot represent tab boundaries)
- **FR-005**: System MUST accept empty string as tab ID for single-tab documents
- **FR-006**: System MUST return an error when tab ID is empty and document has multiple tabs

#### Section-Level Operations

- **FR-007**: System MUST support reading individual sections identified by heading anchor ID
- **FR-008**: System MUST support writing to individual sections identified by heading anchor ID (section replacement)
- **FR-009**: A section includes all content from a heading until the next heading of equal or higher level
- **FR-010**: Section export MUST include the heading line itself as the first line of output
- **FR-011**: Section import MUST replace content from the target heading through (but not including) the next same-or-higher-level heading
- **FR-012**: System MUST accept empty string as section ID to reference content before the first heading (preamble)

#### Hierarchy API

- **FR-013**: System MUST provide a read-only hierarchy view returning only headings as pure markdown
- **FR-014**: Hierarchy output MUST contain only heading lines (`#`, `##`, `###`, etc.) with no body content
- **FR-015**: Each heading in hierarchy MUST include its anchor ID using `## {^ id}Heading Text` syntax
- **FR-016**: Heading anchor IDs MUST be obtained from Google Docs' implicit heading anchors (pending research validation)

#### Format Conversion - Export

- **FR-017**: System MUST convert Google Docs paragraph styles (Normal, Heading 1-6) to corresponding markdown heading syntax
- **FR-018**: System MUST convert Google Docs character formatting (bold, italic) to standard markdown syntax (`**bold**`, `*italic*`)
- **FR-019**: System MUST convert Google Docs lists (bulleted, numbered) to markdown list syntax
- **FR-020**: System MUST convert Google Docs links to markdown link syntax `[text](url)`
- **FR-021**: System MUST convert Google Docs highlight formatting to `{!highlight:color}text{/!}` syntax
- **FR-022**: System MUST convert Google Docs underline formatting to `{!underline}text{/!}` syntax
- **FR-023**: System MUST convert Google Docs text color to `{!color:#hexcode}text{/!}` syntax
- **FR-024**: System MUST convert Google Docs monospace font spans to `{!mono}text{/!}` inline or `{!mono}` block syntax
- **FR-025**: System MUST identify and mark anchor points (comments, bookmarks, headings) with `{^ id}` syntax preserving original IDs
- **FR-026**: System MUST support combined formatting properties in single extension markers (e.g., `{!highlight:yellow, underline}`)
- **FR-027**: System MUST convert stateful block formatting using standalone `{!props}` syntax on its own line

#### Format Conversion - Import

- **FR-028**: System MUST import extended markdown and create corresponding Google Docs formatting
- **FR-029**: System MUST preserve anchor IDs when round-tripping tabs (export then import)
- **FR-030**: System MUST generate new unique anchor IDs for proposed anchors `{^}` during import

#### Embedded Objects

- **FR-031**: System MUST convert embedded objects (images, drawings, charts, equations, videos) to `{^= id type}` placeholder syntax on export
- **FR-032**: System MUST preserve embedded objects unchanged when their `{^= id type}` placeholder is present on import (object must already exist in document)
- **FR-033**: System MUST return an error if an embedded object placeholder references an ID that does not exist in the document
- **FR-034**: Embedded object types MUST be one of: `image`, `drawing`, `chart`, `equation`, `video`, `embed`

#### Additional Format Support

- **FR-035**: System MUST handle Google Docs tables by converting to markdown table syntax
- **FR-036**: System MUST support the `{!font:name}`, `{!size:Npt}`, and `{!weight:value}` block properties
- **FR-037**: System MUST support paragraph formatting properties: `align`, `indent-left`, `indent-right`, `line-spacing`, `space-before`, `space-after`

### Key Entities

- **Tab**: The top-level unit of operation; identified by document ID + tab ID (empty string allowed for single-tab docs)
- **Section**: A portion of a tab from one heading to the next same-or-higher-level heading (empty string ID = preamble)
- **HeadingAnchor**: An anchor ID associated with a heading, used for section-level operations
- **EmbeddedObject**: An opaque object (image, drawing, chart, etc.) preserved via `{^= id type}` placeholder
- **Paragraph**: A block-level element with potential block formatting state
- **TextRun**: A contiguous span of text with uniform character formatting
- **Anchor**: A position marker with unique ID, associated with comments, bookmarks, or headings
- **FormattingState**: The current block-level formatting context (stateful across paragraphs)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of standard markdown elements (headers, bold, italic, lists, links) convert correctly in both directions
- **SC-002**: 100% of supported extension formatting types (highlight, underline, color, mono) convert correctly in both directions
- **SC-003**: Round-trip conversion of a tab with no edits produces semantically identical output (formatting and anchor positions match)
- **SC-004**: Full tabs up to 50 pages convert within 30 seconds
- **SC-005**: Hierarchy requests return within 2 seconds regardless of tab size
- **SC-006**: Section-level operations complete within 5 seconds for sections up to 10 pages
- **SC-007**: Anchor IDs are preserved with 100% accuracy during round-trip operations
- **SC-008**: 95% of real-world Google Docs tabs (with typical business document formatting) convert without data loss in supported formatting types
- **SC-009**: Malformed extension syntax in input does not cause conversion failure; invalid markers appear as literal text
- **SC-010**: Section imports leave content outside the target section 100% unchanged

## Assumptions

- The existing Google Docs access mechanism provides sufficient API access to read tab structure and formatting details
- The md-extensions-spec.md format is stable and changes to it would require corresponding converter updates
- **Google Docs headings have implicit anchor IDs that are accessible via the API** (requires validation)
- **Heading anchor IDs remain stable when surrounding content is edited** (requires validation)
- Comments and suggestions in Google Docs are associated with anchors that have stable IDs
- Block formatting state resets at major structural boundaries (e.g., tables, page breaks, section boundaries)
- Images are referenced but not embedded in the markdown output (URLs or placeholders used)
- Google Docs headings (Heading 1-6 paragraph styles) are used consistently to define tab structure

## Dependencies

- Existing Google Docs API access implementation
- The md-extensions-spec.md format specification (MEBDF and MEA extensions)
- **Research validation of Google Docs API heading anchor behavior** (blocking dependency for section-level features)

## Out of Scope

- **Multi-tab operations**: Cannot be supported because MEBDF has no tab boundary syntax
- Real-time collaborative editing synchronization
- Comment thread content extraction (only anchor positions are preserved)
- Conversion of Google Docs add-on specific formatting
- Version history preservation
- Formatting types not defined in md-extensions-spec.md (strikethrough, superscript, subscript, etc.)
- Cross-section operations (e.g., moving a section to a different location)
- Creating new tabs programmatically
- Editing embedded object content (images, drawings, charts are preserved but not modified)
