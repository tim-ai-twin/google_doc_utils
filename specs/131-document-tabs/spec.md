# Feature Specification: Document Tabs Support

**Feature Branch**: `131-document-tabs`
**Created**: 2026-03-29
**Status**: Draft
**Input**: User description: "Let's update this project to support tabs in documents"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Content from a Specific Tab (Priority: P1)

A user working with a multi-tab Google Doc (e.g., a project plan with separate tabs for "Overview", "Timeline", and "Budget") wants to read the content of a specific tab. They discover the available tabs, select one by ID or title, and retrieve its MEBDF content — without affecting other tabs.

**Why this priority**: Reading is the most fundamental operation. Users cannot do anything meaningful with tabs until they can reliably discover and read from them.

**Independent Test**: Can be fully tested by creating a multi-tab document, listing its tabs, and reading content from each tab individually. Delivers the ability to inspect any tab in a multi-tab document.

**Acceptance Scenarios**:

1. **Given** a document with 3 tabs, **When** user requests metadata, **Then** all 3 tabs are listed with their IDs, titles, and indices.
2. **Given** a document with 3 tabs, **When** user reads tab "Overview" by its tab_id, **Then** only the content of "Overview" is returned in MEBDF format.
3. **Given** a document with 3 tabs, **When** user reads a section within a specific tab, **Then** only that section's content from that tab is returned.
4. **Given** a document with 3 tabs, **When** user requests content without specifying a tab_id, **Then** the system raises a clear error listing available tabs.

---

### User Story 2 - Write/Edit Content in a Specific Tab (Priority: P1)

A user wants to update the content of a specific tab in a multi-tab document. They write MEBDF content to a chosen tab, and only that tab's content changes — other tabs remain untouched.

**Why this priority**: Writing is equally fundamental. Together with reading, it enables the core workflow of editing multi-tab documents.

**Independent Test**: Can be tested by writing content to one tab and verifying other tabs are unchanged. Delivers the ability to safely modify individual tabs.

**Acceptance Scenarios**:

1. **Given** a document with 2 tabs, **When** user writes new content to tab "Timeline", **Then** tab "Timeline" contains the new content and tab "Overview" is unchanged.
2. **Given** a document with 2 tabs, **When** user writes a section within a specific tab, **Then** only that section in that tab is updated.
3. **Given** a document with 2 tabs, **When** user writes content without specifying a tab_id, **Then** the system raises a clear error listing available tabs.

---

### User Story 3 - Formatting and Style Operations on Tabs (Priority: P2)

A user wants to extract styles, normalize formatting, or transfer styles on a per-tab basis. For example, they want to apply the formatting from a "Template" tab to a "Draft" tab within the same document, or across documents.

**Why this priority**: Style operations are valuable but secondary to basic read/write. Users need read/write working reliably before style operations matter.

**Independent Test**: Can be tested by extracting styles from one tab and applying to another, then verifying the target tab's formatting changed correctly.

**Acceptance Scenarios**:

1. **Given** a document with styled content in tab A, **When** user extracts styles from tab A, **Then** styles are returned correctly for that tab only.
2. **Given** a source tab and a target tab, **When** user transfers styles between them, **Then** the target tab's formatting updates and other tabs are unaffected.
3. **Given** a multi-tab document, **When** user normalizes formatting on one tab, **Then** only that tab's formatting is normalized.

---

### User Story 4 - Heading Hierarchy within a Tab (Priority: P2)

A user wants to navigate a multi-tab document by viewing the heading hierarchy of a specific tab. This is essential for section-based operations where the user needs to identify anchor IDs within a particular tab.

**Why this priority**: Supports section-level operations (read_section, write_section) which depend on knowing heading structure within a specific tab.

**Independent Test**: Can be tested by requesting hierarchy for a specific tab and verifying only that tab's headings are returned.

**Acceptance Scenarios**:

1. **Given** a document where tab A has 3 headings and tab B has 5 headings, **When** user requests hierarchy for tab A, **Then** only tab A's 3 headings are returned.

---

### Edge Cases

- What happens when a tab_id references a tab that has been deleted?
- What happens when a document's tab structure changes between metadata retrieval and content operations?
- How does the system handle a document where all tabs have been deleted except one (effectively a single-tab document)?
- What happens when two tabs have very similar titles but different IDs?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST list all tabs in a document including their IDs, titles, and indices when metadata is requested.
- **FR-002**: System MUST allow reading the full content of any individual tab by tab_id.
- **FR-003**: System MUST allow reading a section within a specific tab by combining tab_id and anchor_id.
- **FR-004**: System MUST allow writing/replacing content in a specific tab without affecting other tabs.
- **FR-005**: System MUST allow writing a section within a specific tab without affecting other sections or other tabs.
- **FR-006**: System MUST raise a clear, actionable error when a multi-tab document is accessed without specifying a tab_id. The error MUST list available tabs.
- **FR-007**: System MUST support extracting and applying styles on a per-tab basis.
- **FR-008**: System MUST support heading hierarchy retrieval for a specific tab.
- **FR-009**: System MUST correctly handle the transition between single-tab documents (where tab_id is optional) and multi-tab documents (where tab_id is required).

### Assumptions

- MEBDF format remains tab-scoped — there is no need for a multi-tab MEBDF syntax. Each operation targets exactly one tab.
- Tab IDs are assigned by Google Docs (e.g., "t.0", "t.1") and are stable for the lifetime of a tab.
- The existing converter architecture (TabReference, tab_utils, MultipleTabsError) is sound and does not need redesign — the work is primarily validation and bug fixing.

### Key Entities

- **Tab**: A discrete content section within a Google Doc, identified by a tab_id, with its own body content, document style, named styles, and inline/positioned objects.
- **TabReference**: An immutable reference pairing a document_id with a tab_id, used to scope all converter operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All read operations (full tab, section, hierarchy) return correct content when given a valid tab_id on a multi-tab document — verified by automated tests.
- **SC-002**: All write operations (full tab, section) modify only the targeted tab — verified by reading other tabs before and after and confirming no changes.
- **SC-003**: Style extraction and application work correctly on individual tabs within multi-tab documents — verified by automated tests.
- **SC-004**: Error messages for missing tab_id on multi-tab documents include the list of available tabs and their titles — verified by test assertions.
- **SC-005**: All existing single-tab document tests continue to pass unchanged — verified by running the full test suite.
