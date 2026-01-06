"""Utility modules for configuration, logging, and test resources.

This module provides supporting utilities:
- config: Environment detection (local, CI/CD, cloud agent)
- logging: Package-wide logging configuration
- test_resources: Test resource lifecycle management for Tier B tests

Example:
    >>> from extended_google_doc_utils.utils import EnvironmentType
    >>> env = EnvironmentType.detect()
    >>> print(f"Running in: {env.value}")
"""

from .config import EnvironmentType
from .logging import get_logger, setup_logging, setup_logging_from_env
from .test_resources import (
    ResourceType,
    TestResourceManager,
    TestResourceMetadata,
    isolated_document,
    isolated_folder,
)

__all__ = [
    # Configuration
    "EnvironmentType",
    # Logging
    "get_logger",
    "setup_logging",
    "setup_logging_from_env",
    # Test resources
    "ResourceType",
    "TestResourceManager",
    "TestResourceMetadata",
    "isolated_document",
    "isolated_folder",
]
