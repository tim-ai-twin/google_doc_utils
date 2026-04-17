# Claude Code Skill Contract: Edit Google Document

## Skill Definition

**File**: `.claude/skills/edit-google-doc.md`
**Trigger**: User invokes `/edit-google-doc` or asks to edit a large Google Doc

## Workflow Steps

### Step 1: Discover document structure
```
MCP call: get_metadata(document_id)
→ Shows tabs to user
→ User selects tab (or auto-select if single-tab)
```

### Step 2: Get hierarchy with sizes
```
MCP call: get_hierarchy(document_id, tab_id)
→ Shows headings with word counts
→ User identifies target area or describes what to find
```

### Step 3: Export tab to disk (for large tabs)
```
MCP call: read_tab(document_id, tab_id, format="plain")
→ Content enters context temporarily
Write tool: write content to /tmp/gdoc-{doc_id}-{tab_id}.md
→ Content now on disk, LLM works from file
```

### Step 4: Search on disk
```
Grep tool: search exported file for target content
Read tool: read surrounding context if needed
→ Identify section heading / anchor_id from hierarchy
```

### Step 5: Read target section (MEBDF)
```
MCP call: read_section(document_id, anchor_id, tab_id)
→ MEBDF content for just the target section enters context
→ LLM understands formatting to preserve/modify
```

### Step 6: Write edited section
```
MCP call: write_section(document_id, anchor_id, content, tab_id)
→ Only target section modified
→ Confirm success
```

### Step 7: Cleanup
```
Bash tool: rm /tmp/gdoc-{doc_id}-{tab_id}.md
→ Temp file removed
```

## Decision Points

- **Skip Step 3-4** if hierarchy shows the document is small (< 2000 words total) — just use read_section directly
- **Repeat Step 3-4** for each tab if searching across multiple tabs
- **Skip Step 3** if user already knows the section anchor from a previous hierarchy call

## Error Handling

- If `get_metadata` fails (permissions, invalid ID): report error, stop workflow
- If `read_tab` returns large content: proceed to write to disk immediately
- If `write_section` fails: show error, suggest user check document permissions
- If temp file already exists: overwrite (idempotent)
