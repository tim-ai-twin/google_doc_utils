# Tasks: Cloud Testing Infrastructure with OAuth

**Input**: Design documents from `/specs/001-cloud-testing-oauth/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature implements testing infrastructure. Test tasks are included as this is the core deliverable.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US2.5, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Single Python project**: `src/extended_google_doc_utils/`, `tests/`, `scripts/` at repository root
- Using `uv` for package management with `pyproject.toml` configuration

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic Python package structure

- [ ] T001 Create project structure with src/ layout per plan.md
- [ ] T002 Initialize pyproject.toml with uv, Python 3.11+, and core dependencies
- [ ] T003 Create .python-version file specifying Python 3.11
- [ ] T004 [P] Create .gitignore excluding .credentials/, __pycache__, *.pyc, .pytest_cache/, htmlcov/
- [ ] T005 [P] Create README.md with project overview and setup instructions
- [ ] T006 [P] Configure pytest in pyproject.toml with custom markers (tier_a, tier_b)
- [ ] T007 [P] Create directory structure: src/extended_google_doc_utils/{auth,google_api,utils}
- [ ] T008 [P] Create directory structure: tests/{tier_a,tier_b,fixtures}
- [ ] T009 [P] Create scripts/ directory for bootstrap and cleanup utilities

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Create src/extended_google_doc_utils/__init__.py with package metadata
- [ ] T011 [P] Create src/extended_google_doc_utils/auth/__init__.py
- [ ] T012 [P] Create src/extended_google_doc_utils/google_api/__init__.py
- [ ] T013 [P] Create src/extended_google_doc_utils/utils/__init__.py
- [ ] T014 [P] Create tests/__init__.py and tests/conftest.py skeleton
- [ ] T015 Implement EnvironmentType enum in src/extended_google_doc_utils/utils/config.py
- [ ] T016 [P] Implement CredentialSource enum in src/extended_google_doc_utils/auth/credential_manager.py
- [ ] T017 [P] Implement OAuthCredentials dataclass in src/extended_google_doc_utils/auth/credential_manager.py
- [ ] T018 Implement environment detection logic in src/extended_google_doc_utils/utils/config.py
- [ ] T019 Add pytest custom markers (tier_a, tier_b) in tests/conftest.py
- [ ] T020 Create fixture files: tests/fixtures/google_docs_responses.json (empty initially)
- [ ] T021 [P] Create fixture files: tests/fixtures/google_drive_responses.json (empty initially)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Two-Tier Test Strategy (Priority: P0 - Foundation) 🎯 CRITICAL

**Goal**: Enable credential-free testing (Tier A) and credential-required testing (Tier B) to support cloud agents, local developers, and CI systems

**Independent Test**: Run Tier A tests without credentials (should pass), then run Tier B tests with credentials (should interact with real APIs)

### Implementation for User Story 0

- [ ] T022 [P] [US0] Implement pytest marker registration for tier_a and tier_b in tests/conftest.py
- [ ] T023 [P] [US0] Create example mock fixtures for Google Docs API in tests/fixtures/google_docs_responses.json
- [ ] T024 [P] [US0] Create example mock fixtures for Google Drive API in tests/fixtures/google_drive_responses.json
- [ ] T025 [US0] Implement tier detection logic in tests/conftest.py to skip Tier B when no credentials
- [ ] T026 [US0] Create fixture loader utility in tests/fixtures/__init__.py
- [ ] T027 [P] [US0] Write Tier A example test using mocks in tests/tier_a/test_config_loading.py
- [ ] T028 [P] [US0] Write documentation in tests/tier_a/README.md explaining Tier A tests
- [ ] T029 [P] [US0] Write documentation in tests/tier_b/README.md explaining Tier B tests

**Checkpoint**: Two-tier strategy infrastructure complete - tests can be categorized and executed based on credential availability

---

## Phase 4: User Story 1 - Local Development Testing (Priority: P1) 🎯 MVP

**Goal**: Enable developers to authenticate once and run tests locally with persisted credentials

**Independent Test**: Run bootstrap_oauth.py, authenticate via browser, then run pytest and verify tests execute without re-authentication

### Implementation for User Story 1

- [ ] T030 [P] [US1] Implement CredentialManager class in src/extended_google_doc_utils/auth/credential_manager.py
- [ ] T031 [P] [US1] Implement OAuthFlow class in src/extended_google_doc_utils/auth/oauth_flow.py
- [ ] T032 [US1] Implement load_credentials() method for LOCAL_FILE source in CredentialManager
- [ ] T033 [US1] Implement save_credentials() method for LOCAL_FILE in CredentialManager
- [ ] T034 [US1] Implement refresh_access_token() method using google.auth in CredentialManager
- [ ] T035 [US1] Implement get_credentials_for_testing() convenience method in CredentialManager
- [ ] T036 [US1] Implement run_interactive_flow() for desktop OAuth in OAuthFlow
- [ ] T037 [US1] Implement local callback server in src/extended_google_doc_utils/auth/oauth_flow.py
- [ ] T038 [US1] Add port fallback logic (8080-8089) for callback server
- [ ] T039 [US1] Implement exchange_code_for_tokens() in OAuthFlow
- [ ] T040 [US1] Create bootstrap_oauth.py script in scripts/
- [ ] T041 [US1] Add interactive prompts and instructions to bootstrap_oauth.py
- [ ] T042 [US1] Add credential validation test API call in bootstrap_oauth.py
- [ ] T043 [US1] Output credentials in environment variable format in bootstrap_oauth.py
- [ ] T044 [P] [US1] Write Tier A test for credential loading logic in tests/tier_a/test_auth_logic.py
- [x] T045 [P] [US1] OAuth flow tested via bootstrap_oauth.py (dedicated test removed as redundant)
- [ ] T046 [US1] Create pytest fixture for loading credentials in tests/conftest.py
- [ ] T047 [US1] Add error handling for expired/revoked tokens with clear messages

**Checkpoint**: Local developers can authenticate, persist credentials, and run tests without repeated logins

---

## Phase 5: User Story 2.5 - Credential Pre-Flight Check (Priority: P1)

**Goal**: Validate credentials before running any Tier B tests to provide fast failure with clear error messages

**Independent Test**: Simulate invalid credentials and verify pre-flight check detects issue before tests run

### Implementation for User Story 2.5

- [ ] T048 [P] [US2.5] Implement PreflightCheckResult dataclass in src/extended_google_doc_utils/auth/preflight_check.py
- [ ] T049 [US2.5] Implement PreflightCheck class in src/extended_google_doc_utils/auth/preflight_check.py
- [ ] T050 [US2.5] Implement run() method making lightweight Drive API call in PreflightCheck
- [ ] T051 [US2.5] Add timing measurement (<2s target) in PreflightCheck.run()
- [ ] T052 [US2.5] Implement validate_and_report() with console output in PreflightCheck
- [ ] T053 [US2.5] Create session-scoped pytest fixture for pre-flight check in tests/conftest.py
- [ ] T054 [US2.5] Add auto-skip logic for Tier B tests when pre-flight fails in tests/conftest.py
- [ ] T055 [US2.5] Display bootstrap command instructions in pre-flight error messages
- [ ] T056 [P] [US2.5] Write Tier A test for pre-flight check logic in tests/tier_a/test_preflight_logic.py
- [ ] T057 [P] [US2.5] Write Tier B test validating pre-flight check in tests/tier_b/test_preflight_check.py

**Checkpoint**: Pre-flight check catches credential failures in <2 seconds before any tests run

---

## Phase 6: User Story 4 - Proof of Concept Integration Test (Priority: P1 - High)

**Goal**: Validate end-to-end OAuth and API integration by reading the "Gondwana" document

**Independent Test**: Run test against document ID 1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4 and verify it returns "Gondwana"

### Implementation for User Story 4

- [ ] T058 [P] [US4] Implement GoogleDocsClient class in src/extended_google_doc_utils/google_api/docs_client.py
- [ ] T059 [P] [US4] Implement GoogleDriveClient class in src/extended_google_doc_utils/google_api/drive_client.py
- [ ] T060 [US4] Implement get_document() method in GoogleDocsClient
- [ ] T061 [US4] Implement extract_text() method in GoogleDocsClient
- [ ] T062 [US4] Implement extract_first_word() method in GoogleDocsClient
- [ ] T063 [US4] Implement create_document() method in GoogleDocsClient
- [ ] T064 [US4] Implement get_user_info() method in GoogleDriveClient (for pre-flight)
- [ ] T065 [US4] Implement delete_file() method in GoogleDriveClient
- [ ] T066 [US4] Write proof-of-concept test in tests/tier_b/test_proof_of_concept.py
- [ ] T067 [US4] Add assertions for "Gondwana" first word in test_proof_of_concept.py
- [ ] T068 [US4] Add error handling for document inaccessible scenario
- [ ] T069 [US4] Add error handling for content mismatch scenario
- [ ] T070 [P] [US4] Create mock fixture for Gondwana document in tests/fixtures/google_docs_responses.json
- [ ] T071 [P] [US4] Write Tier A test for document parsing logic in tests/tier_a/test_docs_parsing.py

**Checkpoint**: Proof-of-concept test validates entire authentication and API integration chain

---

## Phase 7: User Story 2 - GitHub Actions CI/CD Testing (Priority: P2)

**Goal**: Enable automated testing in GitHub Actions with environment-based credentials and approval gates

**Independent Test**: Create PR from fork and same-repo branch, verify Tier A runs automatically and Tier B requires approval

### Implementation for User Story 2

- [ ] T072 [US2] Implement load_credentials() for ENVIRONMENT source in CredentialManager
- [ ] T073 [US2] Add environment variable parsing (GOOGLE_OAUTH_REFRESH_TOKEN, etc.) in CredentialManager
- [ ] T074 [US2] Add environment variable validation with clear error messages
- [ ] T075 [P] [US2] Create .github/workflows/tier-a-tests.yml workflow file
- [ ] T076 [P] [US2] Create .github/workflows/tier-b-tests.yml workflow file with environment protection
- [ ] T077 [US2] Configure Tier A workflow to run on all PRs automatically
- [ ] T078 [US2] Configure Tier B workflow to require tier-b-testing environment
- [ ] T079 [US2] Add uv setup and dependency installation steps to workflows
- [ ] T080 [US2] Add pytest execution with appropriate markers to workflows
- [ ] T081 [P] [US2] Create .github/environments/README.md with setup instructions
- [ ] T082 [US2] Document environment secret configuration in README.md
- [ ] T083 [US2] Add workflow status badge suggestions to main README.md
- [ ] T084 [P] [US2] Write Tier A test for environment-based credential loading in tests/tier_a/test_auth_logic.py

**Checkpoint**: GitHub Actions runs Tier A automatically, Tier B waits for maintainer approval with credentials protected

---

## Phase 8: User Story 5 - Test Resource Isolation (Priority: P2)

**Goal**: Enable parallel test execution with dynamic resource creation and unique identifiers

**Independent Test**: Run multiple test suites simultaneously and verify each creates unique resources with minimal conflicts

### Implementation for User Story 5

- [ ] T085 [P] [US5] Implement TestResourceMetadata dataclass in src/extended_google_doc_utils/utils/test_resources.py
- [ ] T086 [P] [US5] Implement ResourceType enum in src/extended_google_doc_utils/utils/test_resources.py
- [ ] T087 [US5] Implement TestResourceManager class in src/extended_google_doc_utils/utils/test_resources.py
- [ ] T088 [US5] Implement generate_unique_title() with timestamp + random suffix
- [ ] T089 [US5] Implement create_document() with tracking in TestResourceManager
- [ ] T090 [US5] Implement create_folder() with tracking in TestResourceManager
- [ ] T091 [US5] Implement cleanup_resource() best-effort deletion in TestResourceManager
- [ ] T092 [US5] Implement cleanup_all() method in TestResourceManager
- [ ] T093 [US5] Implement list_orphaned_resources() method in TestResourceManager
- [ ] T094 [US5] Create isolated_document() context manager in src/extended_google_doc_utils/utils/test_resources.py
- [ ] T095 [US5] Create isolated_folder() context manager in src/extended_google_doc_utils/utils/test_resources.py
- [ ] T096 [US5] Create pytest fixture for TestResourceManager in tests/conftest.py
- [ ] T097 [US5] Add automatic cleanup in pytest session teardown
- [ ] T098 [P] [US5] Write Tier B test for resource isolation in tests/tier_b/test_resource_isolation.py
- [ ] T099 [US5] Test parallel execution scenarios in test_resource_isolation.py
- [ ] T100 [US5] Create cleanup_test_resources.py script in scripts/
- [ ] T101 [US5] Add orphaned resource identification to cleanup script
- [ ] T102 [US5] Add interactive confirmation prompts to cleanup script

**Checkpoint**: Tests can run in parallel creating unique resources, with best-effort cleanup and manual cleanup script

---

## Phase 9: User Story 3 - Cloud Agent Testing (Priority: P3)

**Goal**: Enable cloud agents to run Tier A tests and skip Tier B tests with clear messaging

**Independent Test**: Configure cloud agent environment, run test suite, verify Tier A passes and Tier B skips gracefully

### Implementation for User Story 3

- [ ] T103 [US3] Add CLOUD_AGENT environment variable detection in EnvironmentType.detect()
- [ ] T104 [US3] Update credential source selection logic for cloud agents
- [ ] T105 [US3] Add clear skip messages for Tier B tests in cloud agent mode
- [ ] T106 [US3] Document cloud agent setup in quickstart.md (already done in planning)
- [ ] T107 [P] [US3] Add cloud agent examples to README.md
- [ ] T108 [P] [US3] Create tests/tier_a/README.md section for cloud agents

**Checkpoint**: Cloud agents can run Tier A tests and contribute code without credential access

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T109 [P] Add type hints throughout codebase (mypy --strict compliance)
- [ ] T110 [P] Add docstrings to all public classes and methods
- [ ] T111 [P] Configure pre-commit hooks for formatting (black, isort)
- [ ] T112 [P] Configure pre-commit hooks for linting (ruff)
- [ ] T113 [P] Add pre-commit hook to prevent .credentials/ commits
- [ ] T114 Run pytest with coverage reporting (pytest-cov)
- [ ] T115 Validate coverage meets minimum threshold (80%+)
- [ ] T116 [P] Update main README.md with badges (CI status, coverage)
- [ ] T117 [P] Add CONTRIBUTING.md with development workflow
- [ ] T118 [P] Add LICENSE file (if not already present)
- [ ] T119 Review and update all error messages for clarity and actionability
- [ ] T120 Add logging configuration with appropriate levels
- [ ] T121 Test quickstart.md steps manually as new developer
- [ ] T122 Test bootstrap_oauth.py with both Gmail and Workspace accounts
- [ ] T123 Test GitHub Actions workflows end-to-end with test PRs
- [ ] T124 Performance validation: Pre-flight check <2s, proof-of-concept test <5s
- [ ] T125 Security audit: Verify no credentials in git history or public files
- [ ] T126 Create release notes and version tagging strategy
- [ ] T127 [P] Add architecture diagram to docs/ (optional)
- [ ] T128 Final end-to-end testing across all three environments (local, GitHub Actions, cloud agent simulation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US0 (Two-Tier Strategy): Foundation for all other testing
  - US1 (Local Development): Core MVP, depends on US0
  - US2.5 (Pre-flight Check): Enhances US1, can run in parallel with US4
  - US4 (Proof of Concept): Validates infrastructure, can run in parallel with US2.5
  - US2 (GitHub Actions): Extends US1 to CI/CD
  - US5 (Resource Isolation): Extends US4 for parallel testing
  - US3 (Cloud Agent): Minimal, leverages US0 Tier A infrastructure
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 0 (P0)**: Foundational - MUST complete before other stories
- **User Story 1 (P1)**: Depends on US0 - Core MVP
- **User Story 2.5 (P1)**: Depends on US1 - Enhances developer experience
- **User Story 4 (P1)**: Depends on US1 and US2.5 - Validates end-to-end
- **User Story 2 (P2)**: Depends on US1 - Extends to CI/CD
- **User Story 5 (P2)**: Depends on US4 - Enables parallel testing
- **User Story 3 (P3)**: Depends on US0 - Minimal cloud agent support

### Within Each User Story

- Core infrastructure before utilities
- Managers/services before clients
- Client implementation before tests
- Error handling after happy path
- Documentation alongside implementation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Within each user story, tasks marked [P] can run in parallel
- US2.5 and US4 can be developed in parallel after US1
- Tests in different tier_a/tier_b directories can be written in parallel
- Different user stories (after dependencies met) can be worked on by different developers

---

## Parallel Example: User Story 1

```bash
# Foundation tasks that can run together:
Task T030: "Implement CredentialManager class"
Task T031: "Implement OAuthFlow class"

# Test tasks that can run together:
Task T044: "Write Tier A test for credential loading"
Task T045: "Write Tier B test for OAuth flow"
```

## Parallel Example: User Story 4

```bash
# Client implementations that can run together:
Task T058: "Implement GoogleDocsClient class"
Task T059: "Implement GoogleDriveClient class"

# Test and fixture tasks that can run together:
Task T070: "Create mock fixture for Gondwana document"
Task T071: "Write Tier A test for document parsing"
```

## Parallel Example: User Story 5

```bash
# Core components that can run together:
Task T085: "Implement TestResourceMetadata dataclass"
Task T086: "Implement ResourceType enum"

# Context managers and tests that can run together after manager is complete:
Task T094: "Create isolated_document() context manager"
Task T095: "Create isolated_folder() context manager"
Task T098: "Write Tier B test for resource isolation"
```

---

## Implementation Strategy

### MVP First (User Story 0 + 1 + 2.5 + 4)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T021)
3. Complete Phase 3: User Story 0 - Two-Tier Strategy (T022-T029)
4. Complete Phase 4: User Story 1 - Local Development (T030-T047)
5. Complete Phase 5: User Story 2.5 - Pre-Flight Check (T048-T057)
6. Complete Phase 6: User Story 4 - Proof of Concept (T058-T071)
7. **STOP and VALIDATE**: Run full test suite locally
8. Verify developers can bootstrap OAuth and run tests

**MVP Deliverable**: Local developers can authenticate, run two-tier tests, and validate end-to-end integration

### Incremental Delivery

1. **Foundation** (Phases 1-3): Two-tier testing infrastructure ready
2. **MVP** (Phase 4): Local development works → Can start using library
3. **Enhanced MVP** (Phases 5-6): Pre-flight checks + proof of concept → Production-ready
4. **CI/CD** (Phase 7): GitHub Actions integration → Automated testing
5. **Advanced** (Phases 8-9): Resource isolation + cloud agents → Full feature set
6. **Production** (Phase 10): Polish and documentation → Release ready

### Parallel Team Strategy

With multiple developers:

1. **Team**: Complete Setup + Foundational together (T001-T021)
2. **Team**: Complete US0 together (T022-T029) - Foundation for all testing
3. **After US0 complete**:
   - **Developer A**: US1 (Local Development) - T030-T047
   - **Developer B**: Can prepare US2.5 scaffolding while A works
4. **After US1 complete**:
   - **Developer A**: US2.5 (Pre-flight Check) - T048-T057
   - **Developer B**: US4 (Proof of Concept) - T058-T071
5. **After MVP (US1+2.5+4)**:
   - **Developer A**: US2 (GitHub Actions) - T072-T084
   - **Developer B**: US5 (Resource Isolation) - T085-T102
   - **Developer C**: US3 (Cloud Agent) - T103-T108 (quick)
6. **All developers**: Polish together (T109-T128)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tier A tests use mocks/fixtures; Tier B tests use real Google APIs
- Pre-flight check is critical for good developer experience
- Resource isolation enables reliable parallel testing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Bootstrap script is the entry point for all new developers
- GitHub Actions workflows provide automated testing with security

---

## Task Summary

**Total Tasks**: 128
- Setup (Phase 1): 9 tasks
- Foundational (Phase 2): 12 tasks
- User Story 0 (P0): 8 tasks
- User Story 1 (P1): 18 tasks (MVP core)
- User Story 2.5 (P1): 10 tasks (MVP enhancement)
- User Story 4 (P1): 14 tasks (MVP validation)
- User Story 2 (P2): 13 tasks
- User Story 5 (P2): 18 tasks
- User Story 3 (P3): 6 tasks
- Polish (Phase 10): 20 tasks

**Parallel Tasks**: 58 tasks marked [P] can run in parallel within their phase

**MVP Scope** (User Stories 0, 1, 2.5, 4): 50 tasks + Setup + Foundational = 71 tasks

**Critical Path**: Setup → Foundational → US0 → US1 → US2.5 → US4 → Validate MVP

**Independent Test Criteria**:
- US0: Run pytest -m tier_a (no credentials) → all pass
- US1: Run bootstrap → run pytest → tests pass without re-auth
- US2.5: Simulate invalid credentials → pre-flight fails <2s
- US4: Run proof-of-concept test → reads "Gondwana"
- US2: Create test PR → Tier A auto-runs, Tier B waits for approval
- US5: Run parallel tests → unique resources created, cleanup succeeds
- US3: Set CLOUD_AGENT=true → Tier A passes, Tier B skips

**Format Validation**: ✓ All tasks follow `- [ ] [ID] [P?] [Story?] Description with file path` format
