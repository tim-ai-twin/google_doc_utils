"""Tier A tests for configuration loading (credential-free)."""

import pytest

from extended_google_doc_utils.utils.config import EnvironmentType


@pytest.mark.tier_a
def test_environment_detection_default(monkeypatch):
    """Test environment detection defaults to LOCAL_DEVELOPMENT.

    This is a Tier A test - uses mocks, no credentials required.
    """
    # Clear any environment variables that might affect detection
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CLOUD_AGENT", raising=False)

    # Call the detect method
    result = EnvironmentType.detect()

    # Assert it returns LOCAL_DEVELOPMENT as the default
    assert result == EnvironmentType.LOCAL_DEVELOPMENT


@pytest.mark.tier_a
def test_environment_detection_github_actions(monkeypatch):
    """Test environment detection identifies GitHub Actions."""
    # Set GITHUB_ACTIONS environment variable
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("CLOUD_AGENT", raising=False)

    # Call the detect method
    result = EnvironmentType.detect()

    # Assert it returns GITHUB_ACTIONS
    assert result == EnvironmentType.GITHUB_ACTIONS


@pytest.mark.tier_a
def test_environment_detection_cloud_agent(monkeypatch):
    """Test environment detection identifies Cloud Agent."""
    # Set CLOUD_AGENT environment variable
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CLOUD_AGENT", "true")

    # Call the detect method
    result = EnvironmentType.detect()

    # Assert it returns CLOUD_AGENT
    assert result == EnvironmentType.CLOUD_AGENT
