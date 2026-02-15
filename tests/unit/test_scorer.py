"""Unit tests for score computation."""

import pytest

from extended_google_doc_utils.discoverability.models import (
    AttemptRecord,
    Classification,
    IntentResult,
    TestRun,
    TrialResult,
    VariantResult,
)
from extended_google_doc_utils.discoverability.scorer import compute_scores


def _make_trial(success: bool, first_classification: Classification, total_attempts: int = 1):
    """Helper to create a TrialResult."""
    attempts = [
        AttemptRecord(
            sequence_position=1,
            tool_name="tool_a",
            parameters={},
            classification=first_classification,
            matched_expected_step=0 if first_classification == Classification.CORRECT else None,
        )
    ]
    return TrialResult(
        trial_number=1,
        success=success,
        attempts=attempts,
        total_attempts=total_attempts,
    )


def _make_run(trials_per_variant: list[list[TrialResult]]) -> TestRun:
    """Helper to create a TestRun from trial lists."""
    variant_results = []
    for trials in trials_per_variant:
        variant_results.append(
            VariantResult(
                prompt_text="test prompt",
                prompt_style="natural",
                trials=trials,
            )
        )

    return TestRun(
        results=[
            IntentResult(
                intent_name="test-intent",
                variant_results=variant_results,
            )
        ],
        tool_descriptions={"tool_a": "desc", "tool_b": "desc", "tool_c": "desc"},
    )


class TestComputeScores:
    def test_perfect_scores(self):
        """All 10 trials succeed on first attempt."""
        trials = [
            _make_trial(success=True, first_classification=Classification.CORRECT)
            for _ in range(10)
        ]
        run = _make_run([[trials[i] for i in range(10)]])
        scores = compute_scores(run)

        assert scores["first_attempt_rate"] == 1.0
        assert scores["overall_success_rate"] == 1.0
        assert scores["failure_rate"] == 0.0
        assert scores["avg_attempts_to_success"] == 1.0
        assert scores["total_trials"] == 10

    def test_80_percent_first_attempt(self):
        """8 of 10 first attempts correct."""
        trials = []
        for i in range(10):
            if i < 8:
                trials.append(
                    _make_trial(success=True, first_classification=Classification.CORRECT)
                )
            else:
                trials.append(
                    _make_trial(
                        success=True,
                        first_classification=Classification.WRONG_TOOL,
                        total_attempts=3,
                    )
                )
        run = _make_run([trials])
        scores = compute_scores(run)

        assert scores["first_attempt_rate"] == 0.8
        assert scores["overall_success_rate"] == 1.0

    def test_failure_rate(self):
        """1 of 10 trials fails."""
        trials = []
        for i in range(10):
            if i < 9:
                trials.append(
                    _make_trial(success=True, first_classification=Classification.CORRECT)
                )
            else:
                trials.append(
                    _make_trial(success=False, first_classification=Classification.WRONG_TOOL)
                )
        run = _make_run([trials])
        scores = compute_scores(run)

        assert scores["failure_rate"] == pytest.approx(0.1)
        assert scores["overall_success_rate"] == pytest.approx(0.9)

    def test_avg_attempts_to_success(self):
        """Mixed attempt counts: [1, 1, 3, 1, 2, 1, 1, FAIL, 1, 1]."""
        attempt_counts = [1, 1, 3, 1, 2, 1, 1, None, 1, 1]
        trials = []
        for count in attempt_counts:
            if count is None:
                trials.append(
                    _make_trial(success=False, first_classification=Classification.WRONG_TOOL)
                )
            elif count == 1:
                trials.append(
                    _make_trial(
                        success=True,
                        first_classification=Classification.CORRECT,
                        total_attempts=1,
                    )
                )
            else:
                trials.append(
                    _make_trial(
                        success=True,
                        first_classification=Classification.WRONG_TOOL,
                        total_attempts=count,
                    )
                )
        run = _make_run([trials])
        scores = compute_scores(run)

        # Avg of [1, 1, 3, 1, 2, 1, 1, 1, 1] = 12/9 = 1.333...
        assert scores["avg_attempts_to_success"] == pytest.approx(12 / 9, abs=0.01)
        assert scores["failure_rate"] == pytest.approx(0.1)

    def test_per_intent_breakdown(self):
        """Multiple intents with different success rates."""
        trials_good = [
            _make_trial(success=True, first_classification=Classification.CORRECT)
            for _ in range(5)
        ]
        trials_bad = [
            _make_trial(success=False, first_classification=Classification.WRONG_TOOL)
            for _ in range(5)
        ]

        run = TestRun(
            results=[
                IntentResult(
                    intent_name="good-intent",
                    variant_results=[
                        VariantResult(
                            prompt_text="good",
                            prompt_style="natural",
                            trials=trials_good,
                        )
                    ],
                ),
                IntentResult(
                    intent_name="bad-intent",
                    variant_results=[
                        VariantResult(
                            prompt_text="bad",
                            prompt_style="natural",
                            trials=trials_bad,
                        )
                    ],
                ),
            ],
            tool_descriptions={"tool_a": "desc"},
        )
        scores = compute_scores(run)

        assert scores["per_intent"]["good-intent"]["success_rate"] == 1.0
        assert scores["per_intent"]["bad-intent"]["success_rate"] == 0.0
        assert scores["per_intent"]["bad-intent"]["failure_rate"] == 1.0

    def test_untested_tools(self):
        """Detect tools with no test coverage."""
        trials = [
            _make_trial(success=True, first_classification=Classification.CORRECT)
        ]
        run = _make_run([trials])
        scores = compute_scores(run, all_tool_names=["tool_a", "tool_b", "tool_c"])

        assert "tool_b" in scores["untested_tools"]
        assert "tool_c" in scores["untested_tools"]

    def test_empty_run(self):
        """Handle run with no results."""
        run = TestRun(results=[], tool_descriptions={})
        scores = compute_scores(run)

        assert scores["first_attempt_rate"] == 0.0
        assert scores["overall_success_rate"] == 0.0
        assert scores["total_trials"] == 0
