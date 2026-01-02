# Feature Specification: Cloud Testing Infrastructure with OAuth

**Feature Branch**: `001-cloud-testing-oauth`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "1. Project structure (Python + uv) to enable local + cloud agent + GitHub Actions testing
2. OAuth plan (desktop OAuth with local callback to get refresh token, env-based refresh token for agent + cloud testing). Single user only for now."

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Two-Tier Test Strategy (Priority: P0 - Foundation)

The project must support two distinct tiers of testing to enable development by cloud agents, local developers, and CI systems with varying levels of credential access. Tier A tests run without any Google credentials (using fixtures and mocks), while Tier B tests run against real Google APIs requiring valid OAuth credentials.

**Why this priority**: This is the foundational architecture that enables all other testing scenarios. Without Tier A (credential-free) tests, cloud agents cannot contribute code safely. Without Tier B (credential-required) tests, we cannot validate real API integration. This distinction is critical for security and accessibility.

**Independent Test**: Can be fully tested by running Tier A tests without any credentials configured and verifying they pass, then running Tier B tests with credentials and verifying they interact with real Google APIs.

**Acceptance Scenarios**:

1. **Given** no OAuth credentials are configured, **When** Tier A tests are executed, **Then** all Tier A tests run successfully using fixtures and mocks without requiring network access to Google APIs
2. **Given** valid OAuth credentials are configured, **When** Tier B tests are executed, **Then** all Tier B tests run successfully making real calls to Google Docs and Drive APIs
3. **Given** a cloud agent with no credential access, **When** the agent runs the test suite, **Then** all Tier A tests execute successfully and Tier B tests are skipped with a clear message indicating credentials are required
4. **Given** Tier A tests are running, **When** network connectivity is lost, **Then** Tier A tests continue to pass because they do not require network access
5. **Given** Tier B tests are running with invalid credentials, **When** tests attempt to authenticate, **Then** all Tier B tests are immediately aborted with a clear authentication error

---

### User Story 1 - Local Development Testing (Priority: P1)

A developer working on the extended-google-doc-utils library needs to run unit and integration tests locally on their machine. They want to authenticate once using their Google account and have their credentials persist for subsequent test runs without repeated login prompts.

**Why this priority**: Local testing is the foundation of development workflow. Without reliable local testing, developers cannot validate changes before committing code. This is the minimum viable product that enables basic development.

**Independent Test**: Can be fully tested by running the test suite locally after initial OAuth setup and verifying that tests execute successfully without requiring repeated authentication.

**Acceptance Scenarios**:

1. **Given** a developer has not authenticated yet, **When** they run the test suite for the first time, **Then** they are prompted to complete OAuth authentication via browser and tests execute successfully after authentication
2. **Given** a developer has previously authenticated with valid credentials, **When** they run the test suite again, **Then** tests execute successfully without requiring re-authentication
3. **Given** the refresh token has expired or been revoked, **When** the developer runs tests, **Then** all tests are immediately aborted with a clear error message and the developer must re-authenticate before tests can continue

---

### User Story 2 - GitHub Actions CI/CD Testing (Priority: P2)

The project maintainer wants automated tests to run on every pull request and push to main branch using GitHub Actions. The CI environment should authenticate using pre-configured credentials stored as GitHub secrets, run the full test suite, and report results without manual intervention. To protect credentials, integration tests (Tier B) must only run automatically for pull requests from branches within the same repository, not from forks. For fork pull requests, maintainers can manually trigger integration tests after reviewing the code.

**Why this priority**: Automated CI/CD testing provides continuous quality assurance and prevents regressions. This builds on local testing (P1) by adding automation, making it the logical next step after establishing the testing foundation. Fork PR security is critical to prevent untrusted code from accessing credentials.

**Independent Test**: Can be fully tested by creating pull requests from both same-repo branches and forks, verifying that integration tests run automatically for same-repo PRs, skip for fork PRs, and can be manually triggered by maintainers for fork PRs.

**Acceptance Scenarios**:

1. **Given** GitHub secrets are configured with valid OAuth credentials and a PR is created from a branch in the same repository, **When** the PR targets the main branch, **Then** Tier A tests run automatically, Tier B tests run automatically with authentication, and all results are visible in the PR
2. **Given** a pull request is created from a forked repository, **When** the PR targets the main branch, **Then** Tier A tests run automatically but Tier B tests are skipped with a clear message indicating they require maintainer approval
3. **Given** a pull request from a fork has been reviewed by a maintainer, **When** the maintainer manually triggers the integration test workflow, **Then** Tier B tests execute with credentials and results are visible in the PR
4. **Given** tests are running in GitHub Actions, **When** a test fails, **Then** the workflow fails and reports the specific test failures
5. **Given** the refresh token in GitHub secrets is invalid or expired, **When** GitHub Actions attempts to run Tier B tests, **Then** all Tier B tests are immediately aborted, the workflow fails, and a clear error message indicates that a human user must update the GitHub secrets with fresh OAuth credentials

---

### User Story 3 - Cloud Agent Testing (Priority: P3)

A cloud-based AI agent needs to run tests as part of autonomous development workflows. The agent should authenticate using environment-based credentials and execute tests in a cloud environment without interactive authentication flows.

**Why this priority**: Cloud agent testing enables autonomous AI-assisted development. This is valuable but depends on the foundation of local testing (P1) and follows the same pattern as GitHub Actions (P2), making it a natural extension rather than a core requirement.

**Independent Test**: Can be fully tested by configuring a cloud agent environment with OAuth credentials, triggering a test run from the agent, and verifying successful authentication and test execution.

**Acceptance Scenarios**:

1. **Given** a cloud agent environment has valid OAuth credentials configured, **When** the agent initiates a test run, **Then** authentication succeeds and tests execute without user interaction
2. **Given** tests are running in a cloud agent, **When** tests complete, **Then** results are available to the agent for analysis and decision-making
3. **Given** the agent's OAuth credentials are missing, invalid, or expired, **When** the agent attempts to run tests, **Then** all tests are immediately aborted and a clear error is returned indicating that a human user must provide fresh OAuth credentials

---

### User Story 4 - Proof of Concept Integration Test (Priority: P1 - High)

A developer or automated test runner needs to verify that the OAuth authentication and Google Docs API integration actually work end-to-end. A simple integration test reads a known Google Doc and extracts its first word to prove the system can successfully authenticate and interact with Google Docs.

**Why this priority**: This is a proof-of-concept test that validates the entire authentication and API integration chain. Without this working, the infrastructure has no proven value. This should be implemented alongside User Story 1 as it validates that the local testing setup actually works.

**Independent Test**: Can be fully tested by running the integration test against the known Google Doc URL (https://docs.google.com/document/d/1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4/edit?tab=t.0) and verifying it returns "Gondwana" as the first word.

**Acceptance Scenarios**:

1. **Given** valid OAuth credentials are configured, **When** the integration test runs, **Then** it successfully authenticates, reads the specified Google Doc, extracts the first word "Gondwana", and the test passes
2. **Given** the integration test has run successfully before, **When** it runs again with cached credentials, **Then** it completes without re-authentication and still returns "Gondwana"
3. **Given** invalid or expired credentials, **When** the integration test runs, **Then** it immediately aborts with a clear authentication error before attempting to read the document
4. **Given** the specified Google Doc is inaccessible or deleted, **When** the integration test runs, **Then** it fails with a clear error indicating the document cannot be accessed
5. **Given** the document content changes and no longer starts with "Gondwana", **When** the integration test runs, **Then** it fails with a clear assertion error showing the expected vs actual first word

---

### Edge Cases

#### Two-Tier Testing

- What happens when Tier A tests are run but fixtures are missing or corrupted?
- What happens when a test is incorrectly categorized as Tier A but attempts to make network calls?
- What happens when Tier B tests are run without credentials in a local development environment?
- What happens when both Tier A and Tier B tests are run together and credentials are invalid?

#### OAuth & Authentication

- What happens when the OAuth callback server port is already in use during desktop authentication?
- What happens when network connectivity is lost during the OAuth flow?
- What happens when the refresh token is revoked by the user through their Google account settings?
- What happens when multiple test processes attempt to refresh the access token simultaneously?
- What happens when environment variables for OAuth credentials are malformed or incomplete?
- What happens when the requested OAuth scopes are denied by the user during authentication?
- What happens when a Google Workspace administrator has blocked the OAuth application?
- What happens when authentication fails partway through a test suite execution?
- What happens when the access token expires during a long-running single test?

#### GitHub Actions & Fork PRs

- What happens when a fork PR is created and integration tests are skipped but the PR author expects them to run?
- What happens when a maintainer manually triggers integration tests for a fork PR but credentials are invalid?
- What happens when a same-repo PR is created from a branch with malicious code that attempts to exfiltrate credentials?
- What happens when GitHub secrets are accidentally deleted while integration tests are running?

#### Google API & Resources

- What happens when the Google API quota is exceeded during test execution?
- What happens when tests run in an environment without internet connectivity?
- What happens when the proof-of-concept Google Doc is inaccessible or deleted?
- What happens when the proof-of-concept Google Doc content changes?
- What happens when the Google Doc has no content or is empty?
- What happens when the user's Google account doesn't have permission to access the test document?
- What happens when requested OAuth scopes are insufficient for the operations being tested?

## Requirements *(mandatory)*

### Functional Requirements

#### Test Strategy

- **FR-001**: System MUST support two distinct test tiers: Tier A (credential-free tests using fixtures and mocks) and Tier B (credential-required tests using real Google APIs)
- **FR-002**: Tier A tests MUST execute successfully without any OAuth credentials or network access to Google APIs
- **FR-003**: Tier B tests MUST execute successfully with valid OAuth credentials and make real calls to Google Docs and Drive APIs
- **FR-004**: System MUST clearly indicate which tests are Tier A and which are Tier B
- **FR-005**: When credentials are not available, Tier B tests MUST be skipped with a clear message rather than failing

#### Authentication & Credentials

- **FR-006**: Project MUST support local test execution with developer-initiated OAuth authentication via browser
- **FR-007**: Project MUST support automated test execution in GitHub Actions using environment-based OAuth credentials
- **FR-008**: Project MUST support automated test execution in cloud agent environments using environment-based OAuth credentials
- **FR-009**: System MUST persist OAuth refresh tokens locally for subsequent test runs without re-authentication
- **FR-010**: System MUST provide a desktop OAuth flow with local callback server to capture authorization codes
- **FR-011**: System MUST support single-user authentication only (no multi-user credential management)
- **FR-012**: System MUST automatically refresh expired access tokens using stored refresh tokens when refresh tokens are valid
- **FR-013**: System MUST clearly differentiate between local development mode (interactive OAuth) and automated mode (environment-based OAuth)
- **FR-014**: System MUST immediately abort all tests when authentication fails or credentials are rejected
- **FR-015**: System MUST provide clear error messages when authentication fails, indicating that human re-authentication is required
- **FR-016**: System MUST support configuration of OAuth credentials through environment variables for automated environments
- **FR-017**: System MUST prevent storage of OAuth credentials in version control
- **FR-018**: System MUST validate OAuth credentials before attempting to run tests
- **FR-019**: System MUST NOT attempt automatic recovery or retry when credentials are rejected or invalid

#### OAuth Scopes & Permissions

- **FR-020**: System MUST request OAuth scopes that enable full CRUD (Create, Read, Update, Delete) operations on Google Docs
- **FR-021**: System MUST request OAuth scopes that enable file management operations on Google Drive
- **FR-022**: System MUST use the minimal set of OAuth scopes necessary for Google Docs and Drive CRUD operations

#### Bootstrap & Credential Setup

- **FR-023**: System MUST provide a bootstrap utility that guides users through initial OAuth authentication to obtain a refresh token
- **FR-024**: Bootstrap utility MUST support both consumer Gmail accounts and Google Workspace accounts
- **FR-025**: Bootstrap utility MUST output credentials in a format suitable for both local development and CI environments

#### GitHub Actions Integration

- **FR-026**: GitHub Actions workflows MUST run Tier A tests automatically on all pull requests regardless of source (same-repo or fork)
- **FR-027**: GitHub Actions workflows MUST run Tier B tests automatically only on pull requests from branches within the same repository
- **FR-028**: GitHub Actions workflows MUST skip Tier B tests on pull requests from forked repositories with a clear message
- **FR-029**: GitHub Actions workflows MUST support manual triggering of Tier B tests by maintainers for reviewed fork pull requests
- **FR-030**: GitHub Actions workflows MUST NOT expose credentials to untrusted fork pull request code

#### Project Structure & Compatibility

- **FR-031**: Project structure MUST be compatible with standard package managers and dependency management tools
- **FR-032**: Tests MUST be discoverable and executable through standard test runners
- **FR-033**: System MUST abort test execution immediately upon detecting authentication failure during test runs

#### Proof-of-Concept Integration Test

- **FR-034**: System MUST include a proof-of-concept integration test that reads a specific Google Doc and extracts its first word
- **FR-035**: Proof-of-concept test MUST target the document at https://docs.google.com/document/d/1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4/edit?tab=t.0
- **FR-036**: Proof-of-concept test MUST verify the first word of the document is "Gondwana"
- **FR-037**: Proof-of-concept test MUST fail with a clear error if the document is inaccessible or deleted
- **FR-038**: Proof-of-concept test MUST fail with a clear assertion error if the first word does not match "Gondwana"
- **FR-039**: Proof-of-concept test MUST execute using the same authentication flow as all other Tier B tests

### Key Entities

- **OAuth Credentials**: Contains access token (short-lived, grants API access), refresh token (long-lived, used to obtain new access tokens), token expiry timestamp, and OAuth client configuration (client ID, client secret, scopes, redirect URI)
- **Test Configuration**: Defines authentication mode (interactive desktop flow vs environment-based), credential storage location (local file path vs environment variable names), test execution environment (local, GitHub Actions, cloud agent), and test suite parameters
- **Test Execution Context**: Tracks current access token validity, authentication state (authenticated, needs refresh, needs re-authentication), test environment detection (local, CI, cloud), and credential source (local file, environment variables)
- **Proof-of-Concept Test**: Represents the integration test that validates end-to-end functionality, including target document identifier (1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4), expected first word ("Gondwana"), test result (pass/fail), and failure reason (authentication error, document access error, assertion error)

### Assumptions

- Developers have Google accounts (consumer Gmail or Google Workspace) with appropriate API access permissions
- Project maintainers have the ability to configure GitHub repository secrets
- Cloud agents have environment variable configuration capabilities
- OAuth client credentials (client ID and secret) are provided by project administrators
- Google API quotas are sufficient for expected test execution frequency
- Tier A tests use fixtures and mocks to enable testing without Google API access
- Tier B tests require actual Google API access (not mocked) for integration testing
- Standard OAuth 2.0 desktop application flow is acceptable for local development
- Credential persistence duration is determined entirely by Google's OAuth policies, not by this project
- Human intervention is acceptable and required when credentials expire or are revoked
- Test suite execution can be safely aborted at any point without leaving system in inconsistent state
- OAuth scopes `https://www.googleapis.com/auth/documents` and `https://www.googleapis.com/auth/drive.file` (or broader `drive` scope) provide sufficient permissions for Google Docs and Drive CRUD operations
- The proof-of-concept Google Doc (ID: 1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4) remains accessible and its content starts with "Gondwana"
- The authenticated user has read permissions for the proof-of-concept Google Doc
- The proof-of-concept test serves as a smoke test to validate the entire authentication and API integration chain
- Fork pull requests cannot be automatically trusted with repository secrets
- Maintainers review fork pull requests before manually triggering integration tests

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can complete initial OAuth setup and run tests locally in under 5 minutes
- **SC-002**: Subsequent local test runs execute without requiring re-authentication as long as Google's OAuth policies allow credential persistence
- **SC-003**: GitHub Actions workflows authenticate and complete test suites in under 10 minutes per run when credentials are valid
- **SC-004**: Cloud agents authenticate and execute tests without human intervention 100% of the time when credentials are valid
- **SC-005**: Authentication failures immediately abort all tests with zero tests executing on invalid credentials
- **SC-006**: Authentication failure error messages provide actionable guidance that enables resolution within 2 minutes
- **SC-007**: Zero OAuth credentials are committed to version control (verified through automated checks)
- **SC-008**: Test execution succeeds across all three environments (local, GitHub Actions, cloud agent) using the same test suite when credentials are valid
- **SC-009**: Proof-of-concept integration test successfully reads the target Google Doc and extracts "Gondwana" as the first word in under 5 seconds
- **SC-010**: Proof-of-concept test passes 100% of the time when valid credentials exist and the document is accessible
- **SC-011**: Proof-of-concept test provides clear failure diagnostics distinguishing between authentication errors, document access errors, and content assertion errors
- **SC-012**: Tier A tests execute successfully without credentials 100% of the time in all environments (local, GitHub Actions, cloud agents)
- **SC-013**: Cloud agents can run Tier A tests and contribute code without requiring access to OAuth credentials
- **SC-014**: Bootstrap utility guides users through OAuth setup and outputs valid credentials in under 5 minutes for both Gmail and Workspace accounts
- **SC-015**: Fork pull requests trigger Tier A tests automatically but Tier B tests are skipped 100% of the time without manual approval
- **SC-016**: Maintainers can manually trigger Tier B tests for reviewed fork PRs in under 1 minute
- **SC-017**: Zero credentials are exposed to untrusted fork PR code (verified through security audits)
- **SC-018**: OAuth scopes requested enable all required Google Docs and Drive CRUD operations without requesting unnecessary permissions
