"""Score computation from test results."""

from __future__ import annotations

from typing import Any

from .models import Classification, TestRun


def compute_scores(run: TestRun, all_tool_names: list[str] | None = None) -> dict[str, Any]:
    """Compute aggregate discoverability scores from a test run.

    Args:
        run: Completed TestRun with results.
        all_tool_names: Optional list of all MCP tool names for untested detection.
            If not provided, uses keys from run.tool_descriptions.

    Returns:
        Dict with aggregate and per-intent scores.
    """
    if all_tool_names is None:
        all_tool_names = list(run.tool_descriptions.keys())

    all_trials = []
    per_intent: dict[str, dict[str, Any]] = {}
    tested_tools: set[str] = set()

    for intent_result in run.results:
        intent_trials = []
        for variant_result in intent_result.variant_results:
            intent_trials.extend(variant_result.trials)
            # Track which tools are covered by test intents
            for trial in variant_result.trials:
                for attempt in trial.attempts:
                    if attempt.tool_name:
                        tested_tools.add(attempt.tool_name)

        all_trials.extend(intent_trials)

        total = len(intent_trials)
        if total > 0:
            successes = sum(1 for t in intent_trials if t.success)
            first_correct = sum(
                1 for t in intent_trials
                if t.attempts
                and t.attempts[0].classification == Classification.CORRECT
            )
            successful_attempt_counts = [
                t.total_attempts for t in intent_trials if t.success
            ]
            avg_attempts = (
                sum(successful_attempt_counts) / len(successful_attempt_counts)
                if successful_attempt_counts
                else 0.0
            )

            per_intent[intent_result.intent_name] = {
                "first_attempt_rate": first_correct / total,
                "success_rate": successes / total,
                "failure_rate": (total - successes) / total,
                "avg_attempts_to_success": avg_attempts,
                "total_trials": total,
            }
        else:
            per_intent[intent_result.intent_name] = {
                "first_attempt_rate": 0.0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "avg_attempts_to_success": 0.0,
                "total_trials": 0,
            }

    # Aggregate across all trials
    total = len(all_trials)
    if total > 0:
        successes = sum(1 for t in all_trials if t.success)
        first_correct = sum(
            1 for t in all_trials
            if t.attempts
            and t.attempts[0].classification == Classification.CORRECT
        )
        successful_attempt_counts = [
            t.total_attempts for t in all_trials if t.success
        ]
        avg_attempts = (
            sum(successful_attempt_counts) / len(successful_attempt_counts)
            if successful_attempt_counts
            else 0.0
        )

        first_attempt_rate = first_correct / total
        overall_success_rate = successes / total
        failure_rate = (total - successes) / total
    else:
        first_attempt_rate = 0.0
        overall_success_rate = 0.0
        failure_rate = 0.0
        avg_attempts = 0.0

    # Detect untested tools — tools in the MCP server with no test coverage
    # A tool is "tested" if it appears in any intent's expected_tools
    tested_by_intent: set[str] = set()
    for intent_result in run.results:
        # We need to check the expected tools, but they're not stored in IntentResult.
        # Instead, check which tools were actually called with CORRECT classification
        for vr in intent_result.variant_results:
            for trial in vr.trials:
                for attempt in trial.attempts:
                    if attempt.classification == Classification.CORRECT and attempt.tool_name:
                        tested_by_intent.add(attempt.tool_name)

    untested_tools = sorted(set(all_tool_names) - tested_tools)

    return {
        "first_attempt_rate": first_attempt_rate,
        "overall_success_rate": overall_success_rate,
        "failure_rate": failure_rate,
        "avg_attempts_to_success": avg_attempts,
        "per_intent": per_intent,
        "untested_tools": untested_tools,
        "total_trials": total,
    }
