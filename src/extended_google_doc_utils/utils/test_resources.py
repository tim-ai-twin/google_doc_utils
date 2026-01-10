"""Test resource management for Tier B integration tests.

Provides utilities for creating and tracking Google Docs/Drive resources
with automatic cleanup to prevent orphaned test data.
"""

import secrets
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


class ResourceType(Enum):
    """Type of Google resource."""

    DOCUMENT = "document"
    FOLDER = "folder"
    SPREADSHEET = "spreadsheet"


@dataclass
class TestResourceMetadata:
    """Metadata about a test resource."""

    resource_id: str
    resource_type: ResourceType
    title: str
    created_at: datetime
    test_name: str
    cleanup_attempted: bool = False
    cleanup_succeeded: bool = False

    def is_orphaned(self) -> bool:
        """Check if resource cleanup failed."""
        return self.cleanup_attempted and not self.cleanup_succeeded


@dataclass
class TestResourceManager:
    """Manages test resource lifecycle with tracking and cleanup.

    Handles:
    - Creating resources with unique identifiers
    - Tracking created resources
    - Cleanup on test completion
    - Identification of orphaned resources
    """

    credentials: "Credentials | None" = None
    _resources: list[TestResourceMetadata] = field(default_factory=list)

    def generate_unique_title(self, prefix: str) -> str:
        """Generate unique resource title with timestamp and random suffix.

        Format: {prefix}-{timestamp}-{random}
        Example: test-doc-20260102153045-a3f2

        Args:
            prefix: Title prefix (e.g., "test-doc")

        Returns:
            Unique title string
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(2)
        return f"{prefix}-{timestamp}-{random_suffix}"

    def create_document(
        self, title: str | None = None, test_name: str | None = None
    ) -> str:
        """Create a Google Doc with unique identifier and track for cleanup.

        Args:
            title: Custom title (auto-generated if None)
            test_name: Name of test creating resource (defaults to "unknown")

        Returns:
            Document ID

        Raises:
            RuntimeError: If credentials are not available
        """
        if self.credentials is None:
            raise RuntimeError(
                "Credentials required to create documents. "
                "Initialize TestResourceManager with valid OAuth credentials."
            )

        from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient

        doc_title = title or self.generate_unique_title("test-doc")
        actual_test_name = test_name or "unknown"

        client = GoogleDocsClient(self.credentials)
        doc_id = client.create_document(doc_title)

        self.track_resource(
            resource_id=doc_id,
            resource_type=ResourceType.DOCUMENT,
            title=doc_title,
            test_name=actual_test_name,
        )

        return doc_id

    def create_folder(
        self, name: str | None = None, test_name: str | None = None
    ) -> str:
        """Create a Google Drive folder with unique identifier and track for cleanup.

        Args:
            name: Custom folder name (auto-generated if None)
            test_name: Name of test creating resource (defaults to "unknown")

        Returns:
            Folder ID

        Raises:
            RuntimeError: If credentials are not available
        """
        if self.credentials is None:
            raise RuntimeError(
                "Credentials required to create folders. "
                "Initialize TestResourceManager with valid OAuth credentials."
            )

        from google.oauth2.credentials import Credentials as GoogleCredentials
        from googleapiclient.discovery import build

        folder_name = name or self.generate_unique_title("test-folder")
        actual_test_name = test_name or "unknown"

        # Convert OAuthCredentials to google.oauth2.credentials.Credentials
        google_creds = GoogleCredentials(
            token=self.credentials.access_token,
            refresh_token=self.credentials.refresh_token,
            token_uri=self.credentials.token_uri,
            client_id=self.credentials.client_id,
            client_secret=self.credentials.client_secret,
            scopes=self.credentials.scopes,
        )

        # Create folder using Drive API
        service = build("drive", "v3", credentials=google_creds)
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = folder.get("id")

        self.track_resource(
            resource_id=folder_id,
            resource_type=ResourceType.FOLDER,
            title=folder_name,
            test_name=actual_test_name,
        )

        return folder_id

    def track_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        title: str,
        test_name: str,
    ) -> None:
        """Manually track a resource for cleanup.

        Args:
            resource_id: Google resource ID
            resource_type: Type of resource
            title: Resource title
            test_name: Name of test that created it
        """
        metadata = TestResourceMetadata(
            resource_id=resource_id,
            resource_type=resource_type,
            title=title,
            created_at=datetime.now(timezone.utc),
            test_name=test_name,
        )
        self._resources.append(metadata)

    def cleanup_resource(self, resource_id: str) -> bool:
        """Delete a tracked resource (best effort).

        Args:
            resource_id: Google resource ID to delete

        Returns:
            True if deletion succeeded, False otherwise
        """
        # Find the resource metadata
        resource = None
        for r in self._resources:
            if r.resource_id == resource_id:
                resource = r
                break

        if resource is None:
            return False

        resource.cleanup_attempted = True

        if self.credentials is None:
            return False

        try:
            if resource.resource_type in (ResourceType.DOCUMENT, ResourceType.FOLDER):
                # Use Drive API to delete (works for both docs and folders)
                from google.oauth2.credentials import Credentials as GoogleCredentials
                from googleapiclient.discovery import build

                # Convert OAuthCredentials to google.oauth2.credentials.Credentials
                google_creds = GoogleCredentials(
                    token=self.credentials.access_token,
                    refresh_token=self.credentials.refresh_token,
                    token_uri=self.credentials.token_uri,
                    client_id=self.credentials.client_id,
                    client_secret=self.credentials.client_secret,
                    scopes=self.credentials.scopes,
                )

                service = build("drive", "v3", credentials=google_creds)
                service.files().delete(fileId=resource_id).execute()
                resource.cleanup_succeeded = True
                return True
            else:
                # Other resource types not yet implemented
                return False
        except Exception:
            return False

    def cleanup_all(self) -> tuple[int, int]:
        """Attempt to clean up all tracked resources.

        Returns:
            Tuple of (successful_deletions, failed_deletions)
        """
        succeeded = 0
        failed = 0

        for resource in self._resources:
            if not resource.cleanup_attempted:
                if self.cleanup_resource(resource.resource_id):
                    succeeded += 1
                else:
                    failed += 1

        return succeeded, failed

    def list_tracked_resources(self) -> list[TestResourceMetadata]:
        """Get list of all tracked resources."""
        return list(self._resources)

    def list_orphaned_resources(self) -> list[TestResourceMetadata]:
        """Get list of resources where cleanup failed."""
        return [r for r in self._resources if r.is_orphaned()]


@contextmanager
def isolated_document(
    resource_manager: TestResourceManager,
    title: str | None = None,
    test_name: str | None = None,
) -> Generator[str, None, None]:
    """Context manager for creating a document with automatic cleanup.

    Args:
        resource_manager: TestResourceManager instance
        title: Optional document title
        test_name: Optional test name for tracking

    Yields:
        Document ID

    Example:
        with isolated_document(manager, test_name="test_foo") as doc_id:
            # Use doc_id...
        # Document is automatically cleaned up
    """
    doc_id = resource_manager.create_document(title, test_name)
    try:
        yield doc_id
    finally:
        resource_manager.cleanup_resource(doc_id)


@contextmanager
def isolated_folder(
    resource_manager: TestResourceManager,
    name: str | None = None,
    test_name: str | None = None,
) -> Generator[str, None, None]:
    """Context manager for creating a folder with automatic cleanup.

    Args:
        resource_manager: TestResourceManager instance
        name: Optional folder name
        test_name: Optional test name for tracking

    Yields:
        Folder ID

    Example:
        with isolated_folder(manager, test_name="test_foo") as folder_id:
            # Use folder_id...
        # Folder is automatically cleaned up
    """
    folder_id = resource_manager.create_folder(name, test_name)
    try:
        yield folder_id
    finally:
        resource_manager.cleanup_resource(folder_id)
