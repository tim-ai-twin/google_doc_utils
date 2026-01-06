"""Utilities for tracking test resources created during integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient
    from extended_google_doc_utils.google_api.drive_client import GoogleDriveClient


class ResourceType(Enum):
    """Type of Google resource created during testing."""

    DOCUMENT = "document"
    FOLDER = "folder"
    SPREADSHEET = "spreadsheet"


@dataclass
class TestResourceMetadata:
    """Metadata for a test resource that needs cleanup.

    Attributes:
        resource_id: The Google API resource ID (e.g., document ID, folder ID)
        resource_type: Type of the resource (document, folder, etc.)
        title: Human-readable name of the resource
        created_at: Timestamp when the resource was created
    """

    resource_id: str
    resource_type: ResourceType
    title: str
    created_at: datetime


class TestResourceManager:
    """Manages test resources for integration tests.

    Tracks created documents and folders for automatic cleanup,
    preventing orphaned resources in Google Drive.
    """

    def __init__(
        self,
        docs_client: GoogleDocsClient,
        drive_client: GoogleDriveClient,
    ) -> None:
        """Initialize TestResourceManager with API clients.

        Args:
            docs_client: Google Docs API client for document operations
            drive_client: Google Drive API client for file operations
        """
        self.docs_client = docs_client
        self.drive_client = drive_client
        self._tracked_resources: list[str] = []

    def generate_unique_title(self, prefix: str = "test") -> str:
        """Generate a unique title for test resources.

        Args:
            prefix: Prefix for the generated title

        Returns:
            Unique title string
        """
        raise NotImplementedError

    def create_document(self, title: str | None = None) -> str:
        """Create a test document and track it for cleanup.

        Args:
            title: Optional title for the document. If not provided,
                   a unique title will be generated.

        Returns:
            Document ID of the created document
        """
        raise NotImplementedError

    def create_folder(self, name: str | None = None) -> str:
        """Create a test folder and track it for cleanup.

        Args:
            name: Optional name for the folder. If not provided,
                  a unique name will be generated.

        Returns:
            Folder ID of the created folder
        """
        raise NotImplementedError

    def cleanup_resource(self, resource_id: str) -> bool:
        """Delete a single resource with best-effort cleanup.

        Args:
            resource_id: ID of the resource to delete

        Returns:
            True if deletion succeeded, False otherwise
        """
        raise NotImplementedError

    def cleanup_all(self) -> dict[str, bool]:
        """Clean up all tracked resources.

        Returns:
            Dictionary mapping resource IDs to deletion success status
        """
        raise NotImplementedError

    def list_orphaned_resources(self, prefix: str = "test") -> list[dict]:
        """List resources that appear to be orphaned test resources.

        Args:
            prefix: Prefix used to identify test resources

        Returns:
            List of resource metadata dictionaries
        """
        raise NotImplementedError
