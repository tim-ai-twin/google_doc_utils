# Quickstart: MCP Discoverability Testing

**Feature**: 002-mcp-discoverability-testing

## Prerequisites

- Python 3.11+
- `ANTHROPIC_API_KEY` environment variable set
- Existing MCP server (feature 127) functional

## Install

```bash
pip install anthropic  # New dependency for test harness
# mcp>=1.25.0 already installed
```

## Run the Default Test Suite (Mock Mode)

```bash
python -m extended_google_doc_utils.discoverability run
```

This will:
1. Start the MCP server in mock mode
2. Run 6 intents x 5 variants x 10 trials = 300 LLM calls
3. Generate a desire-path report in `reports/`

## Run a Single Intent

```bash
python -m extended_google_doc_utils.discoverability run --intent edit-section --trials 3
```

## Run in Live Mode (End-to-End)

```bash
python -m extended_google_doc_utils.discoverability run \
  --mode live \
  --credentials /path/to/token.json \
  --trials 2
```

## View Available Intents

```bash
python -m extended_google_doc_utils.discoverability list
```

## Add a New Test Intent

Create or edit a YAML file in `test_suites/`:

```yaml
intents:
  - name: my-new-intent
    description: "What the user wants to accomplish"
    expected_tools:
      - tool_a
      - tool_b
    variants:
      - text: "Natural phrasing of the request"
        style: natural
      - text: "A more explicit phrasing"
        style: explicit
```

## Read a Report

Reports are saved to `reports/desire-path-YYYY-MM-DD-HHMMSS.md`. Open in any markdown viewer. Key sections:
- **Summary** — aggregate scores at a glance
- **Per-Intent Results** — which intents/phrasings struggle
- **Desire Path Analysis** — what the LLM reaches for first
- **Recommendations** — actionable improvements

## Improvement Workflow

1. Run the test suite → read the report
2. Identify the worst-performing intent
3. Read the desire-path data to understand what the LLM tries first
4. Modify the MCP tool description to meet the LLM's expectations
5. Re-run the test suite → compare reports
6. Repeat
