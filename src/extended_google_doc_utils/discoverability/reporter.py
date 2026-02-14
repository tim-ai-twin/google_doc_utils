"""Markdown desire-path report generation."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any

from .models import Classification, IntentResult, TestRun, VariantResult
from .scorer import compute_scores


def generate_report(
    run: TestRun,
    output_dir: str,
    scores: dict[str, Any] | None = None,
) -> str:
    """Generate a markdown desire-path report.

    Args:
        run: Completed TestRun with results.
        output_dir: Directory to write the report file.
        scores: Pre-computed scores. If None, computed from run.

    Returns:
        Path to the generated report file.
    """
    if scores is None:
        scores = compute_scores(run)

    lines: list[str] = []
    _write_header(lines, run)
    _write_summary(lines, scores)
    _write_per_intent_results(lines, run)
    _write_desire_path_analysis(lines, run)
    _write_tool_description_snapshot(lines, run)
    _write_untested_tools(lines, scores)

    # Write to file
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = run.timestamp.strftime("%Y-%m-%d-%H%M%S")
    filename = f"desire-path-{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write("\n".join(lines))

    return filepath


def _write_header(lines: list[str], run: TestRun) -> None:
    """Write report header with metadata."""
    lines.append("# MCP Discoverability Report")
    lines.append("")
    lines.append(f"**Date**: {run.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Model**: {run.model}")
    lines.append(f"**Mode**: {run.mode}")
    lines.append(f"**Commit**: {run.commit_hash}")
    lines.append(f"**Trials per prompt**: {run.trials_per_prompt}")
    lines.append("")


def _write_summary(lines: list[str], scores: dict[str, Any]) -> None:
    """Write summary table with aggregate scores."""
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(
        f"| First-attempt success rate | {scores['first_attempt_rate']:.0%} |"
    )
    lines.append(
        f"| Overall success rate | {scores['overall_success_rate']:.0%} |"
    )
    lines.append(f"| Failure rate | {scores['failure_rate']:.0%} |")
    lines.append(
        f"| Avg attempts to success | {scores['avg_attempts_to_success']:.1f} |"
    )
    lines.append(f"| Total trials | {scores['total_trials']} |")
    lines.append("")


def _write_per_intent_results(lines: list[str], run: TestRun) -> None:
    """Write per-intent results with variant breakdowns."""
    lines.append("## Per-Intent Results")
    lines.append("")

    for intent_result in run.results:
        _write_intent_section(lines, intent_result)


def _write_intent_section(lines: list[str], intent_result: IntentResult) -> None:
    """Write a single intent's results."""
    lines.append(f"### Intent: {intent_result.intent_name}")
    lines.append(
        f"**Overall first-attempt rate**: {intent_result.first_attempt_rate:.0%} | "
        f"**Success rate**: {intent_result.success_rate:.0%}"
    )
    lines.append("")

    for variant in intent_result.variant_results:
        _write_variant_section(lines, variant)


def _write_variant_section(lines: list[str], variant: VariantResult) -> None:
    """Write a single variant's results."""
    total = len(variant.trials)
    first_correct = sum(
        1 for t in variant.trials
        if t.attempts and t.attempts[0].classification == Classification.CORRECT
    )

    lines.append(
        f'#### Variant: "{variant.prompt_text}" ({variant.prompt_style})'
    )
    lines.append(
        f"- First-attempt rate: {variant.first_attempt_rate:.0%} "
        f"({first_correct}/{total} trials)"
    )
    lines.append(
        f"- Most common first tool: `{variant.most_common_first_tool}` "
        f"({_first_tool_count(variant)}/{total})"
    )

    # Desire path visualization
    if variant.desire_path:
        path_parts = []
        for entry in sorted(variant.desire_path, key=lambda e: e.avg_position):
            path_parts.append(f"{entry.tool_name} ({entry.frequency})")
        lines.append(f"- Desire path: {' -> '.join(path_parts)}")

    # Flag desire path mismatches
    if variant.desire_path and variant.most_common_first_tool:
        # Check if most common first tool is unexpected
        first_entry = next(
            (e for e in variant.desire_path if e.as_first_call > 0),
            None,
        )
        if first_entry and first_entry.as_first_call < total * 0.5:
            lines.append(f"  - **DESIRE PATH MISMATCH**: LLM frequently reaches for "
                        f"`{variant.most_common_first_tool}` first")

    lines.append("")


def _first_tool_count(variant: VariantResult) -> int:
    """Count how many trials used the most common first tool."""
    counter: Counter[str] = Counter()
    for trial in variant.trials:
        if trial.attempts and trial.attempts[0].tool_name:
            counter[trial.attempts[0].tool_name] += 1
    return counter.most_common(1)[0][1] if counter else 0


def _write_desire_path_analysis(lines: list[str], run: TestRun) -> None:
    """Write aggregate desire-path analysis across all intents."""
    lines.append("## Desire Path Analysis")
    lines.append("")
    lines.append("### Tools the LLM reaches for first (across all intents)")
    lines.append("")
    lines.append("| Tool | Times called first | Times called total | Avg position |")
    lines.append("|------|-------------------|-------------------|--------------|")

    # Aggregate first-call data across all variants
    first_call_counter: Counter[str] = Counter()
    total_call_counter: Counter[str] = Counter()
    position_sums: dict[str, list[float]] = {}

    for intent_result in run.results:
        for variant in intent_result.variant_results:
            for entry in variant.desire_path:
                first_call_counter[entry.tool_name] += entry.as_first_call
                total_call_counter[entry.tool_name] += entry.frequency
                if entry.tool_name not in position_sums:
                    position_sums[entry.tool_name] = []
                position_sums[entry.tool_name].append(entry.avg_position)

    for tool_name, first_count in first_call_counter.most_common():
        total = total_call_counter[tool_name]
        avg_pos = (
            sum(position_sums[tool_name]) / len(position_sums[tool_name])
            if position_sums.get(tool_name)
            else 0.0
        )
        lines.append(f"| `{tool_name}` | {first_count} | {total} | {avg_pos:.1f} |")

    lines.append("")


def _write_tool_description_snapshot(lines: list[str], run: TestRun) -> None:
    """Write snapshot of MCP tool descriptions at test time."""
    lines.append("## Tool Description Snapshot")
    lines.append("")
    lines.append("Tool descriptions active during this test run:")
    lines.append("")

    for tool_name, description in sorted(run.tool_descriptions.items()):
        # Truncate long descriptions for readability
        desc_preview = description[:200] + "..." if len(description) > 200 else description
        lines.append(f"- **`{tool_name}`**: {desc_preview}")

    lines.append("")


def _write_untested_tools(lines: list[str], scores: dict[str, Any]) -> None:
    """Write list of untested tools."""
    untested = scores.get("untested_tools", [])
    if untested:
        lines.append("## Untested Tools")
        lines.append("")
        for tool_name in untested:
            lines.append(f"- `{tool_name}` -- no test intent covers this tool")
        lines.append("")
