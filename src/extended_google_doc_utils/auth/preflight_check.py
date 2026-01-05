"""Pre-flight credential validation for test execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials


logger = logging.getLogger(__name__)


@dataclass
class PreflightCheckResult:
    """Result of a credential pre-flight check.

    Attributes:
        success: Whether the pre-flight check succeeded
        error_message: Error message if check failed, None otherwise
        user_email: Email address from Drive about.get if successful, None otherwise
        elapsed_time: Time taken to perform the check in seconds
    """

    success: bool
    error_message: str | None
    user_email: str | None
    elapsed_time: float


class PreflightCheck:
    """Validates credentials before running tests.

    Performs a lightweight Drive API call to verify credentials are valid
    and provides fast failure feedback (<2s target).
    """

    def __init__(self, credentials: OAuthCredentials) -> None:
        """Initialize pre-flight check with credentials.

        Args:
            credentials: OAuth credentials to validate
        """
        self.credentials = credentials

    def run(self) -> PreflightCheckResult:
        """Execute pre-flight check with Drive API call.

        Returns:
            PreflightCheckResult with validation outcome
        """
        # Start timer
        start_time = time.perf_counter()

        try:
            # Convert OAuthCredentials to google.oauth2.credentials.Credentials
            google_creds = Credentials(
                token=self.credentials.access_token,
                refresh_token=self.credentials.refresh_token,
                token_uri=self.credentials.token_uri,
                client_id=self.credentials.client_id,
                client_secret=self.credentials.client_secret,
                scopes=self.credentials.scopes,
            )

            # Build Drive API service
            service = build("drive", "v3", credentials=google_creds)

            # Make lightweight Drive API call
            about = service.about().get(fields="user").execute()

            # Extract user email
            user_email = about.get("user", {}).get("emailAddress")

            # Calculate elapsed time
            elapsed_time = time.perf_counter() - start_time

            # Log warning if pre-flight check is slow
            if elapsed_time > 2.0:
                logger.warning(
                    "Pre-flight check took %.2fs (target: <2s). "
                    "Consider checking network connectivity.",
                    elapsed_time,
                )

            return PreflightCheckResult(
                success=True,
                error_message=None,
                user_email=user_email,
                elapsed_time=elapsed_time,
            )

        except Exception as e:
            # Calculate elapsed time even on failure
            elapsed_time = time.perf_counter() - start_time

            return PreflightCheckResult(
                success=False,
                error_message=str(e),
                user_email=None,
                elapsed_time=elapsed_time,
            )

    def validate_and_report(self) -> bool:
        """Execute pre-flight check and output results to console.

        Returns:
            True if validation succeeded, False otherwise
        """
        result = self.run()

        if result.success:
            print(f"✓ Credentials valid for {result.user_email} ({result.elapsed_time:.1f}s)")
        else:
            print(f"✗ Credential validation failed: {result.error_message}")
            print()
            print("To set up credentials, run:")
            print("    python scripts/bootstrap_oauth.py")

        return result.success
