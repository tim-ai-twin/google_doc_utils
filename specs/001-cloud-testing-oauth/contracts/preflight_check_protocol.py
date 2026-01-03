"""
Pre-flight Check Protocol

Defines the interface for validating OAuth credentials before test execution.
"""

from typing import Protocol
from datetime import datetime
from credential_manager_protocol import OAuthCredentials


class PreflightCheckResult(Protocol):
    """Result of pre-flight credential validation"""

    success: bool
    """Whether the pre-flight check passed"""

    check_duration_ms: int
    """Duration of check in milliseconds"""

    timestamp: datetime
    """When the check was performed (UTC)"""

    error_message: str | None
    """Error message if check failed, None otherwise"""

    def is_within_target(self) -> bool:
        """
        Check if duration meets <2 second performance target.

        Returns:
            True if check completed in under 2 seconds
        """
        ...


class PreflightCheck(Protocol):
    """
    Protocol for validating credentials before Tier B test execution.

    The pre-flight check makes a lightweight API call to validate that:
    1. Credentials are not expired
    2. Credentials have not been revoked
    3. Credentials have sufficient permissions
    4. Google APIs are accessible

    This provides fast-fail behavior (< 2s) instead of waiting for
    individual tests to fail.
    """

    def run(self, credentials: OAuthCredentials) -> PreflightCheckResult:
        """
        Execute pre-flight credential validation.

        Makes a lightweight API call (e.g., drive.about().get()) to validate
        credentials without modifying any resources.

        Args:
            credentials: OAuth credentials to validate

        Returns:
            Result object with success status and timing

        Note:
            This method does NOT raise exceptions. All errors are captured
            in the PreflightCheckResult.error_message field.
        """
        ...

    def validate_and_report(self, credentials: OAuthCredentials) -> bool:
        """
        Run pre-flight check and print results to console.

        Convenience method for interactive use. Prints:
        - ✓ Success message if check passes
        - ✗ Error message with details if check fails
        - ⚠ Warning if check is slow (> 2 seconds)

        Args:
            credentials: OAuth credentials to validate

        Returns:
            True if check passed, False otherwise
        """
        ...


class PreflightCheckFactory(Protocol):
    """
    Factory for creating pre-flight check instances.
    """

    @staticmethod
    def create_google_drive_check() -> PreflightCheck:
        """
        Create a pre-flight check using Google Drive API.

        Uses drive.about().get(fields='user') as lightweight validation.

        Returns:
            PreflightCheck implementation for Google Drive
        """
        ...

    @staticmethod
    def create_google_docs_check() -> PreflightCheck:
        """
        Create a pre-flight check using Google Docs API.

        Uses a test document read as validation (if available).

        Returns:
            PreflightCheck implementation for Google Docs
        """
        ...

    @staticmethod
    def create_composite_check() -> PreflightCheck:
        """
        Create a pre-flight check that validates against multiple APIs.

        Runs multiple checks in parallel and succeeds if all pass.

        Returns:
            PreflightCheck that validates Drive + Docs access
        """
        ...
