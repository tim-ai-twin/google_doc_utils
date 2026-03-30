# Research: Large Document Editing

## R1: Plain Markdown Output from Existing AST

**Decision**: Add a `PlainMarkdownSerializer` alongside `MebdfSerializer`, both operating on the same `DocumentNode` AST.

**Rationale**: The conversion pipeline already produces an AST (`DocumentNode`) before serialization. The `MebdfSerializer` walks the AST and emits MEBDF. A `PlainMarkdownSerializer` would walk the same AST but:
- Skip `FormattingNode` wrappers — emit child text only
- Skip `EmbeddedObjectNode` — emit `[image]` placeholder text
- Skip anchor markers (`{^ ...}`) from headings
- Preserve standard markdown: `#` headings, `**bold**`, `*italic*`, `[links](url)`, lists, tables

This avoids touching the Google Docs API parsing layer — only the serialization layer changes.

**Alternatives considered**:
- Regex stripping of MEBDF markers from output → fragile, misses edge cases
- New conversion pipeline → duplicates work, harder to maintain
- Post-processing with `re.sub` → simpler but less reliable than AST-based approach

## R2: Section Size Calculation in Hierarchy

**Decision**: Compute word/character counts per section by extracting plain text from section body elements at hierarchy time.

**Rationale**: `get_hierarchy()` already fetches the full document body and iterates over all elements. The body `content` array contains all paragraph elements with `textRun.content`. We can:
1. Use `get_all_sections()` (already exists in `section_utils.py`) to get section boundaries
2. For each section, iterate elements within `[start_index, end_index)` and extract text via `extract_paragraph_text()`
3. Count words (split on whitespace) and characters (len of text)

This adds O(n) work to an already O(n) operation — negligible overhead.

**Alternatives considered**:
- Separate API call for sizes → adds latency, wasteful since body is already fetched
- Approximate from character indices → inaccurate, doesn't account for non-text elements

## R3: Format Parameter on read_tab

**Decision**: Add `format: str = "mebdf"` parameter to `read_tab` MCP tool (and converter method). Values: `"mebdf"` (default, backward compatible) or `"plain"`.

**Rationale**: Adding a parameter to the existing tool is cleaner than creating a new tool. Default of `"mebdf"` ensures backward compatibility. The converter method routes to the appropriate serializer based on format.

**Alternatives considered**:
- New `read_tab_plain` tool → tool proliferation, harder discovery
- `export_to_file` MCP tool → violates MCP as data-access layer (rejected per user feedback)

## R4: Claude Code Skill Architecture

**Decision**: Create a Claude Code skill at `.claude/skills/edit-google-doc.md` that provides prompt instructions for orchestrating the large-document workflow.

**Rationale**: Claude Code skills are markdown files that provide context and instructions when invoked. The skill will:
1. Guide the LLM through the metadata → hierarchy → read plain → save to disk → grep → read section → write section flow
2. Handle filesystem operations (write temp files, cleanup) via Claude Code's built-in Write/Read/Grep tools
3. Keep the MCP server stateless and filesystem-free

**Alternatives considered**:
- Python script orchestrator → requires separate execution, less integrated
- MCP-level workflow tool → mixes orchestration with data access

## R5: Keeping Content Out of Context

**Decision**: The skill instructs the LLM to use `read_tab(format="plain")`, then immediately write the result to a temp file using Claude Code's Write tool, rather than keeping it in context.

**Rationale**: The key insight is that MCP tool results DO enter context. So even `read_tab(format="plain")` puts the full tab content in context. The skill must instruct the LLM to:
1. Call `read_tab(format="plain")` — content enters context temporarily
2. Immediately write to a temp file — content is now on disk
3. The context window cost is paid once but then the LLM works from disk

This is still better than the current approach because:
- Plain markdown is ~5-25% smaller than MEBDF (no formatting markers)
- The LLM can then use targeted Grep/Read instead of re-reading everything
- For subsequent searches, no additional context is consumed

**Important limitation**: We cannot fully avoid the initial context cost of reading the tab. The savings come from:
- Smaller format (plain vs MEBDF)
- Not needing to re-read for searching (disk-based grep instead)
- Section-targeted reads for editing (only the needed section)
