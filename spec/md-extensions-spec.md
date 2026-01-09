# Markdown Extensions Specification

**Version:** 1.4 Draft
**Scope:** MEBDF (Basic Doc Formatting) & MEA (Anchors)

These extensions augment standard markdown for round-trip editing of rich documents. They are designed for LLM readability, minimal verbosity, and preservation of formatting and anchored elements through edits.

---

## MEBDF: Markdown Extensions for Basic Doc Formatting

### Formatting Syntax

All formatting uses the `{! }` syntax. Inline or block is determined by structure:

| Pattern | Type | Behavior |
|---------|------|----------|
| `{!props}text{/!}` | Inline | Applies to wrapped text only |
| `{!props}` | Block | Standalone line, stateful until changed |

**Spacing is optional.** These are equivalent:

```markdown
{!mono}
{! mono}
{! mono }
```

---

### Property Types

#### Value Properties

Require a value after the colon.

```markdown
{!color:#cc0000}text{/!}
{!highlight:yellow}text{/!}
{!font:Roboto}
```

#### Boolean Properties

No value means `true`. Explicit `true` or `false` supported.

| Syntax | Meaning |
|--------|---------|
| `{!underline}` | underline: true |
| `{!underline:true}` | underline: true |
| `{!underline:false}` | underline: false |

Boolean properties: `underline`, `mono`

---

### Inline Formatting

Inline extensions wrap text spans. Multiple properties can be combined.

**Syntax:** `{!props}text{/!}`

#### Highlight

```markdown
The deadline is {!highlight:yellow}absolutely firm{/!} and cannot move.
We may have {!highlight:red}budget concerns{/!} to address.
Please review the {!highlight:green}approved sections{/!} first.
```

#### Underline

```markdown
The {!underline}key takeaway{/!} is that we must act now.
Please {!underline}sign and date{/!} the bottom of the form.
This {!underline}supersedes{/!} all previous agreements.
```

#### Text Color

```markdown
Status: {!color:#cc0000}At Risk{/!}
Status: {!color:#00aa00}On Track{/!}
The {!color:#0066cc}Q3 deliverables{/!} are listed below.
```

#### Monospace

```markdown
Run the {!mono}deploy.sh{/!} script to begin.
Set {!mono}DEBUG=true{/!} in your environment.
The {!mono}user_id{/!} field is required.
```

#### Combined Properties

```markdown
This is {!highlight:yellow, underline}critically important{/!} information.
Check the {!mono, color:#cc0000}error.log{/!} file immediately.
The {!underline, color:#0066cc}terms of service{/!} have changed.
```

---

### Block Formatting

Block formatting applies to all following content until changed. The directive appears alone on its own line.

**Syntax:** `{!props}`

#### Named Style

```markdown
{!Normal text}
This paragraph uses the document's default body style.
All subsequent paragraphs use Normal text until changed.
No per-paragraph annotations needed.
```

#### Custom Properties

```markdown
{!font:Roboto, weight:Light, size:12pt, color:#555555}
This paragraph has custom formatting applied.
So does this one—the format is stateful.
It continues until another directive appears.
```

#### Monospace Block

```markdown
{!mono}
AUTHORIZATION_ENDPOINT=https://auth.example.com
CLIENT_ID=abc123
REDIRECT_URI=https://app.example.com/callback
```

#### Turning Off Boolean Properties

```markdown
{!mono}
This is monospace.
So is this.

{!mono:false}
Back to regular text.
```

#### Full Property Example

```markdown
{!font:Roboto, weight:Light, size:12pt, color:#555555, align:justify, indent-left:0.5in, indent-right:0.5in, line-spacing:1.5, space-after:12pt}
This is a formatted block quote with full styling.
Readable property names matching the Google Docs GUI.
Continues until the next directive.
```

#### Reset to Default

```markdown
{!Normal text}
Back to standard document formatting.
The custom formatting above no longer applies.
This is regular body text again.
```

---

### Block Format Properties

| Property | Type | Values | GUI Location |
|----------|------|--------|--------------|
| `font` | value | Roboto, Arial, etc. | Font dropdown |
| `weight` | value | Thin, Extra Light, Light, Normal, Medium, Semi Bold, Bold, Extra Bold, Black | Font submenu |
| `size` | value | 12pt | Size field |
| `color` | value | #555555 | Text color picker |
| `highlight` | value | yellow, #hex | Highlight picker |
| `underline` | boolean | true, false | Underline button |
| `mono` | boolean | true, false | Monospace font |
| `align` | value | left, center, right, justify | Alignment buttons |
| `indent-left` | value | 0.5in | Ruler / indent buttons |
| `indent-right` | value | 0.5in | Ruler |
| `first-line-indent` | value | 0.5in | Ruler |
| `hanging-indent` | value | 0.5in | Ruler |
| `line-spacing` | value | single, 1.15, 1.5, double | Line spacing menu |
| `space-before` | value | 12pt | Line spacing menu |
| `space-after` | value | 12pt | Line spacing menu |

---

## MEA: Markdown Extensions for Anchors

### Anchor Markers

Anchors mark points in the document where bookmarks, comments, or other elements attach. They appear inline at the anchor position.

| Type | Syntax | Usage |
|------|--------|-------|
| Existing Anchor | `{^ id}` | Server-provided, must include ID |
| Proposed Anchor | `{^}` | New anchor, server assigns ID |

#### Existing Anchor

```markdown
{^ a3f2}The deadline is March 15th.
{^ b7k9}Bob is investigating the issue.
Multiple anchors can exist in {^ c2m8}one paragraph.
```

#### Existing Anchor Preservation

```markdown
{^ a3f2}The deadline moved to April 1st.
The LLM changed the text but preserved the anchor.
Server knows exactly which anchor to reattach.
```

#### Proposed Anchor

```markdown
{^}This is new content that should be anchored.
Server creates a new anchor at this position.
Use when adding content that needs an anchor point.
```

#### Anchors in Headings

When anchoring headings, place the anchor **after** the heading markers to preserve markdown compatibility. Standard markdown parsers require `#` characters at the start of the line to recognize headings.

```markdown
# {^ h1a2}Introduction
## {^ h2b3}Background
### {^ h3c4}Technical Details
## {^ h2d5}Conclusion
```

---

### Embedded Objects

Embedded objects (images, drawings, charts, etc.) cannot be represented in markdown. Use the `{^= id type}` syntax to preserve them as opaque placeholders during round-trip editing.

**Syntax:** `{^= id type}`

| Component | Description |
|-----------|-------------|
| `{^=` | Opening marker (anchor + equals) |
| `id` | Server-provided object ID |
| `type` | Object type from allowed list |
| `}` | Closing marker |

#### Allowed Types

| Type | Description |
|------|-------------|
| `image` | Inline or positioned image |
| `drawing` | Google Drawing |
| `chart` | Embedded chart (from Sheets) |
| `equation` | Mathematical formula |
| `video` | Embedded video |
| `embed` | Other embedded object (catch-all) |

#### Examples

```markdown
Here's the architecture diagram:

{^= obj_x7y2 image}

The linked spreadsheet shows quarterly data:

{^= obj_k9m3 chart}

See the formula below:

{^= obj_p4q1 equation}
```

#### Behavior

- **Export**: Embedded objects are replaced with `{^= id type}` placeholder
- **Import**: Placeholder is matched by ID; original object is preserved unchanged
- **Round-trip**: Object content is never modified, only its position in the document

---

### Anchor Links

Link to an anchor using `#^id` in standard markdown link syntax.

```markdown
For details, see the {^ a3f2}authentication setup below.

Review the [authentication setup](#^a3f2) before proceeding.
The link jumps directly to the anchor point.
```

The `^` prefix distinguishes anchor links from header links:

| Syntax | Target |
|--------|--------|
| `[text](#^a3f2)` | Anchor with ID `a3f2` |
| `[text](#api-setup)` | Header slug `api-setup` |

---

## Combined Example

A realistic document fragment using both MEBDF and MEA:

```markdown
## API Integration Status

@Jane Smith confirmed the {!mono}oauth-service{/!} deployment is complete.

{!mono}
POST /api/v2/tokens
Authorization: Bearer {token}
Content-Type: application/json

{!mono:false}
{^ b7k9}{!highlight:yellow}Blocking issue:{/!} The {!mono}refresh_token{/!} 
endpoint returns {!color:#cc0000}403{/!} for service accounts. @Bob is investigating.

Next steps:
- [ ] {!underline}Bob to escalate to platform team{/!}
- [ ] Jane to document workaround
- [ ] Sync at 📅 Dec 20, 2024
```

---

## Summary of Extensions

| Category | Syntax | Purpose |
|----------|--------|---------|
| Inline formatting | `{!props}text{/!}` | Apply formatting to wrapped text |
| Inline combined | `{!prop1, prop2}text{/!}` | Multiple properties on same span |
| Block formatting | `{!props}` | Stateful paragraph formatting |
| Boolean off | `{!prop:false}` | Turn off boolean property |
| Existing Anchor | `{^ id}` | Anchor with known ID |
| Proposed Anchor | `{^}` | New anchor, server assigns ID |
| Embedded Object | `{^= id type}` | Opaque placeholder for images, etc. |
| Anchor Link | `[text](#^id)` | Link to anchor |

---

## Design Principles

1. **Content first.** Extensions are minimal and don't obscure the text.

2. **One syntax family.** `{! }` for all formatting, inline or block determined by structure.

3. **Stateful blocks.** Format once, applies until changed. No repetitive annotations.

4. **Boolean defaults.** No value means true. Explicit false to turn off.

5. **Spacing optional.** `{!mono}` and `{! mono }` are equivalent.

6. **Two anchor types.** Existing Anchors have IDs. Proposed Anchors get IDs from the server.

7. **GUI terminology.** Property names match Google Docs interface.

8. **LLM-friendly.** Clean enough to read, structured enough to preserve through edits.

9. **Round-trip safe.** Read a document, edit it, write it back—formatting and anchors survive.
