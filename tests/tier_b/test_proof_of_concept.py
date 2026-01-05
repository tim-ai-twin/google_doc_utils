"""Tier B proof-of-concept test for end-to-end integration.

This test validates the entire authentication and API chain by reading
a real Google Doc and extracting its first word.
"""

import pytest
from googleapiclient.errors import HttpError

from extended_google_doc_utils.google_api.docs_client import GoogleDocsClient


@pytest.mark.tier_b
def test_read_gondwana_document(google_credentials):
    """Test reading the Gondwana test document.

    This proof-of-concept test validates the entire stack:
    1. OAuth credentials are valid and loaded
    2. GoogleDocsClient can authenticate with Google Docs API
    3. Document can be retrieved by ID
    4. Text extraction works correctly
    5. First word extraction works correctly

    Test document: "Gondwana" test document
    Document ID: 1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4
    Expected first word: "Gondwana"

    This test requires valid Google Cloud credentials and the test document
    must be accessible with those credentials.
    """
    # Skip if no credentials available
    if google_credentials is None:
        pytest.skip("No credentials available for proof-of-concept test")

    # Create GoogleDocsClient with loaded credentials
    client = GoogleDocsClient(google_credentials)

    # Retrieve the test document
    document_id = "1t8YEJ57mfNbvE85tQjFDmPmLAvRX1v307teKfXc09T4"

    try:
        document = client.get_document(document_id)
    except HttpError as e:
        # Provide clear error message for common access issues
        error_reason = "unknown error"
        if e.resp.status == 404:
            error_reason = "document not found (404)"
        elif e.resp.status == 403:
            error_reason = "permission denied (403)"

        pytest.fail(
            f"Cannot access Gondwana document. Check sharing permissions. "
            f"Error: {error_reason}"
        )

    # Verify document was retrieved
    assert document is not None, "Document should be retrieved"
    assert "documentId" in document, "Document should have documentId field"
    assert document["documentId"] == document_id, "Document ID should match"

    # Extract first word
    first_word = client.extract_first_word(document)

    # Assert first word is valid and equals "Gondwana"
    assert first_word is not None, "First word should not be None"
    assert first_word == "Gondwana", f"Expected 'Gondwana', got '{first_word}'"
