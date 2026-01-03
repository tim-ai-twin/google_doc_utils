# Tier B Tests

## What are Tier B Tests?

Tier B tests are **credential-required integration tests** that make real API calls to Google services. Unlike Tier A tests (which use mocks and stubs), Tier B tests validate actual API interactions and end-to-end functionality.

**Characteristics:**
- Require valid OAuth credentials
- Make real HTTP requests to Google APIs
- Validate actual API responses and behavior
- May have slower execution times due to network calls
- Should be idempotent and safe to run repeatedly

## When to Write Tier B Tests

Write Tier B tests when you need to:

1. **Validate real API integration** - Ensure your code works with actual Google API responses
2. **Test credential flows** - Verify OAuth authentication and authorization work correctly
3. **Catch API changes** - Detect when Google updates their API contracts
4. **Test edge cases** - Validate behavior that's difficult to mock accurately (rate limits, quota, etc.)
5. **Integration testing** - Test the full stack from credentials through API calls to response handling

**General guideline:** Start with Tier A tests for logic and error handling, add Tier B tests for critical integration paths.

## How to Run Tier B Tests

Run all Tier B tests with the pytest marker:

```bash
pytest -m tier_b
```

Run specific Tier B test files:

```bash
pytest tests/tier_b/test_specific_feature.py
```

Run with verbose output:

```bash
pytest -m tier_b -v
```

## Credential Setup Requirements

Tier B tests require valid Google OAuth credentials. You must complete credential setup before running these tests.

### Prerequisites

1. **Google Cloud Project** - Create a project at https://console.cloud.google.com
2. **OAuth 2.0 Credentials** - Set up OAuth client ID and secret
3. **API Scopes** - Enable required Google APIs (Docs, Drive, etc.)
4. **Refresh Token** - Generate a refresh token for testing

### Setup Process

Use the `bootstrap_oauth.py` script to configure credentials:

```bash
python bootstrap_oauth.py
```

This script will:
- Guide you through OAuth consent flow
- Generate a refresh token
- Save credentials to `.credentials/oauth_credentials.json`
- Provide environment variable format for CI/CD

**Note:** The `.credentials/` directory is git-ignored to protect your secrets.

### Manual Setup

If you prefer manual setup, create `.credentials/oauth_credentials.json`:

```json
{
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "refresh_token": "your-refresh-token"
}
```

## Tier A vs Tier B

| Aspect | Tier A | Tier B |
|--------|--------|--------|
| Credentials | Not required | Required |
| API Calls | Mocked/stubbed | Real HTTP requests |
| Speed | Fast | Slower |
| Purpose | Unit/logic testing | Integration testing |
| Run Frequency | Every commit | On-demand or CI gates |
| Marker | `@pytest.mark.tier_a` | `@pytest.mark.tier_b` |

## Best Practices

1. **Keep Tier B tests focused** - Test specific integration points, not every code path
2. **Make tests idempotent** - Tests should be safe to run multiple times
3. **Handle API quotas** - Be mindful of rate limits and quota consumption
4. **Clean up resources** - Use fixtures to ensure test data is cleaned up
5. **Document API assumptions** - Note which API versions and behaviors are expected
6. **Skip gracefully** - Tests should skip with clear messages if credentials aren't available

## Troubleshooting

**Tests are skipped:**
- Check that `.credentials/oauth_credentials.json` exists
- Verify credentials are valid and not expired
- Ensure required Google APIs are enabled in your Cloud Project

**Authentication errors:**
- Re-run `bootstrap_oauth.py` to refresh credentials
- Check OAuth scopes match your API requirements
- Verify client ID and secret are correct

**API errors:**
- Check Google Cloud Console for API enablement
- Review quota and rate limit settings
- Ensure test service account has required permissions
