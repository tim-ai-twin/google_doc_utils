# Data Model: Google Docs to Markdown Converter

**Feature**: 126-gdoc-markdown-converter
**Date**: 2026-01-09

## Core Entities

### TabReference

Identifies a specific tab within a Google Doc.

```python
@dataclass
class TabReference:
    document_id: str          # Google Doc ID (from URL)
    tab_id: str = ""          # Tab ID (empty string = single-tab default)

    def validate(self) -> None:
        """Raises ValueError if document_id is empty."""
        if not self.document_id:
            raise ValueError("document_id is required")
```

**Validation Rules**:
- `document_id` is required (non-empty)
- `tab_id` may be empty for single-tab documents
- If document has multiple tabs and `tab_id` is empty, operations raise `MultipleTabsError`

---

### HeadingAnchor

A heading in the document with its anchor ID.

```python
@dataclass
class HeadingAnchor:
    anchor_id: str            # Google Docs headingId (e.g., "h.abc123")
    level: int                # 1-6 for Heading 1-6
    text: str                 # Heading text content
    start_index: int          # Character position in document
```

**Relationships**:
- Belongs to a Tab
- Defines Section boundaries

**State Transitions**: N/A (read-only from Google Docs)

---

### Section

A portion of a document from one heading to the next same-or-higher level heading.

```python
@dataclass
class Section:
    anchor_id: str            # Heading anchor ID (empty = preamble)
    level: int                # Heading level (0 = preamble)
    start_index: int          # Start character index (inclusive)
    end_index: int            # End character index (exclusive)

    @property
    def is_preamble(self) -> bool:
        return self.anchor_id == ""
```

**Boundary Rules**:
- Preamble: index 0 to first heading's start_index
- Section: heading start_index to next same-or-higher heading's start_index
- Last section: heading start_index to document end

---

### EmbeddedObject

An opaque object preserved through conversion.

```python
@dataclass
class EmbeddedObject:
    object_id: str | None     # ID (None for equations)
    object_type: EmbeddedObjectType
    start_index: int          # Position in document

class EmbeddedObjectType(Enum):
    IMAGE = "image"
    DRAWING = "drawing"
    CHART = "chart"
    EQUATION = "equation"
    VIDEO = "video"
    EMBED = "embed"           # Generic/unknown
```

**Type Detection** (from Google Docs API):

| Type | API Detection |
|------|---------------|
| IMAGE | `embeddedObject.imageProperties` present, no `linkedContentReference` |
| DRAWING | `embeddedObject.embeddedDrawingProperties` present |
| CHART | `embeddedObject.linkedContentReference.sheetsChartReference` present |
| EQUATION | `element.equation` present (no ID) |
| VIDEO | `richLink` with YouTube URL |
| EMBED | Fallback for unknown types |

**Special Case - Equations**:
- Equations have NO object ID in Google Docs API
- Must be matched by position during import
- Placeholder format: `{^= equation}` (no ID)

---

### Anchor

A position marker for comments, bookmarks, or headings.

```python
@dataclass
class Anchor:
    anchor_id: str            # Unique ID
    anchor_type: AnchorType
    start_index: int

class AnchorType(Enum):
    HEADING = "heading"       # From paragraphStyle.headingId
    BOOKMARK = "bookmark"     # From namedRanges or bookmarks
    COMMENT = "comment"       # From comment anchors
```

---

### FormattingSpan

A contiguous span with uniform formatting.

```python
@dataclass
class FormattingSpan:
    start_index: int
    end_index: int
    formatting: TextFormatting

@dataclass
class TextFormatting:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False      # Not supported in MEBDF
    highlight_color: str | None = None  # e.g., "yellow" or "#ffff00"
    text_color: str | None = None       # e.g., "#cc0000"
    font_family: str | None = None      # e.g., "Roboto Mono"
    is_monospace: bool = False
```

**MEBDF Mapping**:
- `bold` → `**text**`
- `italic` → `*text*`
- `underline` → `{!underline}text{/!}`
- `highlight_color` → `{!highlight:color}text{/!}`
- `text_color` → `{!color:#hex}text{/!}`
- `is_monospace` → `{!mono}text{/!}` or `{!mono}` block

---

### BlockFormatting

Paragraph-level formatting state.

```python
@dataclass
class BlockFormatting:
    named_style: str | None = None    # e.g., "Normal text", "Heading 1"
    font_family: str | None = None
    font_weight: str | None = None    # e.g., "Light", "Bold"
    font_size: str | None = None      # e.g., "12pt"
    text_color: str | None = None
    alignment: str | None = None      # "left", "center", "right", "justify"
    indent_left: str | None = None    # e.g., "0.5in"
    indent_right: str | None = None
    line_spacing: str | None = None   # "single", "1.5", "double"
    space_before: str | None = None   # e.g., "12pt"
    space_after: str | None = None
```

---

## Conversion Results

### ExportResult

Result of converting Google Doc → MEBDF.

```python
@dataclass
class ExportResult:
    content: str              # MEBDF markdown content
    anchors: list[Anchor]     # All anchors found
    embedded_objects: list[EmbeddedObject]  # Objects to preserve
    warnings: list[str]       # Non-fatal issues (unsupported formatting, etc.)
```

### ImportResult

Result of converting MEBDF → Google Doc.

```python
@dataclass
class ImportResult:
    requests: list[dict]      # Google Docs API batchUpdate requests
    preserved_objects: list[str]  # Object IDs that were preserved
    warnings: list[str]       # Non-fatal issues
```

---

### HierarchyResult

Result of hierarchy extraction.

```python
@dataclass
class HierarchyResult:
    headings: list[HeadingAnchor]
    content: str              # Pure markdown hierarchy (# lines only)
```

---

## Entity Relationships

```
TabReference
    │
    ├── contains → Section (0..n)
    │                 │
    │                 ├── has → HeadingAnchor (0..1, None for preamble)
    │                 └── contains → Content with:
    │                                  ├── FormattingSpan (0..n)
    │                                  ├── EmbeddedObject (0..n)
    │                                  └── Anchor (0..n)
    │
    └── has → BlockFormatting (stateful, changes at boundaries)
```

---

## Validation Rules Summary

| Entity | Rule | Error |
|--------|------|-------|
| TabReference | `document_id` required | `ValueError` |
| TabReference | `tab_id` empty + multiple tabs | `MultipleTabsError` |
| Section | `anchor_id` must exist or be empty | `AnchorNotFoundError` |
| EmbeddedObject | ID required except for equations | N/A (equations use position) |
| MEBDF syntax | Must parse without errors | `MebdfParseError` |
| Embedded placeholder | ID must exist in document | `EmbeddedObjectNotFoundError` |
