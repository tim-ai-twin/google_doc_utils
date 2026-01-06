"""Google API client wrappers for Docs and Drive operations.

This module provides high-level clients that abstract the complexity
of the google-api-python-client library:
- GoogleDocsClient: Document creation, retrieval, and text extraction
- GoogleDriveClient: File management and user info retrieval

Example:
    >>> from extended_google_doc_utils.google_api import GoogleDocsClient
    >>> client = GoogleDocsClient(credentials)
    >>> doc = client.get_document("document-id")
    >>> text = client.extract_text(doc)
"""

from .docs_client import GoogleDocsClient
from .drive_client import GoogleDriveClient

__all__ = [
    "GoogleDocsClient",
    "GoogleDriveClient",
]
