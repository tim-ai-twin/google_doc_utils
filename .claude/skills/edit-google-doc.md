# Edit Google Doc

Use this skill when the user wants to edit, update, or modify content in a Google Doc -- especially large documents where reading the entire document would be wasteful. This workflow uses targeted section reading and writing to efficiently locate and edit specific content.

## Single-Tab Workflow

### Step 1: Discover document structure

Call `get_metadata(document_id)` to learn the document title and available tabs.

- If the document has multiple tabs, switch to the **Multi-Tab Workflow** below.
- For single-tab documents, continue here.

### Step 2: Get the heading hierarchy

Call `get_hierarchy(document_id)` (or `get_hierarchy(document_id, tab_id)` if a specific tab).

This returns all headings with their `anchor_id`, heading level, text, and **word counts** per section. It also returns `total_word_count` for the entire tab.

### Step 3: Decision point -- small vs. large document

- If `total_word_count < 2000`: The document is small enough to read directly. Skip to **Step 6** and use `read_section` with the appropriate `anchor_id` to get the content you need. For very small docs you can also just use `read_tab` directly.
- If `total_word_count >= 2000`: The document is large. Continue to Step 4 to export and search.

### Step 4: Export tab to disk for searching

Call `read_tab(document_id, tab_id, format="plain")` to get the full content as plain markdown (no MEBDF markers, which makes searching easier).

Save the result to a temp file:

```
Use the Write tool to save content to /tmp/gdoc-{document_id}-{tab_id}.md
```

If `tab_id` is empty (single-tab doc), use `default` as the tab_id portion of the filename.

### Step 5: Search the exported file to find the target content

Use the **Grep** tool on `/tmp/gdoc-{document_id}-*.md` to find the text the user wants to edit. Then use the **Read** tool to view surrounding context and identify which section heading the target content falls under.

Match the heading text back to the hierarchy from Step 2 to get the `anchor_id`.

### Step 6: Read the target section in MEBDF format

Call `read_section(document_id, anchor_id, tab_id)` to get the MEBDF-formatted content for just the target section. This is the editable representation.

Review the MEBDF content and make the user's requested changes.

### Step 7: Write the edited section back

Call `write_section(document_id, anchor_id, content, tab_id)` with the modified MEBDF content.

The `content` parameter must include the section heading line. Only the target section is replaced; all other document content remains unchanged.

### Step 8: Clean up

Remove the temp file:

```bash
rm /tmp/gdoc-{document_id}-{tab_id}.md
```

---

## Multi-Tab Workflow

Use this when `get_metadata` reveals multiple tabs and the user hasn't specified which tab to edit, or the edit may span tabs.

### Step 1: Export all tabs

After `get_metadata` returns the list of tabs, export each tab to disk:

For each tab in the metadata response:
1. Call `read_tab(document_id, tab_id, format="plain")`
2. Save to `/tmp/gdoc-{document_id}-{tab_title}.md` (use the tab title, sanitized for filesystem safety -- replace spaces with hyphens, remove special characters)

### Step 2: Search across all exported tabs

Use **Grep** on `/tmp/gdoc-{document_id}-*.md` to search across all tabs at once. This identifies which tab contains the target content.

### Step 3: Identify the matching tab and section

From the Grep results, determine:
- Which tab file matched (extract tab title from filename)
- Map back to the `tab_id` from the metadata response
- Call `get_hierarchy(document_id, tab_id)` for that specific tab
- Identify the section heading the match falls under and get its `anchor_id`

### Step 4: Read, edit, and write

Follow Steps 6-7 from the Single-Tab Workflow using the identified `tab_id` and `anchor_id`.

### Step 5: Clean up all temp files

```bash
rm /tmp/gdoc-{document_id}-*.md
```

---

## Error Handling

- **Document not found**: Verify the document ID is correct. It's the long string after `/d/` in the Google Docs URL.
- **Permission denied**: The user needs at least edit access to the document. Ask them to check sharing settings.
- **Tab not found**: Call `get_metadata` again to verify available tab IDs. Tab IDs look like `t.0`, `t.1`, etc.
- **Section not found**: Call `get_hierarchy` again to verify the `anchor_id`. Anchor IDs look like `h.abc123`.
- **Write fails with formatting errors**: Check that the MEBDF content is well-formed. Common issues:
  - Unclosed formatting markers: every `{!...}` needs a matching `{/!}`
  - Missing section heading in the content passed to `write_section`

---

## MEBDF Formatting Quick Reference

When editing section content, use MEBDF (Markdown-Extended Bidirectional Document Format):

**Standard markdown** works as expected:
- `# Heading 1` through `###### Heading 6`
- `**bold**`, `*italic*`, `[link text](url)`, `` `inline code` ``
- `- bullet items`, `1. numbered items`

**MEBDF inline formatting** uses `{!property}text{/!}` syntax:
- `{!underline}text{/!}` -- underlined text
- `{!color:#FF0000}text{/!}` -- colored text (hex or named colors)
- `{!highlight:yellow}text{/!}` -- background highlight
- `{!font:Roboto}text{/!}` -- custom font
- `{!font:Roboto, weight:300}text{/!}` -- font with weight (100-900)
- `{!size:14pt}text{/!}` -- font size
- `{!mono}text{/!}` -- monospace font

**MEBDF paragraph formatting**:
- `{!align:center}text{/!}` -- alignment (left, center, right, justify)
- `{!line-spacing:1.5}text{/!}` -- line spacing
- `{!indent-left:0.5in}text{/!}` -- indentation

**Combine multiple properties**: `{!color:blue, size:16pt, align:center}text{/!}`

**Image placeholders**: `{^= objectId image}` -- preserve these when editing; do not remove or modify them.

**Anchor markers**: `{^ h.abc123}` at the start of headings -- preserve these; they link to the section's anchor ID.
