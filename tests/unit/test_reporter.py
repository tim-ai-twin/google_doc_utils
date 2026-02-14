"""Unit tests for report generation."""

import os
from datetime import datetime

import pytest

from extended_google_doc_utils.discoverability.models import (
    AttemptRecord,
    Classification,
    DesirePathEntry,
    IntentResult,
    TestRun,
    TrialResult,
    VariantResult,
)
from extended_google_doc_utils.discoverability.reporter import generate_report


@pytest.fixture
def sample_test_run():
    """Create a TestRun with known data for testing report output."""
    trials = [
        TrialResult(
            trial_number=1,
            success=True,
            attempts=[
                AttemptRecord(
                    sequence_position=1,
                    tool_name="get_hierarchy",
                    parameters={"document_id": "doc123"},
                    classification=Classification.CORRECT,
                    matched_expected_step=0,
                ),
            ],
        ),
        TrialResult(
            trial_number=2,
            success=True,
            attempts=[
                AttemptRecord(
                    sequence_position=1,
                    tool_name="export_tab",
                    parameters={"document_id": "doc123"},
                    classification=Classification.WRONG_TOOL,
                ),
                AttemptRecord(
                    sequence_position=2,
                    tool_name="get_hierarchy",
                    parameters={"document_id": "doc123"},
                    classification=Classification.CORRECT,
                    matched_expected_step=0,
                ),
            ],
        ),
    ]

    return TestRun(
        timestamp=datetime(2026, 2, 13, 10, 30, 0),
        commit_hash="abc1234",
        model="claude-sonnet-4-20250514",
        mode="mock",
        trials_per_prompt=2,
        max_attempts=10,
        tool_descriptions={
            "get_hierarchy": "Get heading structure",
            "export_tab": "Export full tab content",
            "list_documents": "List accessible documents",
        },
        results=[
            IntentResult(
                intent_name="understand-structure",
                variant_results=[
                    VariantResult(
                        prompt_text="What sections does my report have?",
                        prompt_style="natural",
                        trials=trials,
                        first_attempt_rate=0.5,
                        success_rate=1.0,
                        avg_attempts=1.5,
                        most_common_first_tool="get_hierarchy",
                        desire_path=[
                            DesirePathEntry(
                                tool_name="get_hierarchy",
                                frequency=2,
                                avg_position=1.5,
                                as_first_call=1,
                            ),
                            DesirePathEntry(
                                tool_name="export_tab",
                                frequency=1,
                                avg_position=1.0,
                                as_first_call=1,
                            ),
                        ],
                    ),
                ],
                first_attempt_rate=0.5,
                success_rate=1.0,
                failure_rate=0.0,
            ),
        ],
    )


class TestGenerateReport:
    def test_report_file_created(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        assert os.path.exists(report_path)
        assert report_path.endswith(".md")

    def test_report_filename_format(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        filename = os.path.basename(report_path)
        assert filename.startswith("desire-path-")
        assert filename.endswith(".md")

    def test_report_header(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        with open(report_path) as f:
            content = f.read()

        assert "# MCP Discoverability Report" in content
        assert "**Date**: 2026-02-13 10:30:00" in content
        assert "**Model**: claude-sonnet-4-20250514" in content
        assert "**Mode**: mock" in content
        assert "**Commit**: abc1234" in content
        assert "**Trials per prompt**: 2" in content

    def test_report_summary_table(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        with open(report_path) as f:
            content = f.read()

        assert "## Summary" in content
        assert "First-attempt success rate" in content
        assert "Overall success rate" in content
        assert "Failure rate" in content
        assert "Avg attempts to success" in content

    def test_report_per_intent_section(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        with open(report_path) as f:
            content = f.read()

        assert "## Per-Intent Results" in content
        assert "### Intent: understand-structure" in content
        assert "What sections does my report have?" in content

    def test_report_desire_path_analysis(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        with open(report_path) as f:
            content = f.read()

        assert "## Desire Path Analysis" in content
        assert "Tools the LLM reaches for first" in content
        assert "`get_hierarchy`" in content

    def test_report_tool_description_snapshot(self, sample_test_run, tmp_path):
        report_path = generate_report(sample_test_run, str(tmp_path))
        with open(report_path) as f:
            content = f.read()

        assert "## Tool Description Snapshot" in content
        assert "`get_hierarchy`" in content
        assert "Get heading structure" in content

    def test_report_creates_output_dir(self, sample_test_run, tmp_path):
        nested_dir = str(tmp_path / "nested" / "reports")
        report_path = generate_report(sample_test_run, nested_dir)
        assert os.path.exists(report_path)
