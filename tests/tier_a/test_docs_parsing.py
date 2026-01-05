"""Tier A tests for document parsing logic.

These tests validate document text extraction methods using mock fixtures,
without requiring real credentials or API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from extended_google_doc_utils.auth.credential_manager import OAuthCredentials
from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient
from tests.fixtures import get_mock_response


@pytest.fixture
def mock_oauth_credentials():
    """Create mock OAuth credentials for testing."""
    return OAuthCredentials(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expiry=None,
        client_id="test_client_id",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/documents"],
        token_uri="https://oauth2.googleapis.com/token",
    )


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_extract_text_from_mock(mock_build, mock_oauth_credentials):
    """Test extract_text extracts text from Gondwana mock document.

    This validates that:
    1. Text is correctly extracted from the Gondwana document structure
    2. The extracted text matches the expected content
    3. The method handles the nested document structure correctly
    """
    # Load Gondwana mock response from fixtures
    mock_response = get_mock_response("google_docs_responses", "gondwana_document")

    # Set up mock service (minimal setup since we're testing extraction logic)
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Create client and call extract_text
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.extract_text(mock_response)

    # Verify text extraction
    expected_text = "Gondwana was a large landmass that formed part of the supercontinent Pangaea.\n"
    assert result == expected_text, f"Expected '{expected_text}', got '{result}'"
    assert "Gondwana" in result, "Extracted text should contain 'Gondwana'"


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_extract_first_word_from_mock(mock_build, mock_oauth_credentials):
    """Test extract_first_word extracts 'Gondwana' from mock document.

    This validates that:
    1. First word is correctly extracted from the Gondwana document
    2. The extracted word matches the expected value 'Gondwana'
    3. Whitespace is properly handled
    """
    # Load Gondwana mock response from fixtures
    mock_response = get_mock_response("google_docs_responses", "gondwana_document")

    # Set up mock service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Create client and call extract_first_word
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.extract_first_word(mock_response)

    # Verify first word extraction
    assert result == "Gondwana", f"Expected 'Gondwana', got '{result}'"


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_empty_document_handling(mock_build, mock_oauth_credentials):
    """Test extract_first_word raises ValueError for empty document.

    This validates edge case handling when document has no text content.
    """
    # Create empty document structure
    empty_doc = {
        "documentId": "empty_doc_id",
        "title": "Empty Document",
        "body": {"content": []},
    }

    # Set up mock service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Create client and verify ValueError is raised
    client = GoogleDocsClient(mock_oauth_credentials)
    with pytest.raises(ValueError, match="Document contains no text"):
        client.extract_first_word(empty_doc)


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_extract_text_empty_document(mock_build, mock_oauth_credentials):
    """Test extract_text returns empty string for empty document.

    This validates that extract_text handles empty documents gracefully.
    """
    # Create empty document structure
    empty_doc = {
        "documentId": "empty_doc_id",
        "title": "Empty Document",
        "body": {"content": []},
    }

    # Set up mock service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Create client and call extract_text
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.extract_text(empty_doc)

    # Verify empty string is returned
    assert result == "", f"Expected empty string, got '{result}'"
