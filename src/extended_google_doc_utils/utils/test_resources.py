"""Utilities for tracking test resources created during integration tests."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
