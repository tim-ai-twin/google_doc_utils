"""CLI entry point for MCP discoverability testing.

Usage:
    python -m extended_google_doc_utils.discoverability run
    python -m extended_google_doc_utils.discoverability list
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv


def _get_default_suite_path() -> str:
    """Get path to the built-in default test suite."""
    return str(Path(__file__).parent / "test_suites" / "default.yaml")


def cmd_run(args: argparse.Namespace) -> None:
    """Execute the test suite and generate a report."""
    from .loader import load_test_suite
    from .models import RunConfig
    from .reporter import generate_report
    from .runner import run_test_suite
    from .scorer import compute_scores

    suite_path = args.suite or _get_default_suite_path()
    suite = load_test_suite(suite_path)

    config = RunConfig(
        model=args.model,
        mode=args.mode,
        trials=args.trials,
        max_attempts=args.max_attempts,
        max_tokens_per_trial=args.max_tokens_per_trial,
        credentials_path=args.credentials,
    )

    print(f"Running test suite: {suite.name}")
    print(f"  Model: {config.model}")
    print(f"  Mode: {config.mode}")
    print(f"  Trials per prompt: {config.trials}")
    print(f"  Max attempts per trial: {config.max_attempts}")
    if config.max_tokens_per_trial > 0:
        print(f"  Token budget per trial: {config.max_tokens_per_trial:,}")

    intents_to_run = suite.intents
    if args.intent:
        intents_to_run = [i for i in suite.intents if i.name == args.intent]
        if not intents_to_run:
            available = [i.name for i in suite.intents]
            print(f"Error: Intent '{args.intent}' not found. Available: {available}")
            sys.exit(1)

    total_calls = len(intents_to_run) * 5 * config.trials  # ~5 variants each
    print(f"  Intents: {len(intents_to_run)}")
    print(f"  Estimated LLM calls: ~{total_calls}")
    print()

    # Run the suite
    test_run = asyncio.run(
        run_test_suite(suite, config, intent_filter=args.intent)
    )

    # Compute scores
    scores = compute_scores(test_run)

    # Generate report
    output_dir = args.output_dir
    report_path = generate_report(test_run, output_dir, scores)

    # Print summary to stdout
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"  First-attempt success rate: {scores['first_attempt_rate']:.0%}")
    print(f"  Overall success rate:       {scores['overall_success_rate']:.0%}")
    print(f"  Failure rate:               {scores['failure_rate']:.0%}")
    print(f"  Avg attempts to success:    {scores['avg_attempts_to_success']:.1f}")
    print(f"  Total trials:               {scores['total_trials']}")
    print()

    # Token usage summary
    all_trials = [
        t
        for ir in test_run.results
        for vr in ir.variant_results
        for t in vr.trials
    ]
    total_input = sum(t.input_tokens for t in all_trials)
    total_output = sum(t.output_tokens for t in all_trials)
    if total_input > 0 or total_output > 0:
        budget_stops = sum(1 for t in all_trials if t.budget_exceeded)
        total = total_input + total_output
        print(f"  Total tokens:              {total:,} ({total_input:,} in / {total_output:,} out)")
        if budget_stops:
            print(f"  Trials stopped by budget:   {budget_stops}")
        print()

    if scores.get("per_intent"):
        print("Per-Intent Breakdown:")
        for intent_name, intent_scores in scores["per_intent"].items():
            print(
                f"  {intent_name}: "
                f"first={intent_scores['first_attempt_rate']:.0%} "
                f"success={intent_scores['success_rate']:.0%} "
                f"fail={intent_scores['failure_rate']:.0%}"
            )
        print()

    if scores.get("untested_tools"):
        print(f"Untested tools: {', '.join(scores['untested_tools'])}")
        print()

    print(f"Full report: {report_path}")


def cmd_list(args: argparse.Namespace) -> None:
    """List all intents and prompt variants in a test suite."""
    from .loader import load_test_suite

    suite_path = args.suite or _get_default_suite_path()
    suite = load_test_suite(suite_path)

    print(f"Test Suite: {suite.name}")
    print(f"Intents: {len(suite.intents)}")
    print()

    for intent in suite.intents:
        print(f"  {intent.name}")
        print(f"    Description: {intent.description}")
        print(f"    Expected tools: {' -> '.join(intent.expected_tools)}")
        print(f"    Order sensitive: {intent.order_sensitive}")
        print(f"    Variants ({len(intent.variants)}):")
        for variant in intent.variants:
            print(f"      [{variant.style.value}] {variant.text}")
        print()


def main() -> None:
    """Main CLI entry point."""
    # Load .env.local for API keys
    load_dotenv(dotenv_path=".env.local")
    load_dotenv()  # Also try .env

    parser = argparse.ArgumentParser(
        prog="discoverability",
        description="MCP Discoverability Testing Harness",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the test suite")
    run_parser.add_argument("--suite", type=str, help="Path to test suite YAML")
    run_parser.add_argument(
        "--model", type=str, default="claude-haiku-4-5-20251001",
        help="LLM model ID (default: claude-haiku-4-5-20251001)",
    )
    run_parser.add_argument(
        "--mode", choices=["mock", "live"], default="mock",
        help="Execution mode (default: mock)",
    )
    run_parser.add_argument(
        "--trials", type=int, default=10,
        help="Trials per prompt (default: 10)",
    )
    run_parser.add_argument(
        "--max-attempts", type=int, default=10,
        help="Max tool calls per trial (default: 10)",
    )
    run_parser.add_argument(
        "--max-tokens-per-trial", type=int, default=0,
        help="Token budget per trial; 0 = unlimited (default: 0)",
    )
    run_parser.add_argument(
        "--intent", type=str, help="Run only one intent by name",
    )
    run_parser.add_argument(
        "--output-dir", type=str, default="reports",
        help="Report output directory (default: reports/)",
    )
    run_parser.add_argument(
        "--credentials", type=str, help="OAuth credentials path (live mode)",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List intents and variants")
    list_parser.add_argument("--suite", type=str, help="Path to test suite YAML")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.command == "run":
        cmd_run(args)
    elif args.command == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
