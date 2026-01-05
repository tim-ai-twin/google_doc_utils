"""Tier A tests for GoogleDocsClient.

These tests validate Google Docs API client methods without requiring real
credentials or API calls. All Google API services are mocked.
"""

from unittest.mock import MagicMock, Mock, patch

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
def test_get_document(mock_build, mock_oauth_credentials):
    """Test get_document retrieves document by ID using mocked API.

    This validates that:
    1. Google Docs API service is built with correct credentials
    2. documents().get() is called with the correct document ID
    3. The method returns the API response as a dictionary
    """
    # Load mock response from fixtures
    mock_response = get_mock_response("google_docs_responses", "documents.get")

    # Set up mock Google Docs API service
    mock_service = MagicMock()
    mock_documents = Mock()
    mock_get = Mock()
    mock_execute = Mock(return_value=mock_response)

    # Chain the mocks: service.documents().get().execute()
    mock_service.documents.return_value = mock_documents
    mock_documents.get.return_value = mock_get
    mock_get.execute = mock_execute
    mock_build.return_value = mock_service

    # Create client and call get_document
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.get_document("1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4")

    # Verify API was called correctly
    mock_build.assert_called_once()
    assert mock_build.call_args[0] == ("docs", "v1")
    mock_documents.get.assert_called_once_with(
        documentId="1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4"
    )
    mock_execute.assert_called_once()

    # Verify response structure
    assert result == mock_response
    assert result["documentId"] == "1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4"
    assert result["title"] == "Test Document"
    assert "body" in result


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_extract_text(mock_build, mock_oauth_credentials):
    """Test extract_text extracts text from document structure.

    This validates that:
    1. Text is correctly extracted from document body structure
    2. Multiple text runs are concatenated properly
    3. The method handles the nested document structure correctly
    """
    # Load mock response from fixtures
    mock_response = get_mock_response("google_docs_responses", "documents.get")

    # Set up mock service (minimal setup since we're testing extraction logic)
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Create client and call extract_text
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.extract_text(mock_response)

    # Verify text extraction
    assert result == "This is a test document.\n"
    assert "This is a test document" in result


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_extract_first_word(mock_build, mock_oauth_credentials):
    """Test extract_first_word extracts the first word from a document.

    This validates that:
    1. First word is correctly extracted from text content
    2. Whitespace is properly handled
    3. The method returns only the first word
    """
    # Load mock response from fixtures
    mock_response = get_mock_response("google_docs_responses", "documents.get")

    # Set up mock service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Create client and call extract_first_word
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.extract_first_word(mock_response)

    # Verify first word extraction
    assert result == "This"


@pytest.mark.tier_a
@patch("extended_google_doc_utils.google_api.docs_client.build")
def test_extract_first_word_empty_document(mock_build, mock_oauth_credentials):
    """Test extract_first_word raises ValueError for empty document.

    This validates error handling when document has no text content.
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
def test_create_document(mock_build, mock_oauth_credentials):
    """Test create_document creates a new document with title.

    This validates that:
    1. documents().create() is called with correct title
    2. The method returns the new document ID
    """
    # Mock response for document creation
    mock_create_response = {
        "documentId": "new_doc_123",
        "title": "New Test Document",
    }

    # Set up mock Google Docs API service
    mock_service = MagicMock()
    mock_documents = Mock()
    mock_create = Mock()
    mock_execute = Mock(return_value=mock_create_response)

    # Chain the mocks: service.documents().create().execute()
    mock_service.documents.return_value = mock_documents
    mock_documents.create.return_value = mock_create
    mock_create.execute = mock_execute
    mock_build.return_value = mock_service

    # Create client and call create_document
    client = GoogleDocsClient(mock_oauth_credentials)
    result = client.create_document("New Test Document")

    # Verify API was called correctly
    mock_documents.create.assert_called_once_with(body={"title": "New Test Document"})
    mock_execute.assert_called_once()

    # Verify document ID is returned
    assert result == "new_doc_123"
