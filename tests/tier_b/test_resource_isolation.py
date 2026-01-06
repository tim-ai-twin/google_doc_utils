"""Tier B tests for resource isolation.

These tests validate the TestResourceManager pattern works end-to-end
with real Google Drive, ensuring resources are properly created with
unique identifiers and cleaned up after tests.
"""

from __future__ import annotations

import secrets
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

import pytest
from googleapiclient.errors import HttpError

from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient
from extended_google_doc_utils.google_api.drive_client import GoogleDriveClient

if TYPE_CHECKING:
    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials


class ResourceType(Enum):
    """Type of Google resource."""

    DOCUMENT = "document"
    FOLDER = "folder"
    SPREADSHEET = "spreadsheet"


@dataclass
class TrackedResource:
    """Metadata about a tracked test resource."""

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


class TestResourceManager:
    """Manages test resource lifecycle with unique identifiers and cleanup.

    This implementation provides:
    - Unique title generation with timestamp + random suffix
    - Resource creation and tracking
    - Best-effort cleanup on test completion
    - Identification of orphaned resources
    """

    def __init__(
        self,
        docs_client: GoogleDocsClient,
        drive_client: GoogleDriveClient,
    ) -> None:
        """Initialize resource manager with API clients.

        Args:
            docs_client: Client for Google Docs operations
            drive_client: Client for Google Drive operations
        """
        self.docs_client = docs_client
        self.drive_client = drive_client
        self._tracked_resources: dict[str, TrackedResource] = {}

    def generate_unique_title(self, prefix: str) -> str:
        """Generate unique resource title with timestamp and random suffix.

        Format: {prefix}-{timestamp}-{random}
        Example: test-doc-20260102153045-a3f2

        Args:
            prefix: Title prefix (e.g., "test-doc")

        Returns:
            Unique title string
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(2)  # 4 hex chars
        return f"{prefix}-{timestamp}-{random_suffix}"

    def create_document(
        self,
        title: str | None = None,
        test_name: str | None = None,
    ) -> str:
        """Create a Google Doc with unique identifier and track for cleanup.

        Args:
            title: Custom title (auto-generated if None)
            test_name: Name of test creating resource (defaults to "unknown")

        Returns:
            Document ID
        """
        if title is None:
            title = self.generate_unique_title("test-doc")

        if test_name is None:
            test_name = "unknown"

        # Create the document
        document_id = self.docs_client.create_document(title)

        # Track for cleanup
        self._tracked_resources[document_id] = TrackedResource(
            resource_id=document_id,
            resource_type=ResourceType.DOCUMENT,
            title=title,
            created_at=datetime.now(UTC),
            test_name=test_name,
        )

        return document_id

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
        self._tracked_resources[resource_id] = TrackedResource(
            resource_id=resource_id,
            resource_type=resource_type,
            title=title,
            created_at=datetime.now(UTC),
            test_name=test_name,
        )

    def cleanup_resource(self, resource_id: str) -> bool:
        """Delete a tracked resource (best effort).

        Args:
            resource_id: Google resource ID to delete

        Returns:
            True if deletion succeeded, False otherwise
        """
        if resource_id not in self._tracked_resources:
            return False

        resource = self._tracked_resources[resource_id]
        resource.cleanup_attempted = True

        try:
            self.drive_client.delete_file(resource_id)
            resource.cleanup_succeeded = True
            return True
        except HttpError:
            # Best effort - don't raise, just return False
            resource.cleanup_succeeded = False
            return False

    def cleanup_all(self) -> tuple[int, int]:
        """Attempt to clean up all tracked resources.

        Returns:
            Tuple of (successful_deletions, failed_deletions)
        """
        successful = 0
        failed = 0

        for resource_id in list(self._tracked_resources.keys()):
            if self.cleanup_resource(resource_id):
                successful += 1
            else:
                failed += 1

        return successful, failed

    def list_tracked_resources(self) -> list[TrackedResource]:
        """Get list of all tracked resources.

        Returns:
            List of tracked resource metadata
        """
        return list(self._tracked_resources.values())

    def list_orphaned_resources(self) -> list[TrackedResource]:
        """Get list of resources where cleanup failed.

        Returns:
            List of orphaned resource metadata
        """
        return [r for r in self._tracked_resources.values() if r.is_orphaned()]


@contextmanager
def isolated_document(
    manager: TestResourceManager,
    title_prefix: str = "test-doc",
    test_name: str | None = None,
):
    """Create an isolated test document with automatic cleanup.

    Args:
        manager: Resource manager instance
        title_prefix: Prefix for document title
        test_name: Test name (defaults to "unknown")

    Yields:
        Document ID
    """
    title = manager.generate_unique_title(title_prefix)
    doc_id = manager.create_document(title=title, test_name=test_name)
    try:
        yield doc_id
    finally:
        manager.cleanup_resource(doc_id)


@pytest.fixture
def resource_manager(google_credentials):
    """Create a TestResourceManager for Tier B tests.

    Provides automatic cleanup after test completion.

    Args:
        google_credentials: OAuth credentials fixture

    Yields:
        TestResourceManager instance
    """
    if google_credentials is None:
        pytest.skip("No credentials available for resource isolation test")

    docs_client = GoogleDocsClient(google_credentials)
    drive_client = GoogleDriveClient(google_credentials)

    manager = TestResourceManager(docs_client, drive_client)
    yield manager

    # Cleanup all resources after test (best effort)
    manager.cleanup_all()


@pytest.mark.tier_b
def test_isolated_document_creation_and_cleanup(resource_manager):
    """Test that documents are created with unique titles and cleaned up.

    This test validates:
    1. Documents can be created with unique identifiers
    2. Created documents are accessible via API
    3. Documents are properly tracked for cleanup
    4. Cleanup successfully deletes the document
    """
    # Create a document with unique title
    test_name = "test_isolated_document_creation_and_cleanup"
    title = resource_manager.generate_unique_title("isolation-test")
    doc_id = resource_manager.create_document(title=title, test_name=test_name)

    # Verify document was created
    assert doc_id is not None, "Document ID should be returned"
    assert len(doc_id) > 0, "Document ID should not be empty"

    # Verify document is accessible
    document = resource_manager.docs_client.get_document(doc_id)
    assert document is not None, "Document should be retrievable"
    assert document.get("title") == title, f"Title should be '{title}'"

    # Verify document is tracked
    tracked = resource_manager.list_tracked_resources()
    assert len(tracked) >= 1, "At least one resource should be tracked"

    tracked_doc = next((r for r in tracked if r.resource_id == doc_id), None)
    assert tracked_doc is not None, "Created document should be tracked"
    assert tracked_doc.title == title, "Tracked title should match"
    assert tracked_doc.test_name == test_name, "Tracked test name should match"
    assert tracked_doc.resource_type == ResourceType.DOCUMENT

    # Cleanup the document
    cleanup_success = resource_manager.cleanup_resource(doc_id)
    assert cleanup_success is True, "Cleanup should succeed"

    # Verify document is no longer accessible
    with pytest.raises(HttpError) as exc_info:
        resource_manager.docs_client.get_document(doc_id)
    assert exc_info.value.resp.status == 404, "Deleted document should return 404"


@pytest.mark.tier_b
def test_unique_title_generation(resource_manager):
    """Test that generated titles are unique.

    This test validates:
    1. Multiple titles with same prefix are unique
    2. Title format follows expected pattern
    3. No collisions occur when generating many titles
    """
    prefix = "unique-test"
    generated_titles = set()
    num_titles = 50

    # Generate many titles and verify uniqueness
    for _ in range(num_titles):
        title = resource_manager.generate_unique_title(prefix)

        # Verify format: prefix-timestamp-random
        assert title.startswith(f"{prefix}-"), f"Title should start with '{prefix}-'"
        parts = title.split("-")
        assert len(parts) >= 3, "Title should have at least 3 parts (prefix-timestamp-random)"

        # Verify uniqueness
        assert title not in generated_titles, f"Title '{title}' was generated twice"
        generated_titles.add(title)

    # Verify we generated the expected number of unique titles
    assert len(generated_titles) == num_titles, "All titles should be unique"


@pytest.mark.tier_b
def test_resource_tracking(resource_manager):
    """Test that resources are properly tracked and can be listed.

    This test validates:
    1. Created resources are automatically tracked
    2. Manually tracked resources are recorded
    3. list_tracked_resources returns all tracked resources
    4. cleanup_all cleans up all resources
    5. Orphaned resources are identified correctly
    """
    # Initially no resources tracked
    initial_tracked = resource_manager.list_tracked_resources()
    initial_count = len(initial_tracked)

    # Create multiple documents
    test_name = "test_resource_tracking"
    doc_ids = []
    for i in range(3):
        title = resource_manager.generate_unique_title(f"tracking-test-{i}")
        doc_id = resource_manager.create_document(title=title, test_name=test_name)
        doc_ids.append(doc_id)

    # Verify all documents are tracked
    tracked = resource_manager.list_tracked_resources()
    assert len(tracked) == initial_count + 3, "Should have 3 more tracked resources"

    # Verify each document is in the tracked list
    for doc_id in doc_ids:
        tracked_doc = next((r for r in tracked if r.resource_id == doc_id), None)
        assert tracked_doc is not None, f"Document {doc_id} should be tracked"
        assert tracked_doc.test_name == test_name
        assert tracked_doc.cleanup_attempted is False
        assert tracked_doc.cleanup_succeeded is False

    # Initially no orphaned resources
    orphaned = resource_manager.list_orphaned_resources()
    assert len(orphaned) == 0, "No orphaned resources initially"

    # Cleanup all
    successful, failed = resource_manager.cleanup_all()
    assert successful == initial_count + 3, "All 3 resources should be cleaned up"
    assert failed == 0, "No cleanup failures expected"

    # After successful cleanup, still no orphans (cleanup succeeded)
    orphaned = resource_manager.list_orphaned_resources()
    assert len(orphaned) == 0, "No orphans after successful cleanup"

    # Verify cleanup status is tracked
    for doc_id in doc_ids:
        tracked_doc = next(
            (r for r in resource_manager.list_tracked_resources() if r.resource_id == doc_id),
            None,
        )
        assert tracked_doc is not None
        assert tracked_doc.cleanup_attempted is True
        assert tracked_doc.cleanup_succeeded is True
