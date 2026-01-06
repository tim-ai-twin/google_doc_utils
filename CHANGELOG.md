# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version Format

This project uses **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

## Release Process

1. Update this CHANGELOG.md with changes under a new version heading
2. Update version in `pyproject.toml`
3. Create a git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push the tag: `git push origin vX.Y.Z`
5. Create GitHub release from the tag

## [Unreleased]

## [0.1.0] - 2026-01-05

### Added

- OAuth 2.0 authentication with Google APIs
  - `CredentialManager` for loading/saving credentials from files and environment
  - `OAuthFlow` for interactive desktop authorization
  - `PreflightCheck` for validating credentials before test runs
- Google Docs API client (`GoogleDocsClient`)
  - Document retrieval and text extraction
  - Document creation
- Google Drive API client (`DriveClient`)
  - Basic file operations
- Test infrastructure
  - Tier A tests (mocked, no credentials required)
  - Tier B tests (integration tests with real API)
  - `TestResourceManager` for tracking and cleaning up test resources
- Environment detection for local development, GitHub Actions, and cloud agents
- Pre-commit hooks with ruff formatting

### Security

- Credentials stored with restricted file permissions (0600)
- Support for environment variable-based credentials in CI/CD
