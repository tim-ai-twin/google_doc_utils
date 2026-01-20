# Future Ideas: Document Style Transfer

Ideas for future improvements that are not critical for initial release.

## Testing Improvements

### Multi-Tab Test Document
Create a dedicated multi-tab Google Doc for integration testing:
- Tab 1: Various heading styles with different formatting
- Tab 2: Body text with paragraph spacing variations
- Tab 3: Mixed content for round-trip testing

This would enable T058/T059 from tasks.md and catch regressions in tab-specific style handling.

### E2E Visual Validation with Playwright
Use Playwright to visually validate style transfer results:
- Open source and target documents in browser
- Screenshot heading/body elements before and after transfer
- Compare visual appearance (color, font, size) programmatically
- Detect regressions that unit tests might miss (e.g., subtle rendering differences)

Benefits:
- Catches issues that API-level tests miss
- Validates what users actually see
- Could run on CI with headless browser

### E2E MCP Validation Through Dedicated LLM Test Harness
Create a test harness that exercises MCP tools via actual LLM interaction:
- Spin up MCP server with test credentials
- Connect Claude or another LLM to the server
- Issue natural language requests: "Apply styles from doc A to doc B"
- Verify the LLM correctly interprets tool responses
- Test error handling and edge case communication

Benefits:
- Validates the full LLM-to-API pipeline
- Catches issues in tool descriptions and response formats
- Tests real-world usage patterns
- Could use Claude API with tool_use to automate

Implementation sketch:
```python
async def test_llm_style_transfer():
    # Start MCP server
    server = await start_mcp_server(credentials=test_creds)

    # Connect LLM with MCP tools
    response = await claude.messages.create(
        model="claude-sonnet-4-20250514",
        tools=server.get_tool_definitions(),
        messages=[{
            "role": "user",
            "content": "Apply the heading styles from doc A to doc B"
        }]
    )

    # Verify tool was called correctly
    assert response.tool_calls[0].name == "apply_document_styles"

    # Verify result interpretation
    followup = await claude.messages.create(...)
    assert "successfully applied" in followup.content.lower()
```
