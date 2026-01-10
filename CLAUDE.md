# google_doc_utils Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-02

## Active Technologies
- Python 3.11+ (existing project requirement) + google-api-python-client (existing), new: regex/re for MEBDF parsing (126-gdoc-markdown-converter)
- N/A (stateless conversion, no persistence) (126-gdoc-markdown-converter)
- Python 3.11+ (matches existing project requirement) + `mcp>=1.25.0` (official MCP SDK), existing `extended_google_doc_utils` (converter, auth) (127-gdoc-mcp-server)
- N/A (stateless—credentials from file or environment per existing CredentialManager) (127-gdoc-mcp-server)

- Python 3.11+ (minimum version for modern type hints and async capabilities) (001-cloud-testing-oauth)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (minimum version for modern type hints and async capabilities): Follow standard conventions

## Recent Changes
- 127-gdoc-mcp-server: Added Python 3.11+ (matches existing project requirement) + `mcp>=1.25.0` (official MCP SDK), existing `extended_google_doc_utils` (converter, auth)
- 126-gdoc-markdown-converter: Added Python 3.11+ (existing project requirement) + google-api-python-client (existing), new: regex/re for MEBDF parsing

- 001-cloud-testing-oauth: Added Python 3.11+ (minimum version for modern type hints and async capabilities)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
