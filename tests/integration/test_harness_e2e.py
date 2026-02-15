"""Integration test: full mock-mode run with minimal test suite.

Requires ANTHROPIC_API_KEY environment variable.
"""

from __future__ import annotations

import asyncio
import os

import pytest
import yaml
from dotenv import load_dotenv

# Load .env.local for API key
load_dotenv(dotenv_path=".env.local")
load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


@pytest.fixture
def minimal_suite_path(tmp_path):
    """Create a minimal test suite YAML for integration testing."""
    suite = {
        "suite": {"name": "integration-test", "defaults": {"trials": 2}},
        "intents": [
            {
                "name": "find-document",
                "description": "Find a Google Doc by name",
                "expected_tools": ["list_documents"],
                "order_sensitive": False,
                "variants": [
                    {
                        "text": "Find my project status report",
                        "style": "natural",
                    },
                    {
                        "text": "List documents matching the query 'budget'",
                        "style": "explicit",
                    },
                ],
            },
        ],
    }

    filepath = tmp_path / "test_suite.yaml"
    with open(filepath, "w") as f:
        yaml.dump(suite, f)
    return str(filepath)


class TestHarnessE2E:
    """End-to-end integration test with mock mode."""

    def test_full_mock_run(self, minimal_suite_path, tmp_path):
        """Run a minimal test suite in mock mode and verify outputs."""
        from extended_google_doc_utils.discoverability.loader import load_test_suite
        from extended_google_doc_utils.discoverability.models import RunConfig
        from extended_google_doc_utils.discoverability.reporter import generate_report
        from extended_google_doc_utils.discoverability.runner import run_test_suite
        from extended_google_doc_utils.discoverability.scorer import compute_scores

        suite = load_test_suite(minimal_suite_path)
        assert suite.name == "integration-test"

        config = RunConfig(
            model="claude-sonnet-4-20250514",
            mode="mock",
            trials=2,
            max_attempts=5,
        )

        # Run the suite
        test_run = asyncio.run(run_test_suite(suite, config))

        # Verify TestRun is populated
        assert test_run.model == "claude-sonnet-4-20250514"
        assert test_run.mode == "mock"
        assert test_run.trials_per_prompt == 2
        assert len(test_run.results) == 1  # 1 intent

        intent_result = test_run.results[0]
        assert intent_result.intent_name == "find-document"
        assert len(intent_result.variant_results) == 2  # 2 variants

        for variant_result in intent_result.variant_results:
            assert len(variant_result.trials) == 2  # 2 trials each
            for trial in variant_result.trials:
                assert len(trial.attempts) > 0  # LLM made at least one tool call

        # Verify tool descriptions were captured
        assert len(test_run.tool_descriptions) > 0
        assert "list_documents" in test_run.tool_descriptions

        # Verify commit hash was captured
        assert test_run.commit_hash  # Non-empty

        # Compute scores
        scores = compute_scores(test_run)
        assert "first_attempt_rate" in scores
        assert "overall_success_rate" in scores
        assert 0.0 <= scores["first_attempt_rate"] <= 1.0
        assert 0.0 <= scores["overall_success_rate"] <= 1.0

        # Generate report
        report_path = generate_report(test_run, str(tmp_path), scores)
        assert os.path.exists(report_path)
        assert report_path.endswith(".md")

        with open(report_path) as f:
            content = f.read()

        assert "# MCP Discoverability Report" in content
        assert "find-document" in content
        assert "list_documents" in content
