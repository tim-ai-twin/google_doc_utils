# GitHub Environments Configuration

This document describes the environment configuration required for CI/CD workflows.

## Required Secrets

The following secrets must be configured in GitHub repository settings for Tier B tests to run:

| Secret | Description |
|--------|-------------|
| `TIER_B_OAUTH_REFRESH_TOKEN` | OAuth 2.0 refresh token for Google API access |
| `CLIENT_ID` | Google OAuth 2.0 client ID |
| `CLIENT_SECRET` | Google OAuth 2.0 client secret |

### Obtaining OAuth Credentials

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Docs API and Google Drive API
3. Create OAuth 2.0 credentials (Desktop application type)
4. Download the client configuration to get `CLIENT_ID` and `CLIENT_SECRET`
5. Run the local OAuth flow to obtain a refresh token

### Configuring Secrets

Add these secrets in GitHub under:
**Settings → Secrets and variables → Actions → Repository secrets**
