"""
Google API Client Protocol

Defines interfaces for Google Docs and Drive API client wrappers.
"""

from typing import Protocol, Any
from credential_manager_protocol import OAuthCredentials


class GoogleDocsClient(Protocol):
    """
    Protocol for Google Docs API client wrapper.

    Provides high-level interface for common document operations.
    """

    def __init__(self, credentials: OAuthCredentials) -> None:
        """
        Initialize client with OAuth credentials.

        Args:
            credentials: Valid OAuth credentials
        """
        ...

    def get_document(self, document_id: str) -> dict[str, Any]:
        """
        Retrieve a Google Doc by ID.

        Args:
            document_id: Google Docs document ID

        Returns:
            Document resource as dict

        Raises:
            NotFoundError: If document doesn't exist or user lacks access
            AuthError: If credentials are invalid
        """
        ...

    def create_document(self, title: str) -> dict[str, Any]:
        """
        Create a new Google Doc.

        Args:
            title: Document title

        Returns:
            Created document resource with documentId

        Raises:
            AuthError: If credentials are invalid
            QuotaExceededError: If API quota exceeded
        """
        ...

    def update_document(
        self, document_id: str, requests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Update a document using batchUpdate requests.

        Args:
            document_id: Google Docs document ID
            requests: List of update requests

        Returns:
            BatchUpdate response

        Raises:
            NotFoundError: If document doesn't exist
            AuthError: If credentials are invalid
            ValueError: If requests are malformed
        """
        ...

    def extract_text(self, document: dict[str, Any]) -> str:
        """
        Extract plain text from document resource.

        Args:
            document: Document resource from get_document()

        Returns:
            Plain text content

        Raises:
            ValueError: If document structure is unexpected
        """
        ...

    def extract_first_word(self, document: dict[str, Any]) -> str:
        """
        Extract first word from document content.

        Used by proof-of-concept test to validate "Gondwana" document.

        Args:
            document: Document resource from get_document()

        Returns:
            First word in document

        Raises:
            ValueError: If document is empty or has no text
        """
        ...


class GoogleDriveClient(Protocol):
    """
    Protocol for Google Drive API client wrapper.

    Provides high-level interface for file management operations.
    """

    def __init__(self, credentials: OAuthCredentials) -> None:
        """
        Initialize client with OAuth credentials.

        Args:
            credentials: Valid OAuth credentials
        """
        ...

    def get_file(self, file_id: str, fields: str = "*") -> dict[str, Any]:
        """
        Retrieve file metadata from Google Drive.

        Args:
            file_id: Google Drive file ID
            fields: Fields to include in response (default: all)

        Returns:
            File resource as dict

        Raises:
            NotFoundError: If file doesn't exist or user lacks access
            AuthError: If credentials are invalid
        """
        ...

    def create_folder(self, name: str, parent_id: str | None = None) -> dict[str, Any]:
        """
        Create a new folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None = root)

        Returns:
            Created folder resource with id

        Raises:
            AuthError: If credentials are invalid
            QuotaExceededError: If storage quota exceeded
        """
        ...

    def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Google Drive.

        Args:
            file_id: Google Drive file ID to delete

        Raises:
            NotFoundError: If file doesn't exist
            AuthError: If credentials are invalid
        """
        ...

    def list_files(
        self,
        query: str | None = None,
        page_size: int = 100,
        order_by: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List files in Google Drive matching query.

        Args:
            query: Search query (e.g., "name contains 'test-doc'")
            page_size: Max files per page
            order_by: Sort order (e.g., "createdTime desc")

        Returns:
            List of file resources

        Raises:
            AuthError: If credentials are invalid
            ValueError: If query is malformed
        """
        ...

    def get_user_info(self) -> dict[str, Any]:
        """
        Get information about the authenticated user.

        Used for pre-flight credential validation.

        Returns:
            User resource with email, displayName, etc.

        Raises:
            AuthError: If credentials are invalid
        """
        ...


class GoogleAPIClientFactory(Protocol):
    """
    Factory for creating Google API client instances.
    """

    @staticmethod
    def create_docs_client(credentials: OAuthCredentials) -> GoogleDocsClient:
        """
        Create Google Docs API client.

        Args:
            credentials: Valid OAuth credentials

        Returns:
            Initialized Docs client

        Raises:
            AuthError: If credentials are invalid
        """
        ...

    @staticmethod
    def create_drive_client(credentials: OAuthCredentials) -> GoogleDriveClient:
        """
        Create Google Drive API client.

        Args:
            credentials: Valid OAuth credentials

        Returns:
            Initialized Drive client

        Raises:
            AuthError: If credentials are invalid
        """
        ...
