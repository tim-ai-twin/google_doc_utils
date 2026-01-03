"""
Test Resource Manager Protocol

Defines the interface for managing Google Docs/Drive resources created during tests.
Handles resource creation with unique IDs and best-effort cleanup.
"""

from contextlib import AbstractContextManager
from datetime import datetime
from enum import Enum
from typing import Protocol


class ResourceType(Enum):
    """Type of Google resource"""
    DOCUMENT = "document"
    FOLDER = "folder"
    SPREADSHEET = "spreadsheet"


class TestResourceMetadata(Protocol):
    """Metadata about a test resource"""

    resource_id: str
    """Google resource ID"""

    resource_type: ResourceType
    """Type of resource"""

    title: str
    """Resource title with unique identifier"""

    created_at: datetime
    """When resource was created (UTC)"""

    test_name: str
    """Name of test that created it"""

    cleanup_attempted: bool
    """Whether cleanup was attempted"""

    cleanup_succeeded: bool
    """Whether cleanup succeeded"""

    def is_orphaned(self) -> bool:
        """
        Check if resource cleanup failed.

        Returns:
            True if cleanup was attempted but failed
        """
        ...


class TestResourceManager(Protocol):
    """
    Protocol for managing test resource lifecycle.

    Handles:
    - Creating resources with unique identifiers
    - Tracking created resources
    - Cleanup on test completion
    - Identification of orphaned resources
    """

    def generate_unique_title(self, prefix: str) -> str:
        """
        Generate unique resource title with timestamp and random suffix.

        Format: {prefix}-{timestamp}-{random}
        Example: test-doc-20260102153045-a3f2

        Args:
            prefix: Title prefix (e.g., "test-doc")

        Returns:
            Unique title string
        """
        ...

    def create_document(
        self, title: str | None = None, test_name: str | None = None
    ) -> str:
        """
        Create a Google Doc with unique identifier and track for cleanup.

        Args:
            title: Custom title (auto-generated if None)
            test_name: Name of test creating resource (auto-detected if None)

        Returns:
            Document ID

        Raises:
            AuthError: If credentials are invalid
            QuotaExceededError: If API quota exceeded
        """
        ...

    def create_folder(
        self, name: str | None = None, test_name: str | None = None
    ) -> str:
        """
        Create a Google Drive folder with unique identifier and track for cleanup.

        Args:
            name: Custom folder name (auto-generated if None)
            test_name: Name of test creating resource (auto-detected if None)

        Returns:
            Folder ID

        Raises:
            AuthError: If credentials are invalid
            QuotaExceededError: If storage quota exceeded
        """
        ...

    def track_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        title: str,
        test_name: str
    ) -> None:
        """
        Manually track a resource for cleanup.

        Use when resource is created outside manager methods.

        Args:
            resource_id: Google resource ID
            resource_type: Type of resource
            title: Resource title
            test_name: Name of test that created it
        """
        ...

    def cleanup_resource(self, resource_id: str) -> bool:
        """
        Delete a tracked resource (best effort).

        Args:
            resource_id: Google resource ID to delete

        Returns:
            True if deletion succeeded, False otherwise

        Note:
            Does not raise exceptions. Logs failures and returns False.
        """
        ...

    def cleanup_all(self) -> tuple[int, int]:
        """
        Attempt to clean up all tracked resources.

        Best-effort cleanup. Continues even if individual deletions fail.

        Returns:
            Tuple of (successful_deletions, failed_deletions)
        """
        ...

    def list_tracked_resources(self) -> list[TestResourceMetadata]:
        """
        Get list of all tracked resources.

        Returns:
            List of resource metadata
        """
        ...

    def list_orphaned_resources(self) -> list[TestResourceMetadata]:
        """
        Get list of resources where cleanup failed.

        Returns:
            List of orphaned resource metadata
        """
        ...


class IsolatedTestResource(Protocol):
    """
    Context manager for isolated test resources with automatic cleanup.

    Usage:
        with isolated_document(client, "test-feature") as doc_id:
            # Use doc_id in test
            pass
        # Document automatically cleaned up
    """

    def __enter__(self) -> str:
        """
        Create resource and return its ID.

        Returns:
            Resource ID
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Clean up resource (best effort).

        Logs but does not raise exceptions on cleanup failure.
        """
        ...


def isolated_document(
    manager: TestResourceManager,
    title_prefix: str = "test-doc",
    test_name: str | None = None
) -> AbstractContextManager[str]:
    """
    Create an isolated test document with automatic cleanup.

    Args:
        manager: Resource manager instance
        title_prefix: Prefix for document title
        test_name: Test name (auto-detected if None)

    Returns:
        Context manager yielding document ID

    Example:
        with isolated_document(mgr, "proof-of-concept") as doc_id:
            doc = client.get_document(doc_id)
            assert extract_first_word(doc) == "Test"
    """
    ...


def isolated_folder(
    manager: TestResourceManager,
    name_prefix: str = "test-folder",
    test_name: str | None = None
) -> AbstractContextManager[str]:
    """
    Create an isolated test folder with automatic cleanup.

    Args:
        manager: Resource manager instance
        name_prefix: Prefix for folder name
        test_name: Test name (auto-detected if None)

    Returns:
        Context manager yielding folder ID

    Example:
        with isolated_folder(mgr, "test-uploads") as folder_id:
            # Upload files to folder for testing
            pass
    """
    ...
