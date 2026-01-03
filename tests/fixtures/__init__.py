"""Fixture loading utilities for test data."""

import json
from pathlib import Path


def load_fixture(filename: str) -> dict:
    """Load JSON fixture file.

    Args:
        filename: Name of the fixture file (e.g., 'google_docs_responses.json')

    Returns:
        dict: Parsed JSON content

    Raises:
        FileNotFoundError: If fixture file doesn't exist
        json.JSONDecodeError: If fixture file is not valid JSON
    """
    fixture_path = Path(__file__).parent / filename
    with open(fixture_path) as f:
        return json.load(f)


def get_mock_response(fixture_name: str, response_key: str) -> dict:
    """Get specific mock response from a fixture file.

    Args:
        fixture_name: Name of the fixture file without extension
                     (e.g., 'google_docs_responses')
        response_key: Key of the specific response to retrieve
                     (e.g., 'documents.get')

    Returns:
        dict: The requested mock response

    Raises:
        FileNotFoundError: If fixture file doesn't exist
        KeyError: If response_key is not found in the fixture
    """
    fixture_data = load_fixture(f"{fixture_name}.json")
    return fixture_data[response_key]
