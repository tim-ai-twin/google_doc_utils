# Quickstart: Google Docs MCP Server

Get started with the Google Docs MCP Server in 5 minutes.

## Prerequisites

1. **OAuth Credentials**: Run `python scripts/bootstrap_oauth.py` to set up Google API access
2. **Python 3.11+**: Required for the MCP SDK
3. **MCP Client**: Claude Desktop, Claude Code, or another MCP-compatible client

## Installation

```bash
# Install the MCP server (from project root)
pip install -e ".[mcp]"

# Or with uv
uv pip install -e ".[mcp]"
```

## Running the Server

### Option 1: Direct Execution

```bash
python -m extended_google_doc_utils.mcp.server
```

### Option 2: Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-docs": {
      "command": "python",
      "args": ["-m", "extended_google_doc_utils.mcp.server"],
      "cwd": "/path/to/google_doc_utils"
    }
  }
}
```

### Option 3: Claude Code Configuration

Add to your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "google-docs": {
      "command": "python",
      "args": ["-m", "extended_google_doc_utils.mcp.server"]
    }
  }
}
```

## Common Workflows

### 1. Update a Section in a Shared Document

```text
User: Update the "Status" section in my weekly report with these bullet points...

LLM workflow:
1. list_documents(query="weekly report") → find document_id
2. get_hierarchy(document_id) → find anchor_id for "Status" section
3. export_section(document_id, anchor_id) → get current content
4. import_section(document_id, anchor_id, new_content) → write updated section
```

### 2. Read a Specific Section

```text
User: What does the "Budget" section say?

LLM workflow:
1. get_hierarchy(document_id) → find anchor_id for "Budget"
2. export_section(document_id, anchor_id) → read section content
```

### 3. Clean Up Document Formatting

```text
User: Make my document use Arial 11pt throughout

LLM workflow:
1. normalize_formatting(document_id, body_font="Arial", body_size="11pt")
```

### 4. Match Another Document's Style

```text
User: Make this document look like our company template

LLM workflow:
1. extract_styles(template_document_id) → get template styles
2. apply_styles(target_document_id, styles) → apply to target
```

## MEBDF Content Format

Content is exchanged in MEBDF (Markdown Extensions for Basic Doc Formatting):

### Standard Markdown

```markdown
# Heading 1
## Heading 2

**Bold text** and *italic text*

- Bullet point
- Another point

1. Numbered item
2. Second item

[Link text](https://example.com)
```

### Formatting Extensions

```markdown
{!highlight:yellow}Highlighted text{/!}
{!underline}Underlined text{/!}
{!color:#cc0000}Red text{/!}
{!mono}Monospace text{/!}
```

### Anchors and Embedded Objects

```markdown
## {^ h.abc123}Section Heading

Text with an image: {^= obj123 image}
```

## Error Handling

All errors include actionable suggestions:

```json
{
  "success": false,
  "error": {
    "type": "AnchorNotFoundError",
    "message": "Section 'h.xyz789' not found in document",
    "suggestion": "Call get_hierarchy to see available sections"
  }
}
```

## Tips for LLMs

1. **Always call get_hierarchy first** before section operations
2. **Use import_section for targeted edits** instead of import_tab
3. **Preserve image placeholders** (`{^= id image}`) when editing around images
4. **Empty anchor_id** refers to content before the first heading (preamble)
5. **Empty tab_id** is valid for single-tab documents

## Tool Reference

### Navigation Tools

#### `list_documents(max_results?, query?)`
List Google Docs accessible to the current user.
- `max_results`: Maximum documents to return (default 25)
- `query`: Optional search term to filter by name

#### `get_metadata(document_id)`
Get document metadata including available tabs.
- Returns title, tabs list (with tab_id, title, index), permissions

#### `get_hierarchy(document_id, tab_id?)`
Get the heading structure of a document tab.
- Returns list of headings with anchor_id, level, text
- Call this BEFORE section operations

### Section Tools

#### `export_section(document_id, anchor_id, tab_id?)`
Export a specific section to MEBDF markdown.
- `anchor_id`: From get_hierarchy. Empty string for preamble.
- Returns section content in MEBDF format

#### `import_section(document_id, anchor_id, content, tab_id?)`
Replace a section's content with new MEBDF markdown.
- Only modifies the target section - other content unchanged
- Returns preserved_objects list

### Tab Tools

#### `export_tab(document_id, tab_id?)`
Export an entire document tab to MEBDF markdown.
- Returns full tab content with all formatting

#### `import_tab(document_id, content, tab_id?)`
Replace entire tab content with MEBDF markdown.
- WARNING: Replaces ALL content in the tab

### Formatting Tools

#### `normalize_formatting(document_id, tab_id?, body_font?, body_size?, heading_font?, line_spacing?, space_after?)`
Apply consistent formatting throughout a document.
- Only specified parameters are changed
- Embedded objects are preserved

#### `extract_styles(document_id, tab_id?)`
Extract formatting patterns from a source document.
- Returns list of style definitions for body and headings

#### `apply_styles(document_id, styles, tab_id?)`
Apply extracted styles to a target document.
- Use with extract_styles for style matching

## Troubleshooting

### "MultipleTabsError"

The document has multiple tabs. Call `get_metadata` to find tab IDs, then specify `tab_id` in your request.

### "AnchorNotFoundError"

The section anchor doesn't exist. Call `get_hierarchy` to see available anchors.

### "PermissionDeniedError"

You don't have edit access. Request access to the document or use a different account.

### "CredentialError"

OAuth credentials are not configured. Run `python scripts/bootstrap_oauth.py` to set up authentication.
