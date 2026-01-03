# Tier A Tests - Credential-Free Testing

## Overview

Tier A tests are credential-free tests that run without any Google OAuth credentials or network access to Google APIs. These tests use fixtures and mocks to validate the application logic in isolation, making them accessible to cloud agents, CI/CD systems, and developers who don't have Google API credentials.

## Purpose

Tier A tests enable:

- **Cloud agents** to contribute code and run tests without credential access
- **Continuous Integration** to run automated tests on every pull request without approval gates
- **Fast feedback** during development without network latency or API rate limits
- **Offline development** when network connectivity is unavailable
- **Security** by testing untrusted code without exposing sensitive credentials

## How They Work

Tier A tests achieve credential-free operation by:

1. **Using mock fixtures** from `tests/fixtures/` that simulate Google API responses
2. **Testing business logic** in isolation without making real API calls
3. **Validating data transformations** using pre-recorded API response data
4. **Skipping authentication flows** by mocking credential management

## Running Tier A Tests

### Run only Tier A tests:
```bash
uv run pytest -m tier_a
```

### Run from this directory:
```bash
cd tests/tier_a
uv run pytest
```

### Run a specific test file:
```bash
uv run pytest tests/tier_a/test_auth_logic.py
```

## Writing Tier A Tests

### Test Structure

All Tier A tests must:

1. Be marked with the `@pytest.mark.tier_a` decorator
2. Use fixtures and mocks instead of real API calls
3. Be located in the `tests/tier_a/` directory
4. Not require any credentials or environment variables
5. Not make network requests to Google APIs

### Example Test

```python
import pytest
from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient

@pytest.mark.tier_a
def test_extract_text_from_document(mock_docs_api_response):
    """Test document text extraction using mock API response."""
    client = GoogleDocsClient(credentials=None)  # No real credentials needed

    # Use fixture providing mock Google Docs API response
    result = client.extract_text(mock_docs_api_response)

    assert result == "Expected text from mock document"
    assert "Gondwana" in result
```

### Using Fixtures

Mock fixtures are maintained in `tests/fixtures/`:

- `google_docs_responses.json` - Mock responses from Google Docs API
- `google_drive_responses.json` - Mock responses from Google Drive API

Load fixtures in your tests using the fixture loader utility from `tests/fixtures/__init__.py`.

## What Tier A Tests Cover

Tier A tests validate:

- **Authentication logic** - Credential loading, validation, and error handling (without real OAuth)
- **API response parsing** - Document structure parsing, text extraction, metadata handling
- **Configuration management** - Environment detection, settings loading, validation
- **Data transformations** - Converting API responses to internal data structures
- **Error handling** - Exception handling for various failure scenarios
- **Business logic** - Core application logic that doesn't require real API access

## What Tier A Tests DON'T Cover

Tier A tests cannot validate:

- **Real OAuth flows** - Actual authentication with Google requires Tier B tests
- **API integration** - Network communication and Google API behavior requires Tier B tests
- **End-to-end workflows** - Full integration scenarios require Tier B tests
- **API rate limiting** - Real API behavior requires Tier B tests
- **Credential refresh** - Token refresh flows require Tier B tests

## Maintaining Fixtures

When Google APIs change:

1. Run corresponding Tier B tests with real credentials to capture actual API responses
2. Update mock fixtures in `tests/fixtures/` to match current API response format
3. Re-run Tier A tests to verify compatibility with new fixture data
4. Document any breaking changes in fixture structure

## Performance Characteristics

Tier A tests are designed to be:

- **Fast** - No network latency, typically milliseconds per test
- **Reliable** - No external dependencies, consistent results
- **Isolated** - Can run in parallel without conflicts
- **Offline** - No internet connection required

Expected performance:
- Individual test execution: <100ms
- Full Tier A suite: <5 seconds

## Troubleshooting

### Tests are making network requests
- Verify test is marked with `@pytest.mark.tier_a`
- Check that API clients are properly mocked
- Ensure fixtures are loaded instead of real API calls

### Fixtures are out of date
- Run Tier B tests to capture current API responses
- Update fixture files with actual response data
- Verify fixture structure matches code expectations

### Tests fail in CI but pass locally
- Ensure no local environment variables are being used
- Verify no dependencies on local file system state
- Check that all fixtures are committed to version control

## See Also

- **[Tier B Tests](../tier_b/README.md)** - Credential-required integration tests
- **[Quickstart Guide](../../specs/001-cloud-testing-oauth/quickstart.md)** - Setup instructions
- **[Contributing](../../CONTRIBUTING.md)** - Development workflow (when available)

## Philosophy

Tier A tests embody the principle that **most application logic should be testable without external dependencies**. By separating business logic from API integration, we enable:

- Rapid development cycles with instant feedback
- Inclusive contribution from developers without credential access
- Robust test coverage that's fast, reliable, and maintainable
- Security through isolation of untrusted code from sensitive credentials

**When in doubt, write a Tier A test first.** Only escalate to Tier B tests when you need to validate real API integration.
