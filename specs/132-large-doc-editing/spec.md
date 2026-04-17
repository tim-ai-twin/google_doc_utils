# Feature Specification: Large Document Editing

**Feature Branch**: `132-large-doc-editing`
**Created**: 2026-03-29
**Status**: Draft
**Input**: User description: "Large document editing support with disk-based scan workflow to minimize context window usage when editing large Google Docs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Edit a Specific Paragraph in a Large Document (Priority: P1)

A user wants to find and edit a specific paragraph buried somewhere in a 50-page Google Doc. Today, the only option is to read the entire tab into context, wasting budget on 49 pages of irrelevant content. Instead, the user should be able to read the tab in plain markdown (keeping MEBDF overhead out), save it to a local file via the skill, search on disk to locate the target, then pull only the relevant section into context for editing.

**Why this priority**: This is the core use case — targeted editing of large documents without context blowup. Without this, large document editing is impractical.

**Independent Test**: Can be fully tested by reading a tab in plain format, saving to disk via the skill, grepping for a known phrase, reading just that section, and verifying the edit applies correctly.

**Acceptance Scenarios**:

1. **Given** a 50-page document, **When** the user reads a tab in plain markdown format, **Then** the response contains clean markdown without MEBDF formatting markers.
2. **Given** the skill is orchestrating the workflow, **When** the skill receives the plain markdown content from the MCP tool, **Then** it writes it to a local file for subsequent disk-based searching, avoiding repeated full-tab reads into context.
3. **Given** an exported file on disk, **When** the user searches for a phrase using standard file tools, **Then** they find the location and can identify which section heading it falls under.
4. **Given** the identified section anchor, **When** the user reads just that section via the MCP tool, **Then** only the target section content enters context (not the full document).
5. **Given** the section content in context, **When** the user writes an updated version back, **Then** only the target section is modified and the rest of the document remains unchanged.

---

### User Story 2 - Understand the Structure of a Large Document (Priority: P1)

A user wants to understand what a large multi-tab document contains — how many tabs, what sections exist, and how large each section is — before deciding what to read. Today, the hierarchy tool returns headings but no size information, so the user cannot judge which sections are large without reading them.

**Why this priority**: Size-aware hierarchy is the foundation for informed decisions about what to read. Without knowing section sizes, users cannot make smart choices about context budget.

**Independent Test**: Can be tested by calling the enhanced hierarchy tool on a document with sections of varying sizes and verifying that word counts are returned per heading.

**Acceptance Scenarios**:

1. **Given** a document with sections of varying lengths, **When** the user requests the hierarchy, **Then** each heading includes a word count and character count for the content under that heading (through to the next heading of equal or higher level).
2. **Given** the hierarchy with sizes, **When** the user looks at the response, **Then** they can identify which sections are large (thousands of words) vs small (a few sentences) and plan their reading accordingly.

---

### User Story 3 - Search Across Multiple Tabs (Priority: P2)

A user wants to find all mentions of a term across a multi-tab document (e.g., 5 tabs, each 10+ pages). Rather than reading every tab into context, they should be able to save each tab to disk and search all files at once.

**Why this priority**: Multi-tab search extends the core workflow to the multi-tab case, which is common for large documents.

**Independent Test**: Can be tested by saving multiple tabs to separate files via the skill, searching across all files for a known term, and verifying results include correct tab and section references.

**Acceptance Scenarios**:

1. **Given** a multi-tab document, **When** the skill saves each tab to separate files, **Then** each file is named in a way that identifies the tab it came from.
2. **Given** saved files from multiple tabs, **When** the user searches across files for a term, **Then** matches include enough context to identify the tab and section.

---

### User Story 4 - Guided Workflow via Skill (Priority: P2)

A user invokes an "edit Google Doc" skill that guides them through the optimal large-document workflow step by step — from discovering tabs, to understanding structure, to finding content on disk, to making the targeted edit. The skill handles all filesystem operations (writing temp files, cleanup) while the MCP server remains a pure data-access layer.

**Why this priority**: The skill makes the multi-step workflow discoverable and repeatable without the user needing to remember tool names or the correct sequence.

**Independent Test**: Can be tested end-to-end by invoking the skill with a document ID and edit description, and verifying it orchestrates the correct sequence of tool calls.

**Acceptance Scenarios**:

1. **Given** a user invokes the editing skill with a document ID, **When** the workflow begins, **Then** it first retrieves metadata to discover tabs, then shows the hierarchy with sizes.
2. **Given** the hierarchy is displayed, **When** the user describes what they want to edit, **Then** the skill reads the relevant tab in plain format, writes it to a temp file, and guides the user to search the file.
3. **Given** the target section is identified, **When** the edit is complete, **Then** the skill cleans up any temporary files.

---

### User Story 5 - Read Tab in Plain Markdown Format (Priority: P3)

A user wants to read a document tab as plain markdown (without MEBDF formatting markers) for easier reading and searching. MEBDF markers add noise when the goal is to find content, not to preserve formatting. The MCP tool returns the content; the skill (or user) decides whether to save it to disk.

**Why this priority**: Plain markdown produces cleaner output for text search. The MEBDF format is only needed when editing formatting — for content discovery, plain markdown is preferred.

**Independent Test**: Can be tested by reading the same tab in both plain and MEBDF formats and verifying the plain version has no formatting markers while preserving all text content.

**Acceptance Scenarios**:

1. **Given** a formatted document tab, **When** the user reads in plain markdown format, **Then** the response contains standard markdown without MEBDF formatting markers (`{!...}`, `{/!}`, `{^...}`).
2. **Given** a formatted document tab, **When** the user reads in MEBDF format (the default), **Then** the response contains full MEBDF with all formatting preserved for later editing.

---

### Edge Cases

- What happens when reading a tab that has no headings (unstructured content)? The hierarchy should return an empty headings list, and reading should still produce the full content.
- What happens when the skill writes to a path that already exists? The skill should overwrite the existing file (idempotent).
- What happens when the document has embedded images? Plain markdown should include image placeholders as alt text. MEBDF should include full image markers.
- What happens when the document is empty? Reading should produce empty content and return zero counts.
- What happens when section word counts are requested for a document with no headings? The entire content should be counted as a single "preamble" section.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tab-reading MCP tool MUST support a format parameter that allows reading in plain markdown (no MEBDF markers) or MEBDF (full formatting, the default).
- **FR-002**: The hierarchy MCP tool MUST be enhanced to include word count and character count for each heading's section (content from that heading through to the next heading of equal or higher level).
- **FR-003**: The hierarchy MCP tool MUST include total word count and character count in the response for the entire tab.
- **FR-004**: The hierarchy section sizes MUST count only text content (not formatting markers or image placeholders).
- **FR-005**: The MCP server MUST remain a pure data-access layer — it MUST NOT write to the local filesystem.
- **FR-006**: System MUST provide a Claude Code skill that orchestrates the large-document editing workflow (metadata, hierarchy, read plain, write to disk, search, read section, write section, cleanup).
- **FR-007**: The skill MUST handle all filesystem operations: writing tab content to temporary files, providing file paths to the user, and cleaning up temp files after editing is complete.
- **FR-008**: The skill MUST guide the user through each step, providing clear instructions and options at each stage.
- **FR-009**: For multi-tab documents, the skill MUST support saving individual tabs to separate files for cross-tab search.
- **FR-010**: The plain markdown format MUST preserve all text content, headings, lists, links, and structure while stripping MEBDF-specific formatting markers.

### Key Entities

- **Temporary Export File**: A local file written by the skill containing a document tab's content in plain markdown. Key attributes: file path, source document ID, source tab ID, word count, line count. Managed entirely by the skill (created, used, cleaned up).
- **Section Size**: Metadata attached to each heading in the hierarchy response. Key attributes: word count, character count, anchor ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a 50-page document, the save-to-disk-then-search-then-read-section workflow consumes at least 80% fewer context tokens than reading the full tab into context.
- **SC-002**: Users can locate and edit a specific paragraph in a 50-page document using the guided workflow within 6 tool calls (metadata, hierarchy, read plain, search, read_section, write_section) plus filesystem operations handled by the skill.
- **SC-003**: Section word counts in the hierarchy response are accurate to within 5% of the actual plain-text word count.
- **SC-004**: The guided skill successfully orchestrates the full edit workflow end-to-end on documents with 3+ tabs and 50+ pages total.
- **SC-005**: The MCP server performs no filesystem writes — all file operations are handled by the skill layer.
