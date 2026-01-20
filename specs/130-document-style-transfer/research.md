# Research: Document Style Transfer

**Feature**: 130-document-style-transfer
**Date**: 2026-01-19
**Prior Research**: See [129-document-level-styles/research.md](../129-document-level-styles/research.md) for API details

## Research Questions

### 1. How to read effective/visible styles (not just definitions)?

**Decision**: Analyze actual paragraphs in the document to determine what users see.

**Rationale**: The spec requires capturing "effective styles"—what the user actually sees. This differs from named style definitions when paragraphs have inline overrides.

**Approach**:
1. Iterate through `document.body.content` to find all paragraphs
2. Group paragraphs by their `namedStyleType` (HEADING_1, NORMAL_TEXT, etc.)
3. For each style type with paragraphs:
   - Extract the paragraph's resolved text and paragraph styles
   - Use first paragraph of that type as the representative effective style
   - Alternative: Use most common formatting if paragraphs differ (implementation choice per edge case)
4. For style types with no paragraphs: Fall back to named style definition

**API Fields Needed**:
```python
# From paragraph element
paragraph.paragraphStyle.namedStyleType  # e.g., "HEADING_1"
paragraph.paragraphStyle.*  # Resolved paragraph properties
paragraph.elements[].textRun.textStyle.*  # Resolved text properties
```

**Alternatives Considered**:
- Only read named style definitions → Rejected: Doesn't capture user's actual visual experience
- Read all paragraphs and compute average → Rejected: Over-complicated, edge case says first/most-common is acceptable

### 2. How to apply styles when UpdateNamedStyles doesn't exist?

**Decision**: "Style flattening"—apply source style properties inline to every paragraph of matching type in target.

**Rationale**: Google Docs API has no `UpdateNamedStyleRequest` (confirmed in prior research). The only way to change how a paragraph looks is to apply formatting inline via `updateParagraphStyle` and `updateTextStyle`.

**Approach**:
1. Read effective styles from source document (per Question 1)
2. In target document, find all paragraphs of each style type
3. For each target paragraph:
   - Apply text style properties: `updateTextStyle` with range covering paragraph
   - Apply paragraph style properties: `updateParagraphStyle` with same range
4. Batch all requests into single `batchUpdate` call for efficiency

**Request Structure**:
```python
requests = []
for para_range in target_paragraphs_of_type:
    # Apply paragraph-level formatting
    requests.append({
        'updateParagraphStyle': {
            'range': para_range,
            'paragraphStyle': source_effective_style.paragraph_style,
            'fields': 'alignment,lineSpacing,spaceAbove,spaceBelow,indentStart,indentEnd,indentFirstLine'
        }
    })
    # Apply text-level formatting (excluding character overrides)
    requests.append({
        'updateTextStyle': {
            'range': para_range,
            'textStyle': source_effective_style.text_style,
            'fields': 'fontSize,weightedFontFamily,foregroundColor,backgroundColor,bold,italic,underline'
        }
    })
```

**Alternatives Considered**:
- Google Apps Script → Rejected: Adds complexity, different auth model
- Copy document and modify → Rejected: User wants to update existing target

### 3. How to preserve character-level inline overrides in target?

**Decision**: Apply paragraph-level text style using paragraph range, not character range.

**Rationale**: FR-016 requires preserving inline formatting (e.g., a bold word within a heading). When `updateTextStyle` is applied to a paragraph range, it sets the default text style for that paragraph but preserves explicit character-level overrides.

**Key Insight**: Google Docs text style inheritance:
```
Named style default
    ↓
Paragraph text style default (what we set)
    ↓
Character-level explicit formatting (preserved)
```

When we apply `updateTextStyle` to a paragraph, we're setting the paragraph's default text style. Any text that was explicitly formatted (e.g., a bold word) retains its explicit formatting because explicit overrides take precedence.

**Verification**: This matches how Google Docs UI works—changing a heading style doesn't remove bold words within the heading.

### 4. How to handle document-level properties (background, margins, page size)?

**Decision**: Use `UpdateDocumentStyle` request (fully supported by API).

**Rationale**: Unlike named styles, document-level properties can be both read and written.

**API Pattern**:
```python
# Read
doc_style = document.get('documentStyle', {})
background = doc_style.get('background', {})
margins = {
    'top': doc_style.get('marginTop'),
    'bottom': doc_style.get('marginBottom'),
    'left': doc_style.get('marginLeft'),
    'right': doc_style.get('marginRight'),
}
page_size = doc_style.get('pageSize', {})

# Write
requests = [{
    'updateDocumentStyle': {
        'documentStyle': {
            'background': source_background,
            'marginTop': source_margins['top'],
            'marginBottom': source_margins['bottom'],
            'marginLeft': source_margins['left'],
            'marginRight': source_margins['right'],
            'pageSize': source_page_size
        },
        'fields': 'background,marginTop,marginBottom,marginLeft,marginRight,pageSize'
    }
}]
```

### 5. How to handle colors (theme vs RGB)?

**Decision**: Convert all colors to explicit RGB values.

**Rationale**: Per edge case in spec—theme colors depend on document theme which may differ between source and target. RGB values are universal.

**Conversion**:
```python
def extract_rgb_color(color_obj):
    """Extract RGB from any color structure."""
    if not color_obj:
        return None

    # Handle nested color structure
    color = color_obj.get('color', color_obj)
    if 'rgbColor' in color:
        rgb = color['rgbColor']
        return {
            'red': rgb.get('red', 0),
            'green': rgb.get('green', 0),
            'blue': rgb.get('blue', 0)
        }
    # Theme colors - read resolved value from API response (already RGB)
    return None
```

### 6. What text/paragraph properties to capture for effective styles?

**Decision**: Capture all properties listed in FR-012 and FR-013.

**Text Style Properties** (FR-012):
- `fontSize` - Font size in points
- `weightedFontFamily.fontFamily` - Font family name
- `weightedFontFamily.weight` - Font weight (100-900)
- `foregroundColor` - Text color (RGB)
- `backgroundColor` - Highlight color (RGB)
- `bold` - Boolean
- `italic` - Boolean
- `underline` - Boolean

**Paragraph Style Properties** (FR-013):
- `alignment` - START, CENTER, END, JUSTIFIED
- `lineSpacing` - Multiplier (100 = single spacing)
- `spaceAbove` - Space before in points
- `spaceBelow` - Space after in points
- `indentStart` - Left indent
- `indentEnd` - Right indent
- `indentFirstLine` - First line indent

**Explicitly Excluded** (FR-028-030):
- `smallCaps`
- `baselineOffset` (superscript/subscript)
- `strikethrough`

### 7. How to structure MCP tool responses?

**Decision**: Return structured JSON with clear property names matching spec terminology.

**get_document_styles Response**:
```json
{
  "document_properties": {
    "background_color": "#f5f5f5",
    "margin_top_pt": 72,
    "margin_bottom_pt": 72,
    "margin_left_pt": 72,
    "margin_right_pt": 72,
    "page_width_pt": 612,
    "page_height_pt": 792
  },
  "effective_styles": {
    "NORMAL_TEXT": {
      "text": {
        "font_family": "Arial",
        "font_size_pt": 11,
        "font_weight": 400,
        "text_color": "#000000",
        "highlight_color": null,
        "bold": false,
        "italic": false,
        "underline": false
      },
      "paragraph": {
        "alignment": "START",
        "line_spacing": 1.15,
        "space_before_pt": 0,
        "space_after_pt": 0,
        "indent_start_pt": 0,
        "indent_end_pt": 0,
        "first_line_indent_pt": 0
      },
      "source": "paragraph_sample"  // or "style_definition"
    },
    "HEADING_1": { ... },
    // ... all 9 style types
  }
}
```

**apply_document_styles Response**:
```json
{
  "success": true,
  "document_properties_applied": true,
  "styles_applied": {
    "HEADING_1": {"paragraphs_updated": 3},
    "HEADING_2": {"paragraphs_updated": 5},
    "NORMAL_TEXT": {"paragraphs_updated": 42}
  },
  "total_paragraphs_updated": 50
}
```

## Best Practices Applied

### Google Docs API
- Batch requests for efficiency (single `batchUpdate` call)
- Use `fields` mask to specify exactly what to update
- Handle API errors gracefully with clear messages

### Python Project Patterns
- Follow existing `types.py` pattern for data classes
- Use dataclasses with `@dataclass(frozen=True)` for immutable style objects
- Follow existing converter module organization

### Testing
- Unit tests with mocked API responses (tier_a)
- Integration tests with real API calls (tier_b)
- Round-trip tests verifying style fidelity

## Summary of Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Read effective styles | Analyze actual paragraphs | Captures what user sees, not just definitions |
| Apply styles without UpdateNamedStyles | Style flattening (inline) | Only available approach |
| Preserve inline overrides | Paragraph-range text style | Google Docs inheritance model preserves explicit formatting |
| Document properties | UpdateDocumentStyle | Fully supported by API |
| Color handling | Convert to RGB | Theme colors not portable |
| Properties to capture | FR-012 + FR-013 lists | Comprehensive set per spec |
| MCP response format | Structured JSON | Clear, LLM-friendly |
