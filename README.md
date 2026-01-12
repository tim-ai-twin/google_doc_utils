# Google Docs MCP Server

[![Tier A Tests](https://github.com/tim-ai-twin/google_doc_utils/actions/workflows/tier-a-tests.yml/badge.svg)](https://github.com/tim-ai-twin/google_doc_utils/actions/workflows/tier-a-tests.yml)
[![Tier B Tests](https://github.com/tim-ai-twin/google_doc_utils/actions/workflows/tier-b-tests.yml/badge.svg)](https://github.com/tim-ai-twin/google_doc_utils/actions/workflows/tier-b-tests.yml)

An MCP server that enables LLMs to read and edit Google Docs. Provides 10 tools for document navigation, section editing, and formatting.

## Quick Start

### 1. Install

```bash
git clone https://github.com/tim-ai-twin/google_doc_utils.git
cd google_doc_utils
uv sync
```

### 2. Set Up OAuth Credentials

```bash
uv run python scripts/bootstrap_oauth.py
```

This opens a browser for Google OAuth and saves credentials to `.credentials/token.json`.

### 3. Configure Your MCP Client

Replace `/path/to/google_doc_utils` with your actual installation path.

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "google-docs": {
      "command": "/path/to/google_doc_utils/.venv/bin/python",
      "args": ["-m", "extended_google_doc_utils.mcp", "--credentials", "/path/to/google_doc_utils/.credentials/token.json"]
    }
  }
}
```

**Claude Code** (`.claude/settings.json` in your project):
```json
{
  "mcpServers": {
    "google-docs": {
      "command": "/path/to/google_doc_utils/.venv/bin/python",
      "args": ["-m", "extended_google_doc_utils.mcp", "--credentials", "/path/to/google_doc_utils/.credentials/token.json"]
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "google-docs": {
      "command": "/path/to/google_doc_utils/.venv/bin/python",
      "args": ["-m", "extended_google_doc_utils.mcp", "--credentials", "/path/to/google_doc_utils/.credentials/token.json"]
    }
  }
}
```

### 4. Available Tools

| Tool | Description |
|------|-------------|
| `list_documents` | List Google Docs accessible to the user |
| `get_metadata` | Get document metadata including tabs |
| `get_hierarchy` | Get heading structure with anchor IDs |
| `export_section` | Export a section to markdown |
| `import_section` | Replace a section's content (other sections unchanged) |
| `export_tab` | Export entire tab to markdown |
| `import_tab` | Replace entire tab content |
| `normalize_formatting` | Apply consistent fonts/styles |
| `extract_styles` | Extract formatting from a document |
| `apply_styles` | Apply extracted styles to another document |

## Overview

This project provides:
- **MCP Server**: 10 tools for LLM document manipulation
- **Section Isolation**: Edit one section without affecting others
- **MEBDF Format**: Markdown with extensions for Google Docs formatting
- **Two-Tier Testing**: Unit tests with mocks + e2e tests against real Google Docs

## Development Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- (Optional) Google Cloud project with Docs and Drive APIs enabled for integration testing

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd google_doc_utils
```

2. Install dependencies using uv:
```bash
uv sync
```

3. (Optional) Install development dependencies:
```bash
uv sync --group dev
```

4. (Optional) Install Google API dependencies for integration testing:
```bash
uv sync --group google
```

## Testing

### Unit Tests (No Credentials Required)

Run the complete unit test suite:
```bash
uv run pytest
```

Run with verbose output:
```bash
uv run pytest -v
```

Run specific test files:
```bash
uv run pytest tests/unit/
```

### Integration Tests (Credentials Required)

Integration tests require Google API credentials. See the Authentication section below.

```bash
uv run pytest tests/integration/
```

### Code Quality

Lint the codebase:
```bash
uv run ruff check .
```

Format code:
```bash
uv run ruff format .
```

## Authentication

For local development and integration testing, you'll need to set up OAuth credentials:

1. Create a Google Cloud project and enable the Google Docs and Drive APIs
2. Create OAuth 2.0 credentials (Desktop application type)
3. Run the bootstrap script to obtain a refresh token:
```bash
uv run python scripts/bootstrap_google_refresh_token.py
```

4. The script will create a `.env.local` file with your credentials (this file is gitignored)

For detailed authentication setup and troubleshooting, see the [Authentication Guide](docs/authentication.md).

## Project Structure

```
src/extended_google_doc_utils/
  core/                     # Core format logic (no Google dependencies)
    model.py                # Extended format types
    validate.py             # Schema validation
    normalize.py            # Canonicalization rules

  google_adapter/           # Google API integration layer
    auth.py                 # OAuth utilities
    docs_api.py             # Docs API client
    drive_api.py            # Drive API client
    doc_to_format.py        # Google Doc → Extended Format
    format_to_requests.py   # Extended Format → batchUpdate requests

  mcp_server/               # MCP server implementation
    server.py               # Server entrypoint
    tools.py                # High-level MCP tools

tests/
  unit/                     # Unit tests (no credentials)
  integration/              # Integration tests (requires credentials)
  fixtures/                 # Test fixtures
```

## Development

### For Cloud Coding Agents

This project is designed to be developer-friendly for both humans and AI coding agents:

1. **Tier A tests run without credentials**: Clone the repo and run tests immediately
2. **Clear layering**: Core logic is separated from Google API specifics
3. **Comprehensive fixtures**: Real-world test cases without manual JSON wrangling

#### Cloud Agent Mode

Cloud agents should set `CLOUD_AGENT=true` and run only Tier A tests:

```bash
export CLOUD_AGENT=true
uv run pytest -m tier_a
```

This runs all credential-free tests using mocks and fixtures. Tier B tests (which require Google API credentials) are automatically skipped.

**Test Tiers:**
- **Tier A** (`-m tier_a`): No credentials required, uses mocks/fixtures
- **Tier B** (`-m tier_b`): Requires Google API credentials, makes real API calls

See [tests/tier_b/README.md](tests/tier_b/README.md) for more details on the tiered testing strategy.

### Contributing

When working on this project:
- Run unit tests before committing: `uv run pytest`
- Ensure code passes linting: `uv run ruff check .`
- Format your code: `uv run ruff format .`
- Integration tests run automatically on PRs to `main` (for same-repo branches)

## Documentation

- [Project PRD](spec/Proposed%20Rough%20Draft%20PRD%20Extended%20Google%20Doc%20MCP%20Server.md) - Comprehensive product requirements
- [Extended Doc Format Specification](spec/md-extensions-spec.md) - Format specification

## License

See [LICENSE](LICENSE) for details.

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.
