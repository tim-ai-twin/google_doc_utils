# Research: Google Docs MCP Server

**Feature Branch**: `127-gdoc-mcp-server`
**Date**: 2026-01-10

## Research Questions

### 1. MCP Python SDK Selection

**Decision**: Use the official `mcp` Python SDK (v1.25.0+)

**Rationale**:
- Official Anthropic SDK with full MCP specification compliance
- FastMCP interface integrated into official SDK since 2024
- Active maintenance with latest release December 2025
- Decorator-based tool definitions match Python idioms
- Automatic JSON Schema generation from type hints and docstrings

**Alternatives Considered**:
- **FastMCP 2.0 standalone**: More features (enterprise auth, deployment tools) but adds complexity we don't need. Our auth is already handled by the existing CredentialManager.
- **Raw protocol implementation**: Rejected—unnecessarily complex and error-prone.

**Sources**:
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python SDK Documentation](https://modelcontextprotocol.github.io/python-sdk/)
- [PyPI MCP Package](https://pypi.org/project/mcp/1.7.1/)

### 2. Tool Definition Pattern for LLM Discoverability

**Decision**: Use decorator-based tools with explicit type hints, detailed docstrings, and parameter constraints

**Rationale**:
- MCP SDK auto-generates JSON Schema from type hints
- Docstrings become tool descriptions visible to LLMs
- Constrained inputs (enums, bounds, required fields) reduce LLM errors
- Short, action-oriented tool names (e.g., `export_section`, `import_tab`)

**Best Practices from Research**:
1. **Clear naming**: Use short identifiers like `get_hierarchy` rather than sentences
2. **Focused descriptions**: State what questions/tasks the tool handles
3. **Schema constraints**: Use enums, min/max bounds, required fields
4. **Avoid similar tools**: LLMs confuse tools with overlapping functionality
5. **Concise responses**: JSON or small markdown fragments, not verbose prose

**Example Pattern**:
```python
@mcp.tool()
def export_section(
    document_id: str,
    anchor_id: str,
    tab_id: str = ""
) -> dict:
    """Export a specific section of a Google Doc to MEBDF markdown.

    Use this tool when you need to read one section of a document.
    First call get_hierarchy to find the anchor_id for your target section.

    Args:
        document_id: Google Doc ID (from the document URL)
        anchor_id: Heading anchor ID from get_hierarchy. Empty string for preamble.
        tab_id: Tab ID for multi-tab docs. Empty string for single-tab docs.

    Returns:
        dict with 'content' (MEBDF markdown) and 'warnings' (list of issues)
    """
```

**Sources**:
- [MCP Tips, Tricks and Pitfalls](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)
- [MCP Python SDK Documentation](https://modelcontextprotocol.github.io/python-sdk/)

### 3. Authentication Integration

**Decision**: Reuse existing CredentialManager from `extended_google_doc_utils.auth`

**Rationale**:
- CredentialManager already handles OAuth credential loading (file and environment)
- Token refresh is automatic
- No need for MCP-level authentication—Google API auth is the only requirement
- MCP server runs locally (stdio transport) so no additional auth needed

**Implementation**:
- MCP server loads credentials once at startup using CredentialManager
- Creates GoogleDocsConverter with those credentials
- All tool calls use the same converter instance

### 4. Transport Selection

**Decision**: Use stdio transport (default for local MCP servers)

**Rationale**:
- Standard transport for Claude Desktop and local LLM integration
- No network exposure—secure by design
- Simple deployment (run script directly)

**Alternatives Considered**:
- **SSE/HTTP**: Only needed for remote servers or web integration—out of scope
- **WebSocket**: Same as above—unnecessary complexity for local use

### 5. Error Handling Strategy

**Decision**: Return structured error responses with actionable messages

**Pattern**:
```python
{
    "success": False,
    "error": {
        "type": "AnchorNotFoundError",
        "message": "Section 'h.abc123' not found in document",
        "suggestion": "Call get_hierarchy to see available sections"
    }
}
```

**Rationale**:
- LLMs can parse structured errors and recover
- Actionable suggestions reduce retry failures
- Consistent response format for all tools

### 6. Formatting Operations Design

**Decision**: Implement formatting normalization as MEBDF transformation

**Approach**:
1. Export document to MEBDF
2. Parse and identify block formatting patterns
3. Apply target formatting rules (font, size, spacing)
4. Re-serialize to MEBDF
5. Import back to Google Doc

**Rationale**:
- Leverages existing converter infrastructure
- Round-trip safe by design
- Can be extended to style matching (extract patterns from source doc)

**Alternative Considered**:
- **Direct Google Docs API formatting**: More efficient but bypasses MEBDF, breaking the round-trip safety principle. Rejected per Constitution Principle II.

## Technology Summary

| Component | Choice | Rationale |
|-----------|--------|-----------|
| MCP SDK | `mcp>=1.25.0` | Official SDK with FastMCP interface |
| Python | 3.11+ | Matches existing project requirement |
| Transport | stdio | Standard for local MCP servers |
| Auth | CredentialManager | Reuse existing OAuth infrastructure |
| Content Format | MEBDF | Round-trip safe per Constitution |
