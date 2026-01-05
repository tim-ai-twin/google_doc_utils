"""Google Drive API client for file operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials


class GoogleDriveClient:
    """High-level API for Google Drive operations.

    Abstracts google-api-python-client complexity and provides
    convenient methods for file management and user info retrieval.
    """

    def __init__(self, credentials: OAuthCredentials) -> None:
        """Initialize Google Drive client with OAuth credentials.

        Args:
            credentials: OAuth credentials for API authentication
        """
        self.credentials = credentials

        # Convert OAuthCredentials to google.oauth2.credentials.Credentials
        google_creds = Credentials(
            token=credentials.access_token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes,
        )

        # Build Google Drive API service
        self.service = build("drive", "v3", credentials=google_creds)

    def get_user_info(self) -> dict:
        """Get information about the authenticated user.

        Used for pre-flight checks to validate credentials quickly.

        Returns:
            User information as a dictionary containing displayName,
            emailAddress, and other user metadata

        Raises:
            googleapiclient.errors.HttpError: If request fails
        """
        return self.service.about().get(fields="user").execute()

    def delete_file(self, file_id: str) -> None:
        """Delete a file from Google Drive.

        Args:
            file_id: The ID of the file to delete

        Raises:
            googleapiclient.errors.HttpError: If deletion fails
        """
        self.service.files().delete(fileId=file_id).execute()

    def list_files(self, query: str) -> list[dict]:
        """List files matching a query.

        Args:
            query: Google Drive API query string (e.g., "name='test.txt'")

        Returns:
            List of file resources matching the query

        Raises:
            googleapiclient.errors.HttpError: If request fails
        """
        results = (
            self.service.files()
            .list(q=query, fields="files(id, name, mimeType, createdTime)")
            .execute()
        )
        return results.get("files", [])
