# Quickstart: Document Style Transfer

**Feature**: 130-document-style-transfer
**Date**: 2026-01-19

## Overview

This feature enables reading and applying document styles between Google Docs. It captures "effective styles"—what the user actually sees—and transfers them to another document.

## Python API Usage

### Read Styles from a Document

```python
from extended_google_doc_utils.converter import read_document_styles
from extended_google_doc_utils.converter.types import NamedStyleType

# Read complete style information
styles = read_document_styles("1abc...source_doc_id")

# Access document-level properties
print(f"Background: {styles.document_properties.background_color}")
print(f"Top margin: {styles.document_properties.margin_top_pt}pt")

# Access effective styles for any of the 9 types
heading1 = styles.effective_styles[NamedStyleType.HEADING_1]
print(f"Heading 1 font: {heading1.text_style.font_family}")
print(f"Heading 1 size: {heading1.text_style.font_size_pt}pt")
print(f"Source: {heading1.source}")  # "paragraph_sample" or "style_definition"
```

### Transfer Styles Between Documents

```python
from extended_google_doc_utils.converter import apply_document_styles

# Apply all styles from source to target
result = apply_document_styles(
    source_document_id="1abc...source",
    target_document_id="2xyz...target"
)

print(f"Success: {result.success}")
print(f"Paragraphs updated: {result.total_paragraphs_updated}")

# See breakdown by style type
for style_type, app_result in result.styles_applied.items():
    print(f"  {style_type.value}: {app_result.paragraphs_updated} paragraphs")
```

### Transfer Only Specific Parts

```python
from extended_google_doc_utils.converter import (
    apply_document_styles,
    apply_document_properties,
    apply_effective_styles,
)
from extended_google_doc_utils.converter.types import StyleTransferOptions, NamedStyleType

# Option 1: Only document properties (background, margins, page size)
apply_document_properties("source_id", "target_id")

# Option 2: Only named styles (not document properties)
results = apply_effective_styles("source_id", "target_id")

# Option 3: Only specific style types
results = apply_effective_styles(
    "source_id",
    "target_id",
    style_types=[NamedStyleType.HEADING_1, NamedStyleType.HEADING_2]
)

# Option 4: Using options for full control
result = apply_document_styles(
    "source_id",
    "target_id",
    options=StyleTransferOptions(
        include_document_properties=False,
        include_effective_styles=True,
        style_types=[NamedStyleType.NORMAL_TEXT, NamedStyleType.HEADING_1]
    )
)
```

## MCP Server Usage

### Get Styles (for LLM workflows)

```
Tool: get_document_styles
Input: { "document_id": "1abc...xyz" }

Response:
{
  "document_properties": {
    "background_color": "#f5f5f5",
    "margin_top_pt": 72.0,
    ...
  },
  "effective_styles": {
    "NORMAL_TEXT": {
      "text": { "font_family": "Arial", "font_size_pt": 11.0, ... },
      "paragraph": { "alignment": "START", "line_spacing": 1.15, ... },
      "source": "paragraph_sample"
    },
    "HEADING_1": { ... },
    ...
  }
}
```

### Apply Styles (for "Make this match that" requests)

```
Tool: apply_document_styles
Input: {
  "source_document_id": "1abc...source",
  "target_document_id": "2xyz...target",
  "include_document_properties": true,
  "include_effective_styles": true
}

Response:
{
  "success": true,
  "document_properties_applied": true,
  "styles_applied": {
    "HEADING_1": { "paragraphs_updated": 3 },
    "NORMAL_TEXT": { "paragraphs_updated": 42 }
  },
  "total_paragraphs_updated": 45,
  "errors": []
}
```

## Common Workflows

### "Apply the styles from document A to document B"

```python
from extended_google_doc_utils.converter import apply_document_styles

result = apply_document_styles(
    source_document_id="doc_a_id",
    target_document_id="doc_b_id"
)

if result.success:
    print(f"Transferred styles to {result.total_paragraphs_updated} paragraphs")
else:
    print(f"Errors: {result.errors}")
```

### "What styles does this document use?"

```python
from extended_google_doc_utils.converter import read_document_styles
from extended_google_doc_utils.converter.types import NamedStyleType

styles = read_document_styles("doc_id")

# Document properties
props = styles.document_properties
print(f"Page: {props.page_width_pt}×{props.page_height_pt}pt")
print(f"Margins: T={props.margin_top_pt}, B={props.margin_bottom_pt}")

# Named styles
for style_type in NamedStyleType:
    style = styles.effective_styles[style_type]
    text = style.text_style
    print(f"{style_type.value}: {text.font_family} {text.font_size_pt}pt")
```

### "Make all my headings match this document's style"

```python
from extended_google_doc_utils.converter import apply_effective_styles
from extended_google_doc_utils.converter.types import NamedStyleType

heading_types = [
    NamedStyleType.HEADING_1,
    NamedStyleType.HEADING_2,
    NamedStyleType.HEADING_3,
    NamedStyleType.HEADING_4,
    NamedStyleType.HEADING_5,
    NamedStyleType.HEADING_6,
]

results = apply_effective_styles(
    source_document_id="template_doc",
    target_document_id="my_doc",
    style_types=heading_types
)

total = sum(r.paragraphs_updated for r in results.values())
print(f"Updated {total} heading paragraphs")
```

## Important Notes

### Effective Styles vs Style Definitions

The system captures **what the user sees**, not just style definitions:

- If HEADING_1 paragraphs use the default style → returns style definition values
- If HEADING_1 paragraphs are manually formatted to "Roboto 20pt blue" → returns "Roboto 20pt blue"

This enables true "copy what I see" behavior.

### Style Flattening

Google Docs API doesn't support updating named style definitions. Instead, this feature applies formatting **inline** to each paragraph. The result looks the same, but:

- Target document's style definitions remain unchanged
- Using "Update heading to match" in Google Docs UI would revert to target's definition

### Preserved Formatting

When applying styles, character-level overrides in the target are preserved:

- A **bold word** within a heading stays bold
- Inline links remain intact
- Character-level color overrides are kept
