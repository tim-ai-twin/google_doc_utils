# Data Model: Google Docs MCP Server

**Feature Branch**: `127-gdoc-mcp-server`
**Date**: 2026-01-10

## Overview

This document defines the MCP tool interfaces, request/response schemas, and data types for the Google Docs MCP Server. Tools are organized into four categories matching the functional requirements.

## Tool Categories

### 1. Navigation Tools (FR-007 to FR-010)

#### `list_documents`

List Google Docs the user can access.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | No | Search query to filter documents (name contains) |
| `limit` | integer | No | Maximum results (default: 20, max: 100) |

**Response**:
```python
@dataclass
class DocumentSummary:
    document_id: str      # Google Doc ID
    title: str            # Document title
    last_modified: str    # ISO 8601 timestamp
    owner: str            # Owner email

@dataclass
class ListDocumentsResponse:
    success: bool
    documents: list[DocumentSummary]
    total_count: int      # Total matching (may exceed limit)
```

---

#### `get_metadata`

Get document metadata including tabs and permissions.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID from document URL |

**Response**:
```python
@dataclass
class TabInfo:
    tab_id: str           # Tab identifier
    title: str            # Tab title
    index: int            # Tab position (0-based)

@dataclass
class DocumentMetadata:
    success: bool
    document_id: str
    title: str
    tabs: list[TabInfo]
    can_edit: bool        # User has edit permission
    can_comment: bool     # User has comment permission
```

---

#### `get_hierarchy`

Get the heading structure of a document tab.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID |
| `tab_id` | string | No | Tab ID for multi-tab docs. Empty for single-tab. |

**Response**:
```python
@dataclass
class HeadingInfo:
    anchor_id: str        # Use this for section operations
    level: int            # 1-6 (H1-H6)
    text: str             # Heading text content

@dataclass
class HierarchyResponse:
    success: bool
    headings: list[HeadingInfo]
    markdown: str         # Pure markdown hierarchy (# lines with anchors)
```

---

### 2. Section Tools (FR-011 to FR-013)

#### `export_section`

Export a specific section to MEBDF markdown.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID |
| `anchor_id` | string | Yes | Heading anchor ID from get_hierarchy. Empty string for preamble. |
| `tab_id` | string | No | Tab ID for multi-tab docs. Empty for single-tab. |

**Response**:
```python
@dataclass
class ExportSectionResponse:
    success: bool
    content: str          # MEBDF markdown content
    anchor_id: str        # Echo back for confirmation
    warnings: list[str]   # Non-fatal issues (e.g., unsupported formatting)
```

---

#### `import_section`

Replace a section's content with new MEBDF markdown.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID |
| `anchor_id` | string | Yes | Heading anchor ID. Empty string for preamble. |
| `content` | string | Yes | MEBDF markdown to write |
| `tab_id` | string | No | Tab ID for multi-tab docs. Empty for single-tab. |

**Response**:
```python
@dataclass
class ImportSectionResponse:
    success: bool
    anchor_id: str        # Echo back for confirmation
    preserved_objects: list[str]  # Object IDs that were preserved
    warnings: list[str]   # Non-fatal issues
```

---

### 3. Tab Tools (FR-014 to FR-015)

#### `export_tab`

Export an entire tab to MEBDF markdown.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID |
| `tab_id` | string | No | Tab ID for multi-tab docs. Empty for single-tab. |

**Response**:
```python
@dataclass
class ExportTabResponse:
    success: bool
    content: str          # Full MEBDF markdown
    tab_id: str           # Echo back (resolved if empty)
    warnings: list[str]
```

---

#### `import_tab`

Replace entire tab content with MEBDF markdown.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID |
| `content` | string | Yes | MEBDF markdown to write |
| `tab_id` | string | No | Tab ID for multi-tab docs. Empty for single-tab. |

**Response**:
```python
@dataclass
class ImportTabResponse:
    success: bool
    tab_id: str           # Echo back
    preserved_objects: list[str]
    warnings: list[str]
```

---

### 4. Formatting Tools (FR-016 to FR-021)

#### `normalize_formatting`

Apply consistent formatting throughout a document.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Google Doc ID |
| `tab_id` | string | No | Tab ID for multi-tab docs |
| `body_font` | string | No | Font family for body text (e.g., "Arial") |
| `body_size` | string | No | Font size for body text (e.g., "11pt") |
| `heading_font` | string | No | Font family for headings |
| `line_spacing` | string | No | Line spacing ("single", "1.5", "double") |
| `space_after` | string | No | Space after paragraphs (e.g., "6pt") |

**Response**:
```python
@dataclass
class NormalizeFormattingResponse:
    success: bool
    changes_made: int     # Number of formatting changes applied
    warnings: list[str]   # e.g., unsupported formatting preserved
```

---

#### `extract_styles`

Extract formatting patterns from a source document.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Source document ID |
| `tab_id` | string | No | Tab ID for multi-tab docs |

**Response**:
```python
@dataclass
class StyleDefinition:
    element_type: str     # "body", "heading1", "heading2", etc.
    font_family: str | None
    font_size: str | None
    font_weight: str | None
    text_color: str | None
    line_spacing: str | None
    space_before: str | None
    space_after: str | None

@dataclass
class ExtractStylesResponse:
    success: bool
    styles: list[StyleDefinition]
    source_document_id: str
```

---

#### `apply_styles`

Apply extracted styles to a target document.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | string | Yes | Target document ID |
| `styles` | list[dict] | Yes | Style definitions from extract_styles |
| `tab_id` | string | No | Tab ID for multi-tab docs |

**Response**:
```python
@dataclass
class ApplyStylesResponse:
    success: bool
    changes_made: int
    warnings: list[str]
```

---

## Error Response Schema

All tools return structured errors on failure:

```python
@dataclass
class ErrorDetail:
    type: str             # Error class name (e.g., "AnchorNotFoundError")
    message: str          # Human-readable description
    suggestion: str | None # How to fix the issue

@dataclass
class ErrorResponse:
    success: bool = False
    error: ErrorDetail
```

### Error Types

| Type | When | Suggestion |
|------|------|------------|
| `DocumentNotFoundError` | Document ID invalid or not accessible | Verify document ID from URL |
| `PermissionDeniedError` | User lacks required permissions | Request access or use different account |
| `MultipleTabsError` | tab_id required but not provided | Call get_metadata to find tab IDs |
| `AnchorNotFoundError` | anchor_id doesn't exist | Call get_hierarchy to see available anchors |
| `MebdfParseError` | Invalid MEBDF syntax in content | Check MEBDF format specification |
| `EmbeddedObjectNotFoundError` | Placeholder references missing object | Object ID must exist in document |

---

## Key Entities (from spec)

| Entity | Description | Identifier |
|--------|-------------|------------|
| **Document** | A Google Doc | `document_id` (from URL) |
| **Tab** | A tab within a document | `tab_id` (from get_metadata) |
| **Section** | Content between headings | `anchor_id` (from get_hierarchy) |
| **Anchor** | Heading/bookmark/comment position | `anchor_id` string |
| **FormattingPattern** | Extracted style definition | `StyleDefinition` object |

---

## MEBDF Content Format

All content exchange uses MEBDF (Markdown Extensions for Basic Doc Formatting).

**Standard Markdown**:
- Headings: `# H1`, `## H2`, etc.
- Bold/Italic: `**bold**`, `*italic*`
- Lists: `- item`, `1. item`
- Links: `[text](url)`

**Extensions**:
- Highlight: `{!highlight:yellow}text{/!}`
- Underline: `{!underline}text{/!}`
- Color: `{!color:#cc0000}text{/!}`
- Monospace: `{!mono}text{/!}`
- Anchors: `{^ anchor_id}` (in headings: `## {^ h.abc123}Heading`)
- Embedded objects: `{^= object_id image}`
