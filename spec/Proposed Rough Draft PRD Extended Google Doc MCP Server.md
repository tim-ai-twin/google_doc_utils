# Proposed Rough Draft PRD: Extended Google Doc MCP Server.md

Architecture for Local + CI + Cloud-Agent Development

** THIS DOC IS A ROUGH DRAFT CONCEPT/SUGGESTION ONLY. **

## 1. Context and problem statement

You are building an “Extended Google Doc MCP server” (Python + `uv`) that:
- Reads/writes Google Docs (including formatting) and likely Drive metadata.
- Handles comments and other business-document writing features.
- Converts between Google Doc API representations and an internal “Extended Doc Format” (spec already defined).
- Exposes higher-level MCP tools (e.g., `insert_markdown`, `replace_section_with_markdown`) instead of low-level Google API primitives.

Primary integration challenge: Google Docs/Drive access requires OAuth 2.0 and (for read/write/delete) uses sensitive scopes. You need:
- Reliable **local development** (interactive OAuth allowed).
- Reliable **GitHub Actions CI** (no interactive OAuth, must use stored credentials).
- Support for **cloud-based coding agents** (Cursor / Claude Code / Codex) that may not have access to OAuth secrets but should still develop effectively.

A poor decision around auth + repo structure will cascade into reauth churn, brittle CI, and “agent can’t run tests” issues.

## 2. Goals

### 2.1 Primary goals
1. **Deterministic unit test suite** runnable locally, in CI, and by cloud agents **without Google credentials**.
2. **Automated integration test suite** that calls real Google APIs using **non-interactive auth** (refresh token), runnable in:
   - GitHub Actions on every PR targeting `main` **when the PR branch is in the same repo** (secrets available)
   - `workflow_dispatch` for maintainer-triggered runs (required fallback for fork PRs)
   - local developer machine (optional)
3. A **bootstrap OAuth script** that:
   - prompts developer login once
   - outputs a refresh token and supporting metadata
   - avoids OAuth Playground and “Testing-mode 7-day expiry” traps
4. A **consistent Python configuration** across:
   - local scripts
   - CI jobs
   - eventual deployment runtime
5. Clean layering separating:
   - core format/spec logic
   - Google adapters
   - MCP server layer

### 2.2 Non-goals (for this PRD)
- Completing Google’s sensitive scope verification process.
- Full multi-tenant production credential storage design (we define interfaces and a minimal dev+CI mechanism now).

## 3. Users and use cases

### Personas
- **Developer (you / collaborator):** runs local scripts/tests; occasionally rotates tokens.
- **CI runner:** executes unit tests on PRs and gated integration tests on protected workflows.
- **Cloud coding agent:** can modify code and run unit tests, but may not access OAuth secrets.

### Key use cases
- Convert Google Doc JSON → Extended Format; validate formatting transforms.
- Generate Google `batchUpdate` requests from Extended Format.
- Run unit tests on every PR (no secrets).
- Run integration tests against a dedicated test Google account + dedicated test docs (secrets required).
- Allow cloud agents to contribute safely without exposing secrets.

## 4. Key product decisions

### 4.1 Test strategy: two tiers
**Tier A: Unit/contract tests (always on)**
- No Google network calls.
- Uses fixtures (captured `documents.get` JSON, comments JSON, and canonical expected request payloads).
- Validates conversion, normalization, idempotence, and tool semantics.

**Tier B: Integration tests (automated with secure gating)**
- Calls real Google APIs using stored credentials.
- Runs automatically on **every PR targeting `main`** when the PR originates from the same repo (not a fork).
- For fork PRs (where secrets are not available), provides a **manual maintainer-triggered** `workflow_dispatch` path.
- Must be runnable locally using the same `.env.local` or secret-store inputs used by CI.

### 4.2 Auth strategy: bootstrap + long-lived refresh token (single-user, local-first)

- MCP server runs **locally** (on the developer/user machine) for now.
- Use a **local installed-app OAuth flow** to mint a refresh token once and store it securely.
- Use **single-user** OAuth token storage initially (one dedicated test identity).
- Do **not** use OAuth Playground tokens for dev/CI.
- Do **not** churn refresh tokens unnecessarily (token issuance limits can invalidate older tokens).
- Ensure OAuth consent screen “Publishing status” is **In production** (not “Testing”) to avoid forced expiry.

Account compatibility:
- Must support **consumer Gmail** and **Google Workspace** accounts.
- Note: some Workspace admins restrict third-party OAuth apps or unverified apps; the local auth bootstrap should surface clear errors and a troubleshooting note if the domain blocks consent.

## 5. Requirements

### 5.1 Repository structure (required)
Use `src/` layout and explicit layering:

```
repo/
  pyproject.toml
  uv.lock
  README.md
  LICENSE
  .python-version
  .gitignore
  .env.example

  src/extended_gdoc_mcp/
    __init__.py

    core/                     # spec-driven logic; NO google deps
      model.py                # AST / extended format types
      validate.py             # schema validation + invariants
      normalize.py            # canonicalization rules
      transforms/             # formatting transforms
      serialization/          # format import/export (non-google)

    google_adapter/           # google-specific translation layer
      auth.py                 # token exchange utilities (no prompting)
      docs_api.py             # thin client wrapper
      drive_api.py
      comments_api.py
      doc_to_format.py        # Google Doc JSON -> core model
      format_to_requests.py   # core model -> batchUpdate requests
      fixtures/               # fixture helpers (sanitization)

    mcp_server/               # MCP exposure layer (tools)
      server.py               # entrypoint
      tools.py                # high-level tools: insert_markdown, etc.
      routing.py              # dispatch/validation
      errors.py

    config/
      settings.py             # pydantic settings + env var mapping

  scripts/
    bootstrap_google_refresh_token.py
    fetch_fixture_doc.py
    fetch_fixture_comments.py
    sanitize_fixture.py

  tests/
    unit/
      test_doc_to_format.py
      test_format_to_requests.py
      test_roundtrip.py
    integration/
      test_live_docs_smoke.py
      test_live_comments_smoke.py
    fixtures/
      docs/
      comments/
      expected_requests/

  .github/workflows/
    unit.yml
    integration.yml
```

**Acceptance criteria**
- `core/` must remain importable and fully testable without Google libraries.
- `google_adapter/` must be testable with fixtures and mocks.
- `mcp_server/` must be testable with a fake adapter (dependency injection).

### 5.2 Python tooling & consistency (required)
- Use `uv` with:
  - `pyproject.toml` defining dependencies, optional dependency groups, and entrypoints.
  - `uv.lock` committed for reproducible installs.
- Define dependency groups:
  - `dev`: `ruff`, `pytest`, `coverage`, `pre-commit`, (optional `pyright` or `mypy`)
  - `google`: `google-auth`, `google-auth-oauthlib`, (optional `google-api-python-client`)
  - `mcp`: MCP server dependencies
- Provide consistent commands:
  - Unit: `uv run pytest -q`
  - Integration: `uv run pytest -q tests/integration`
  - Lint: `uv run ruff check .`
  - Format: `uv run ruff format .`

### 5.3 Auth bootstrap script (required)
Create `scripts/bootstrap_google_refresh_token.py`.

**Functional requirements**
- Uses `google-auth-oauthlib` installed-app flow (`InstalledAppFlow.run_local_server`) to prompt login and capture the authorization code locally.
- Requests offline access and outputs a refresh token.
- Supports `--scopes` and a default scope set suitable for Drive + Docs CRUD (see **5.3.1**).
- Outputs (stdout and/or `.secrets/` file):
  - `refresh_token`
  - `client_id`
  - `client_secret` reference (see security requirements)
  - granted scopes
  - timestamp + “token source” metadata
- Supports `--publish` to distribute credentials for development and CI:
  - `--publish local` writes/updates a local env file (default: `.env.local`, gitignored) with `GOOGLE_*` values.
  - `--publish github` publishes secrets to GitHub for CI testing (see **5.3.2**).
  - `--publish both` does both.

**Security requirements**
- Never writes secrets into tracked repo files.
- If writing to disk, write under `.secrets/` (gitignored) with 0600 permissions.
- Warn if consent screen publishing status is “Testing” (expiry risk).
- Never echo secrets in logs unless explicitly requested with `--print-secrets` (default false).

#### 5.3.1 Default scope set (Drive + Docs CRUD)
The bootstrap script must ship with a conservative-but-functional default scope set that supports CRUD for both Docs and Drive.

**Default (recommended for integration tests / full CRUD):**
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/drive`

**Least-privilege alternative (optional):**
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/drive.file`

Notes:
- `drive.file` limits access to files created by or opened with the app. It is lower risk but can be surprising if you expect access to arbitrary existing files.
- The script must allow overriding scopes via `--scopes` and must persist the chosen scopes into published env/secrets so local and CI runs are consistent.

#### 5.3.2 Publishing to GitHub (required behavior)
- The script must support publishing CI secrets using one of:
  - GitHub CLI (`gh secret set`) if available, OR
  - GitHub REST API calls if `GITHUB_TOKEN`/`GH_TOKEN` with appropriate permissions is available.
- Inputs required for GitHub publishing:
  - `--repo owner/name` (or inferred from `git remote`)
  - authentication via `gh auth` or token env var
- Secrets to set in GitHub:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REFRESH_TOKEN`
  - `GOOGLE_SCOPES`
  - `TEST_DOC_ID` (and optional folder/file IDs)

### 5.4 Credential distribution model (required)
You need one refresh token for a dedicated test account and dedicated test documents.

**Local development**
- Credentials sourced from one of:
  - `.env` (gitignored)
  - local secret store (preferred later)
- Required env vars:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REFRESH_TOKEN`
  - `GOOGLE_SCOPES` (optional)
  - `TEST_DOC_ID` (and optionally `TEST_FOLDER_ID`)

**GitHub Actions**
- Store the same values as GitHub repo secrets (or environment secrets).
- Integration workflow must never run on untrusted fork PRs.

**Cloud coding agents**
- Must be able to run Tier A tests without secrets.
- Must have a clear path to Tier B integration verification:
  - Preferred: the agent works on a **branch in the main repo** (not a fork) so GitHub Actions secrets are available and integration tests can run automatically on PRs to `main`.
  - Fallback: maintainer triggers `workflow_dispatch` after reviewing the PR.
- Document the expected workflow in `README.md` so agents and humans follow the same path.

### 5.5 GitHub Actions workflows (required)

#### `.github/workflows/unit.yml`
Triggers: `pull_request`, `push`

Steps:
- checkout
- install via `uv`
- lint/format/typecheck (as configured)
- run unit tests
- (optional) upload coverage

#### `.github/workflows/integration.yml`
Triggers:
- `pull_request` **to `main`** (required)
- `workflow_dispatch` (required)

Behavior requirements (security + usability):
- Integration tests must run automatically on **every PR targeting `main`**, but **only when secrets can be safely used**.
- Because secrets are not provided to workflows triggered from forks, the workflow must:
  - Run automatically for PRs where `head.repo.full_name == github.repository` (same-repo branches), and
  - Skip (with a clear message) for fork PRs.
- For fork PRs, provide a manual path:
  - Maintainer triggers `workflow_dispatch` after reviewing the PR, OR
  - Maintainer asks the cloud agent to open a branch in the main repo (not a fork) if possible.

Steps:
- checkout
- install via `uv` including `[google]` deps
- run integration tests only
- store logs/artifacts (optional)

**Hard requirements**
- Integration workflow must not leak secrets in logs.
- Integration workflow must not run untrusted fork code with secrets.

### 5.6 Adapter interfaces & dependency injection (required)
Define an interface (protocol) so MCP tools and core logic can run with either:
- real Google adapter (integration)
- fake adapter (unit tests)

Example surface:
- `get_document(doc_id) -> dict`
- `batch_update(doc_id, requests: list[dict]) -> dict`
- `list_comments(file_id) -> dict`
- (integration convenience) `create_document(title, folder_id=None) -> str`

### 5.7 Fixture capture tooling (required)
Provide scripts to capture and sanitize fixtures:
- `scripts/fetch_fixture_doc.py --doc-id ... --out tests/fixtures/docs/...json`
- `scripts/fetch_fixture_comments.py --file-id ... --out tests/fixtures/comments/...json`
- `scripts/sanitize_fixture.py` removes unstable fields (timestamps, revision IDs) and any PII.

Goal: deterministic unit tests with real-world coverage without manual JSON wrangling.

## 6. Operational guardrails

### 6.1 Refresh token stability policy
- Mint refresh token once; reuse.
- Avoid repeated full-consent flows.
- Avoid OAuth Playground for CI/dev.
- Keep OAuth consent screen out of “Testing” mode.

### 6.2 Sensitive scope policy (development time)
- Use minimal scopes that still support your features.
- Accept “unverified app” warnings during development.

## 7. Milestones

1. Repo scaffold + `uv` + unit workflow green
2. Core model + converter skeleton (fixture-based)
3. Auth bootstrap script working + documented
4. Integration workflow green on `workflow_dispatch` with secrets
5. MCP server layer using adapter interface
6. Fixture capture + sanitization scripts

## 8. Acceptance criteria (definition of done)

- Cloud agent can:
  - clone repo
  - run `uv run pytest` successfully with no secrets (Tier A)
- Maintainer can:
  - run `scripts/bootstrap_google_refresh_token.py` to mint a token
  - set GitHub secrets
  - run integration workflow_dispatch successfully (Tier B)
- MCP server can run locally with `.env` credentials and successfully:
  - read a doc
  - apply a batchUpdate
  - read comments (if included)
- Secrets never appear in logs or committed files.

## 9. Resolved decisions and remaining considerations

### 9.1 Resolved decisions (from user)
- MCP server runs **locally** for now.
- Must support both **consumer Gmail** and **Google Workspace** accounts.
- Scopes: those required for **Google Drive CRUD** and **Google Docs CRUD**.
- Bootstrap utility must support `--publish` to push credentials to local env and GitHub secrets.
- Integration tests should run on **every PR to `main`** (with secure gating for forks).
- Integration tests must be runnable:
  - locally
  - in GitHub Actions
  - by cloud coding agents (via same-repo branches or maintainer-triggered runs)
- Token storage: **single-user** initially for simplicity.

### 9.2 Remaining considerations (to avoid future rework)
1. **Workspace admin restrictions:** some domains may block unverified OAuth apps or restrict third-party access. Document a troubleshooting section in `README.md` for common admin-policy failures.
2. **Dedicated test resources:** decide whether integration tests operate on:
   - a pre-created `TEST_DOC_ID`, or
   - a test folder where tests create and delete docs each run (recommended for isolation).
3. **Quotas and flakiness controls:** set conservative retry/backoff for transient 429/5xx responses in integration tests.
4. **Secret rotation procedure:** document a short “regen refresh token + publish secrets” playbook.

