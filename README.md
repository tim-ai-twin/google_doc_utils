# Extended Google Doc Utils

A Python-based MCP (Model Context Protocol) server that provides high-level utilities for reading, writing, and managing Google Docs with advanced formatting support.

## Overview

This project provides:
- **Extended Google Docs API**: Read/write Google Docs including formatting, comments, and Drive metadata
- **Format Conversion**: Convert between Google Doc API representations and an internal "Extended Doc Format"
- **MCP Server**: Exposes high-level tools (e.g., `insert_markdown`, `replace_section_with_markdown`) instead of low-level Google API primitives
- **Two-Tier Testing**: Unit tests that run without credentials and integration tests with real Google APIs

## Features

- Clean layered architecture separating core logic, Google adapters, and MCP server
- Support for both consumer Gmail and Google Workspace accounts
- OAuth 2.0 authentication with long-lived refresh tokens
- Comprehensive test coverage with fixture-based unit tests
- GitHub Actions CI with secure credential handling

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- (Optional) Google Cloud project with Docs and Drive APIs enabled for integration testing

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd extended-google-doc-utils
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

1. **Unit tests run without credentials**: Clone the repo and run `uv run pytest` immediately
2. **Clear layering**: Core logic is separated from Google API specifics
3. **Comprehensive fixtures**: Real-world test cases without manual JSON wrangling

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
