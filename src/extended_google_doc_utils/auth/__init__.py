"""Authentication and credential management for Google APIs.

This module provides OAuth 2.0 authentication utilities including:
- Credential management (loading, saving, refreshing tokens)
- OAuth authorization code flow for desktop applications
- Pre-flight credential validation

Example:
    >>> from extended_google_doc_utils.auth import CredentialManager, CredentialSource
    >>> manager = CredentialManager(CredentialSource.LOCAL_FILE)
    >>> credentials = manager.load_credentials()
"""

from .credential_manager import (
    CredentialError,
    CredentialManager,
    CredentialSource,
    CredentialSourceDetector,
    InvalidCredentialsError,
    MissingEnvironmentVariableError,
    OAuthCredentials,
    TokenExpiredError,
    TokenRevokedError,
    is_cloud_agent,
)
from .oauth_flow import OAuthFlow
from .preflight_check import PreflightCheck, PreflightCheckResult

__all__ = [
    # Credential management
    "CredentialManager",
    "CredentialSource",
    "CredentialSourceDetector",
    "OAuthCredentials",
    "is_cloud_agent",
    # Exceptions
    "CredentialError",
    "TokenExpiredError",
    "TokenRevokedError",
    "InvalidCredentialsError",
    "MissingEnvironmentVariableError",
    # OAuth flow
    "OAuthFlow",
    # Pre-flight check
    "PreflightCheck",
    "PreflightCheckResult",
]
