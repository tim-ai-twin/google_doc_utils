# Data Model: Document Tabs Support

**Feature**: 131-document-tabs
**Date**: 2026-03-29

## Entities

### Tab (unchanged — already exists in Google Docs API response)

| Field | Description |
|-------|-------------|
| `tabProperties.tabId` | Unique identifier (e.g., "t.0") |
| `tabProperties.title` | User-visible tab name |
| `tabProperties.index` | Ordinal position (0-based) |
| `documentTab.body` | Tab's body content |
| `documentTab.documentStyle` | Tab's document-level styles |
| `documentTab.namedStyles` | Tab's named style definitions |
| `documentTab.inlineObjects` | Tab's inline objects (images, etc.) |
| `documentTab.positionedObjects` | Tab's positioned objects |

### TabReference (unchanged — already exists)

| Field | Description |
|-------|-------------|
| `document_id` | Google Doc ID (required) |
| `tab_id` | Tab identifier (empty string for single-tab) |

### New: TabNotFoundError exception

| Field | Description |
|-------|-------------|
| `tab_id` | The requested tab_id that was not found |
| `available_tabs` | List of `(tab_id, title, index)` tuples |

### Updated: MultipleTabsError exception

| Field | Description |
|-------|-------------|
| `tab_count` | Number of tabs (existing) |
| `available_tabs` | List of `(tab_id, title, index)` tuples (new) |

## No New Persistence

No database, files, or state changes. All data comes from the Google Docs API at request time.
