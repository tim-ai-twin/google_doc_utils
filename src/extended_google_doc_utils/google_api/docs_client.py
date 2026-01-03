"""Google Docs API client for document operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials


class GoogleDocsClient:
    """High-level API for Google Docs operations.

    Abstracts google-api-python-client complexity and provides
    convenient methods for document management.
    """

    def __init__(self, credentials: OAuthCredentials) -> None:
        """Initialize Google Docs client with OAuth credentials.

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

        # Build Google Docs API service
        self.service = build("docs", "v1", credentials=google_creds)

    def get_document(self, document_id: str) -> dict:
        """Retrieve a Google Doc by ID.

        Args:
            document_id: The ID of the document to retrieve

        Returns:
            Document resource as a dictionary

        Raises:
            googleapiclient.errors.HttpError: If document not found or access denied
        """
        return self.service.documents().get(documentId=document_id).execute()

    def extract_text(self, document: dict) -> str:
        """Extract all text content from a document.

        Args:
            document: Document resource from get_document()

        Returns:
            Concatenated text content from the document
        """
        text_parts = []

        # Navigate the document structure to extract text
        body = document.get("body", {})
        content = body.get("content", [])

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for elem in paragraph.get("elements", []):
                    text_run = elem.get("textRun", {})
                    content_text = text_run.get("content", "")
                    text_parts.append(content_text)

        return "".join(text_parts)

    def extract_first_word(self, document: dict) -> str:
        """Extract the first word from a document.

        Args:
            document: Document resource from get_document()

        Returns:
            First word in the document, stripped of whitespace

        Raises:
            ValueError: If document is empty or has no text
        """
        text = self.extract_text(document)

        # Split on whitespace and get first non-empty word
        words = text.split()
        if not words:
            raise ValueError("Document contains no text")

        return words[0]

    def create_document(self, title: str) -> str:
        """Create a new Google Doc with the given title.

        Args:
            title: Title for the new document

        Returns:
            Document ID of the created document

        Raises:
            googleapiclient.errors.HttpError: If creation fails
        """
        document = self.service.documents().create(body={"title": title}).execute()
        return document.get("documentId")
