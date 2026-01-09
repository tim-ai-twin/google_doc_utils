# Quickstart: Google Docs to Markdown Converter

## Overview

The converter provides bidirectional conversion between Google Docs and MEBDF (Markdown Extensions for Basic Doc Formatting) v1.4. It operates at the **tab level** and supports section-level operations via heading anchors.

## Installation

```python
# The converter is part of the extended_google_doc_utils package
from extended_google_doc_utils.converter import GoogleDocsConverter
from extended_google_doc_utils.auth import CredentialManager
```

## Basic Usage

### 1. Initialize the Converter

```python
from extended_google_doc_utils.converter import GoogleDocsConverter, TabReference
from extended_google_doc_utils.auth import CredentialManager

# Get credentials (OAuth flow)
creds = CredentialManager.load_credentials()

# Create converter instance
converter = GoogleDocsConverter(credentials=creds)

# Reference a document tab
tab = TabReference(
    document_id="1ABC123...",  # From Google Doc URL
    tab_id=""                   # Empty for single-tab docs
)
```

### 2. Get Document Hierarchy

Before editing, get the document structure to find section anchors:

```python
hierarchy = converter.get_hierarchy(tab)

print(hierarchy.markdown)
# Output:
# # {^ h.abc123}Introduction
# ## {^ h.def456}Background
# ## {^ h.ghi789}Methods
# ### {^ h.jkl012}Data Collection
# ## {^ h.mno345}Results
```

### 3. Export Content

**Export entire tab:**

```python
result = converter.export_tab(tab)
print(result.content)
# Full MEBDF markdown with all formatting and anchors
```

**Export a section:**

```python
# Export just the "Methods" section (includes subsections)
result = converter.export_section(tab, anchor_id="h.ghi789")
print(result.content)
# ## {^ h.ghi789}Methods
# Content here...
# ### {^ h.jkl012}Data Collection
# More content...
```

**Export preamble (content before first heading):**

```python
result = converter.export_section(tab, anchor_id="")  # Empty string
```

### 4. Import Content

**Replace entire tab:**

```python
mebdf_content = """
# {^ h.abc123}Introduction

This is the {!highlight:yellow}updated{/!} introduction.

{^= img_001 image}

More content with **bold** and *italic*.
"""

result = converter.import_tab(tab, content=mebdf_content)
if result.warnings:
    print("Warnings:", result.warnings)
```

**Replace a section:**

```python
# Update just the Methods section
new_methods = """
## {^ h.ghi789}Methods

Updated methodology description.

### {^ h.jkl012}Data Collection

New data collection process.
"""

result = converter.import_section(tab, anchor_id="h.ghi789", content=new_methods)
```

## MEBDF Format Reference

### Standard Markdown

All standard markdown is supported:
- `# Heading 1` through `###### Heading 6`
- `**bold**` and `*italic*`
- `[link text](url)`
- `- unordered` and `1. ordered` lists
- `` `inline code` ``

### Inline Formatting Extensions

```markdown
{!highlight:yellow}highlighted text{/!}
{!underline}underlined text{/!}
{!color:#cc0000}red text{/!}
{!mono}monospace text{/!}
{!highlight:yellow, underline}combined{/!}
```

### Block Formatting

Standalone line, applies until changed:

```markdown
{!mono}
This paragraph is monospace.
So is this one.

{!mono:false}
Back to normal.
```

### Anchors

```markdown
# {^ h.abc123}Heading with anchor
{^ bookmark_id}Text with bookmark anchor
{^}Text with proposed new anchor (server assigns ID)
```

### Embedded Objects

Objects are preserved as placeholders:

```markdown
{^= img_001 image}
{^= drw_002 drawing}
{^= cht_003 chart}
{^= equation}
{^= vid_004 video}
```

**Note**: Embedded objects must already exist in the document. Placeholders preserve them during round-trip editing - they cannot create new objects.

## Common Workflows

### AI-Assisted Editing

```python
# 1. Get structure
hierarchy = converter.get_hierarchy(tab)

# 2. Export section to edit
section = converter.export_section(tab, anchor_id="h.methods")

# 3. Send to LLM for editing
# ... LLM modifies the text but preserves:
#     - Heading anchors: {^ id}
#     - Embedded objects: {^= id type}
#     - Formatting markers: {!...}

# 4. Import modified section
converter.import_section(tab, anchor_id="h.methods", content=modified)
```

### Preserve Images While Editing Text

```python
# Export section with image
result = converter.export_section(tab, anchor_id="h.results")
# Content includes: {^= img_chart image}

# Edit text, keep the placeholder in same relative position
edited = result.content.replace(
    "old conclusion text",
    "new conclusion text"
)
# The {^= img_chart image} placeholder remains unchanged

# Import - image is preserved at its position
converter.import_section(tab, anchor_id="h.results", content=edited)
```

## Error Handling

```python
from extended_google_doc_utils.converter import (
    MultipleTabsError,
    AnchorNotFoundError,
    EmbeddedObjectNotFoundError,
    MebdfParseError,
)

try:
    result = converter.export_section(tab, anchor_id="h.unknown")
except MultipleTabsError as e:
    print(f"Specify tab_id - document has {e.tab_count} tabs")
except AnchorNotFoundError as e:
    print(f"Anchor '{e.anchor_id}' not found - re-fetch hierarchy")
except EmbeddedObjectNotFoundError as e:
    print(f"Object {e.object_id} ({e.object_type}) not in document")
except MebdfParseError as e:
    print(f"Invalid MEBDF at line {e.line}: {e}")
```

## Limitations

1. **Tab-level only**: Cannot process multiple tabs in one call (MEBDF has no tab boundary syntax)
2. **Embedded objects**: Preserved but not editable - cannot create new images via placeholder
3. **Equations**: No object ID - matched by position (may be fragile if multiple equations exist)
4. **Unsupported formatting**: Strikethrough, superscript, subscript pass through as plain text
5. **Heading anchors**: Can change if heading is copy-pasted (re-fetch hierarchy if anchor not found)
