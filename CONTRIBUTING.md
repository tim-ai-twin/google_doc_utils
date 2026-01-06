# Contributing to Extended Google Doc Utils

## Development Setup

### Prerequisites

- Python 3.11 or later
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd google_doc_utils

# Install dependencies
uv sync

# Run tests to verify setup
uv run pytest -m tier_a
```

### Optional: Google API Credentials

For integration testing (Tier B tests), you'll need OAuth credentials:

```bash
uv run scripts/bootstrap_oauth.py
```

This opens a browser for Google OAuth consent and saves credentials to `.credentials/token.json` (gitignored).

## Testing Strategy

This project uses a two-tier testing strategy to enable contributions from developers and cloud agents without requiring Google API credentials.

### Tier A Tests (Credential-Free)

**Run without any credentials or network access.**

```bash
uv run pytest -m tier_a
```

Tier A tests:
- Use mocks and fixtures to simulate Google API responses
- Run on every PR automatically in CI
- Are fast (<5 seconds for the full suite)
- Cover business logic, data transformations, error handling

**When to write Tier A tests:**
- Testing application logic that doesn't require real API calls
- Validating response parsing and data transformations
- Testing error handling and edge cases
- Any new feature's core logic

### Tier B Tests (Credential-Required)

**Require valid OAuth credentials and make real API calls.**

```bash
uv run pytest -m tier_b
```

Tier B tests:
- Validate real Google API integration
- Require manual approval in CI (protected environment)
- Are slower due to network calls
- Cover authentication flows and API contracts

**When to write Tier B tests:**
- Testing real OAuth flows
- Validating actual API response handling
- Catching Google API changes
- Integration testing critical paths

### Running All Tests

```bash
# All tests (Tier B will skip if no credentials)
uv run pytest

# Verbose output
uv run pytest -v

# Specific test file
uv run pytest tests/tier_a/test_auth_logic.py
```

### Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## Commit Conventions

Use the task ID prefix format when working on tracked tasks:

```
T###: Brief description of change

Longer explanation if needed.
```

Examples:
- `T076: Add Tier B tests workflow with environment protection`
- `T074: Add environment variable validation with clear error messages`

For general commits without a task ID:

```
<type>: Brief description

Types: fix, feat, refactor, docs, test, chore
```

Examples:
- `fix: Correct token refresh logic`
- `feat: Add document export functionality`
- `docs: Update authentication guide`

### Commit Guidelines

1. **Keep commits atomic** - Each commit should represent one logical change
2. **Write meaningful messages** - Explain what and why, not how
3. **Reference task IDs** - Link to tracked work when applicable
4. **Run tests before committing** - Ensure `uv run pytest -m tier_a` passes

## Pull Request Process

### Before Opening a PR

1. **Run Tier A tests locally:**
   ```bash
   uv run pytest -m tier_a
   ```

2. **Run linting:**
   ```bash
   uv run ruff check .
   ```

3. **Format code:**
   ```bash
   uv run ruff format .
   ```

### PR Requirements

- All Tier A tests must pass
- Code must pass linting (ruff check)
- Include tests for new functionality
- Update documentation if changing public APIs

### CI Workflow

1. **Tier A tests run automatically** on all PRs
2. **Tier B tests require approval** - A maintainer must approve the `tier-b-testing` environment
3. **Maintainer reviews code** before approving Tier B environment access

### Merging

- PRs require passing CI checks
- Squash merge is preferred for clean history
- Delete branch after merge

## Project Structure

```
src/extended_google_doc_utils/
  auth/                       # OAuth and credential management
  google_api/                 # Google API clients
  core/                       # Core format logic

tests/
  tier_a/                     # Credential-free tests
  tier_b/                     # Integration tests
  fixtures/                   # Mock API responses

.github/workflows/
  tier-a-tests.yml           # Auto-run on PRs
  tier-b-tests.yml           # Requires approval
```

## Getting Help

- Check existing [tests/tier_a/README.md](tests/tier_a/README.md) for Tier A test examples
- Check [tests/tier_b/README.md](tests/tier_b/README.md) for Tier B test guidance
- See [specs/001-cloud-testing-oauth/quickstart.md](specs/001-cloud-testing-oauth/quickstart.md) for detailed setup
