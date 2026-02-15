"""Test execution engine — MCP client + Anthropic SDK agentic loop."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from collections import Counter
from typing import Any

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .mock import get_mock_response
from .models import (
    AttemptRecord,
    Classification,
    DesirePathEntry,
    IntentResult,
    RunConfig,
    TestRun,
    TestSuite,
    TrialResult,
    UserIntent,
    VariantResult,
)

logger = logging.getLogger(__name__)

# System prompt for the LLM during testing
SYSTEM_PROMPT = (
    "You are an assistant with access to Google Docs tools via MCP. "
    "Use the available tools to accomplish the user's request. "
    "Call tools as needed — do not ask for confirmation."
)


def _mcp_tools_to_anthropic(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to Anthropic tool format.

    Args:
        mcp_tools: List of MCP Tool objects from session.list_tools().

    Returns:
        List of tool dicts in Anthropic format.
    """
    anthropic_tools = []
    for tool in mcp_tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        })
    return anthropic_tools


async def _get_mcp_tools_mock() -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Get tool definitions directly from FastMCP (no subprocess needed).

    This imports the MCP server module and registers tools in-process,
    avoiding the need for Google credentials in mock mode.

    Returns:
        Tuple of (anthropic_tools, tool_descriptions_snapshot).
    """
    from extended_google_doc_utils.mcp.server import mcp as fastmcp_server
    from extended_google_doc_utils.mcp.server import register_tools

    register_tools()
    mcp_tools = await fastmcp_server.list_tools()

    anthropic_tools = []
    tool_descriptions = {}
    for tool in mcp_tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        })
        tool_descriptions[tool.name] = tool.description or ""

    return anthropic_tools, tool_descriptions


async def _get_mcp_tools_live(
    config: RunConfig,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Connect to MCP server subprocess and retrieve tool definitions.

    Used for live mode where the server needs credentials to execute tools.

    Returns:
        Tuple of (anthropic_tools, tool_descriptions_snapshot).
    """
    server_params = StdioServerParameters(
        command=config.mcp_server_command[0],
        args=config.mcp_server_command[1:],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools

            anthropic_tools = _mcp_tools_to_anthropic(mcp_tools)
            tool_descriptions = {t.name: (t.description or "") for t in mcp_tools}

            return anthropic_tools, tool_descriptions


async def _get_mcp_tools(config: RunConfig) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Get MCP tool definitions.

    In mock mode: imports tools directly from FastMCP (no subprocess).
    In live mode: starts MCP server subprocess and connects via stdio.

    Returns:
        Tuple of (anthropic_tools, tool_descriptions_snapshot).
    """
    if config.mode == "mock":
        return await _get_mcp_tools_mock()
    else:
        return await _get_mcp_tools_live(config)


def _classify_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    expected_tools: list[str],
    next_expected_idx: int,
    order_sensitive: bool,
) -> tuple[Classification, int | None]:
    """Classify a tool call against expected tools.

    Args:
        tool_name: Name of the tool called.
        parameters: Parameters provided by the LLM.
        expected_tools: Ordered list of expected tool names.
        next_expected_idx: Index of the next expected tool to satisfy.
        order_sensitive: Whether order matters.

    Returns:
        Tuple of (classification, matched_step_index_or_none).
    """
    if order_sensitive:
        if next_expected_idx < len(expected_tools):
            if tool_name == expected_tools[next_expected_idx]:
                return Classification.CORRECT, next_expected_idx
        # Check if it matches any remaining expected tool (not yet satisfied)
        for i in range(next_expected_idx, len(expected_tools)):
            if tool_name == expected_tools[i]:
                # Right tool but out of order — classified as wrong_tool
                # since order matters
                return Classification.WRONG_TOOL, None
    else:
        # Order insensitive: match any unsatisfied expected tool
        for i in range(len(expected_tools)):
            if tool_name == expected_tools[i] and i >= next_expected_idx:
                return Classification.CORRECT, i

    # Tool not in expected sequence at all
    if tool_name in expected_tools:
        # It's an expected tool but already satisfied or out of order
        return Classification.WRONG_TOOL, None

    return Classification.WRONG_TOOL, None


def _evaluate_trial_success(
    attempts: list[AttemptRecord],
    expected_tools: list[str],
    order_sensitive: bool,
) -> bool:
    """Determine if all expected tools were called correctly.

    Uses subset match: expected tools must appear in order within the
    call sequence. Extra tools are allowed.

    Args:
        attempts: All tool calls made during the trial.
        expected_tools: Expected tool sequence.
        order_sensitive: Whether order matters.

    Returns:
        True if all expected tools were satisfied in order.
    """
    if not expected_tools:
        return True

    if order_sensitive:
        expected_idx = 0
        for attempt in attempts:
            if attempt.classification == Classification.CORRECT:
                if (
                    attempt.matched_expected_step is not None
                    and attempt.matched_expected_step == expected_idx
                ):
                    expected_idx += 1
                    if expected_idx >= len(expected_tools):
                        return True
        return expected_idx >= len(expected_tools)
    else:
        satisfied = set()
        for attempt in attempts:
            if (
                attempt.classification == Classification.CORRECT
                and attempt.matched_expected_step is not None
            ):
                satisfied.add(attempt.matched_expected_step)
        return len(satisfied) >= len(expected_tools)


def _check_tools_against_sequence(
    attempts: list[AttemptRecord],
    expected_tools: list[str],
    order_sensitive: bool,
) -> bool:
    """Check if attempts satisfy an expected tool sequence (fresh evaluation).

    Unlike _evaluate_trial_success, this does not rely on pre-classified
    attempt records. It re-evaluates tool names directly against the
    expected sequence.

    Args:
        attempts: All tool calls made during the trial.
        expected_tools: Expected tool sequence to check against.
        order_sensitive: Whether order matters.

    Returns:
        True if all expected tools appear in the attempt sequence.
    """
    if not expected_tools:
        return True

    tool_names = [a.tool_name for a in attempts if a.tool_name]

    if order_sensitive:
        expected_idx = 0
        for name in tool_names:
            if expected_idx < len(expected_tools) and name == expected_tools[expected_idx]:
                expected_idx += 1
                if expected_idx >= len(expected_tools):
                    return True
        return expected_idx >= len(expected_tools)
    else:
        remaining = list(expected_tools)
        for name in tool_names:
            if name in remaining:
                remaining.remove(name)
        return len(remaining) == 0


def _call_with_backoff(
    client: anthropic.Anthropic,
    model: str,
    system: str,
    tools: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    max_retries: int = 5,
) -> anthropic.types.Message:
    """Call Anthropic API with exponential backoff on rate limits.

    Args:
        client: Anthropic client instance.
        model: Model ID.
        system: System prompt.
        tools: Tool definitions.
        messages: Conversation messages.
        max_retries: Maximum retry attempts.

    Returns:
        API response message.

    Raises:
        anthropic.RateLimitError: If retries exhausted.
    """
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(
                model=model,
                max_tokens=4096,
                system=system,
                tools=tools,
                messages=messages,
            )
        except anthropic.RateLimitError:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
            logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
    # Unreachable, but satisfies type checker
    raise anthropic.RateLimitError("Exhausted retries")  # pragma: no cover


async def run_single_trial(
    prompt_text: str,
    tools: list[dict[str, Any]],
    expected_tools: list[str],
    config: RunConfig,
    trial_number: int = 1,
    order_sensitive: bool = True,
    session: ClientSession | None = None,
    expected_tools_alt: list[list[str]] | None = None,
) -> TrialResult:
    """Execute a single trial of a prompt.

    Runs the agentic loop: send prompt to Claude, capture tool calls,
    return mock or live results, continue until done or max attempts.

    Args:
        prompt_text: The natural-language prompt to send.
        tools: Tool definitions in Anthropic format.
        expected_tools: Expected tool names in order.
        config: Run configuration.
        trial_number: 1-indexed trial number.
        order_sensitive: Whether tool order matters.
        session: MCP client session (for live mode).

    Returns:
        TrialResult with all attempt records.
    """
    client = anthropic.Anthropic()
    attempts: list[AttemptRecord] = []
    next_expected_idx = 0
    sequence_pos = 0
    total_input_tokens = 0
    total_output_tokens = 0
    budget_exceeded = False

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": prompt_text},
    ]

    for _attempt_round in range(config.max_attempts):
        response = _call_with_backoff(
            client, config.model, SYSTEM_PROMPT, tools, messages
        )

        # Track token usage for this API call
        round_input = response.usage.input_tokens if response.usage else 0
        round_output = response.usage.output_tokens if response.usage else 0
        total_input_tokens += round_input
        total_output_tokens += round_output

        # Check if the LLM wants to call tools
        if response.stop_reason != "tool_use":
            # LLM responded with text only (no tool call)
            if not attempts and response.stop_reason == "end_turn":
                sequence_pos += 1
                attempts.append(AttemptRecord(
                    sequence_position=sequence_pos,
                    tool_name="",
                    parameters={},
                    classification=Classification.NO_TOOL_CALL,
                    matched_expected_step=None,
                    input_tokens=round_input,
                    output_tokens=round_output,
                ))
            break

        # Process all tool_use blocks in the response
        tool_results = []
        tool_use_count = sum(1 for b in response.content if b.type == "tool_use")
        # Split round tokens evenly across tool_use blocks in this response
        per_block_input = round_input // max(tool_use_count, 1)
        per_block_output = round_output // max(tool_use_count, 1)
        block_idx = 0
        for block in response.content:
            if block.type == "tool_use":
                block_idx += 1
                sequence_pos += 1
                tool_name = block.name
                parameters = block.input if isinstance(block.input, dict) else {}

                classification, matched_step = _classify_tool_call(
                    tool_name, parameters, expected_tools, next_expected_idx, order_sensitive
                )
                if classification == Classification.CORRECT and matched_step is not None:
                    next_expected_idx = matched_step + 1

                # Last block gets remainder tokens to avoid rounding loss
                if block_idx == tool_use_count:
                    block_input = round_input - per_block_input * (tool_use_count - 1)
                    block_output = round_output - per_block_output * (tool_use_count - 1)
                else:
                    block_input = per_block_input
                    block_output = per_block_output

                attempts.append(AttemptRecord(
                    sequence_position=sequence_pos,
                    tool_name=tool_name,
                    parameters=parameters,
                    classification=classification,
                    matched_expected_step=matched_step,
                    input_tokens=block_input,
                    output_tokens=block_output,
                ))

                # Get tool response
                if config.mode == "mock":
                    tool_response = get_mock_response(tool_name, parameters)
                else:
                    # Live mode: call real MCP server
                    if session is None:
                        tool_response = {"error": "No MCP session for live mode"}
                    else:
                        result = await session.call_tool(tool_name, parameters)
                        tool_response = (
                            json.loads(result.content[0].text)
                            if result.content
                            else {"success": True}
                        )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(tool_response),
                })

        # Add assistant response and tool results to conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # Check if all expected tools are satisfied
        if next_expected_idx >= len(expected_tools):
            break

        # Check token budget
        if config.max_tokens_per_trial > 0 and total_input_tokens >= config.max_tokens_per_trial:
            budget_exceeded = True
            logger.warning(
                f"Token budget exceeded ({total_input_tokens} >= "
                f"{config.max_tokens_per_trial}), stopping trial"
            )
            break

    success = _evaluate_trial_success(attempts, expected_tools, order_sensitive)

    # If primary expected_tools failed, try alternative sequences
    if not success and expected_tools_alt:
        for alt_tools in expected_tools_alt:
            if _check_tools_against_sequence(attempts, alt_tools, order_sensitive):
                success = True
                break

    return TrialResult(
        trial_number=trial_number,
        success=success,
        attempts=attempts,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        budget_exceeded=budget_exceeded,
    )


async def run_prompt(
    prompt_text: str,
    prompt_style: str,
    expected_tools: list[str],
    config: RunConfig,
    tools: list[dict[str, Any]],
    order_sensitive: bool = True,
    session: ClientSession | None = None,
    expected_tools_alt: list[list[str]] | None = None,
) -> VariantResult:
    """Execute a single prompt variant across N trials.

    Each trial is a fresh conversation.

    Args:
        prompt_text: The prompt to test.
        prompt_style: Style category of the prompt.
        expected_tools: Expected tool sequence.
        config: Run configuration.
        tools: Anthropic tool definitions.
        order_sensitive: Whether tool order matters.
        session: MCP session for live mode.

    Returns:
        VariantResult with aggregated statistics.
    """
    trials: list[TrialResult] = []

    for i in range(config.trials):
        logger.info(f"  Trial {i + 1}/{config.trials} for: {prompt_text[:60]}...")
        trial = await run_single_trial(
            prompt_text=prompt_text,
            tools=tools,
            expected_tools=expected_tools,
            config=config,
            trial_number=i + 1,
            order_sensitive=order_sensitive,
            session=session,
            expected_tools_alt=expected_tools_alt,
        )
        trials.append(trial)

    return _aggregate_variant_result(prompt_text, prompt_style, trials, expected_tools)


def _aggregate_variant_result(
    prompt_text: str,
    prompt_style: str,
    trials: list[TrialResult],
    expected_tools: list[str],
) -> VariantResult:
    """Aggregate trial results into a VariantResult."""
    if not trials:
        return VariantResult(prompt_text=prompt_text, prompt_style=prompt_style, trials=[])

    total = len(trials)
    successes = sum(1 for t in trials if t.success)
    success_rate = successes / total if total > 0 else 0.0

    # First-attempt rate: first tool call was correct
    first_correct = 0
    first_tool_counter: Counter[str] = Counter()
    for trial in trials:
        if trial.attempts:
            first_tool = trial.attempts[0].tool_name
            if first_tool:
                first_tool_counter[first_tool] += 1
            if trial.attempts[0].classification == Classification.CORRECT:
                first_correct += 1

    first_attempt_rate = first_correct / total if total > 0 else 0.0

    # Average attempts to success (excluding failures)
    successful_attempt_counts = [t.total_attempts for t in trials if t.success]
    avg_attempts = (
        sum(successful_attempt_counts) / len(successful_attempt_counts)
        if successful_attempt_counts
        else 0.0
    )

    most_common_first = first_tool_counter.most_common(1)[0][0] if first_tool_counter else ""

    # Build desire path entries
    desire_path = _compute_desire_path(trials)

    return VariantResult(
        prompt_text=prompt_text,
        prompt_style=prompt_style,
        trials=trials,
        first_attempt_rate=first_attempt_rate,
        success_rate=success_rate,
        avg_attempts=avg_attempts,
        most_common_first_tool=most_common_first,
        desire_path=desire_path,
    )


def _compute_desire_path(trials: list[TrialResult]) -> list[DesirePathEntry]:
    """Compute desire path entries from trial results."""
    tool_data: dict[str, dict[str, Any]] = {}

    for trial in trials:
        seen_in_trial: set[str] = set()
        for attempt in trial.attempts:
            name = attempt.tool_name
            if not name:
                continue

            if name not in tool_data:
                tool_data[name] = {
                    "frequency": 0,
                    "positions": [],
                    "as_first_call": 0,
                }

            if name not in seen_in_trial:
                tool_data[name]["frequency"] += 1
                seen_in_trial.add(name)

            tool_data[name]["positions"].append(attempt.sequence_position)

            if attempt.sequence_position == 1:
                tool_data[name]["as_first_call"] += 1

    entries = []
    for tool_name, data in sorted(tool_data.items(), key=lambda x: -x[1]["frequency"]):
        positions = data["positions"]
        entries.append(DesirePathEntry(
            tool_name=tool_name,
            frequency=data["frequency"],
            avg_position=sum(positions) / len(positions) if positions else 0.0,
            as_first_call=data["as_first_call"],
        ))

    return entries


async def run_intent(
    intent: UserIntent,
    config: RunConfig,
    tools: list[dict[str, Any]],
    session: ClientSession | None = None,
) -> IntentResult:
    """Execute all prompt variants for an intent.

    Args:
        intent: The intent to test.
        config: Run configuration.
        tools: Anthropic tool definitions.
        session: MCP session for live mode.

    Returns:
        IntentResult with aggregated statistics.
    """
    logger.info(f"Running intent: {intent.name} ({len(intent.variants)} variants)")

    variant_results: list[VariantResult] = []
    for variant in intent.variants:
        result = await run_prompt(
            prompt_text=variant.text,
            prompt_style=variant.style.value,
            expected_tools=intent.expected_tools,
            config=config,
            tools=tools,
            order_sensitive=intent.order_sensitive,
            session=session,
            expected_tools_alt=intent.expected_tools_alt or None,
        )
        variant_results.append(result)

    # Aggregate across variants
    all_trials = [t for vr in variant_results for t in vr.trials]
    total = len(all_trials)
    successes = sum(1 for t in all_trials if t.success)
    first_correct = sum(
        1 for t in all_trials
        if t.attempts and t.attempts[0].classification == Classification.CORRECT
    )

    return IntentResult(
        intent_name=intent.name,
        variant_results=variant_results,
        first_attempt_rate=first_correct / total if total > 0 else 0.0,
        success_rate=successes / total if total > 0 else 0.0,
        failure_rate=(total - successes) / total if total > 0 else 0.0,
    )


def _get_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


async def run_test_suite(
    suite: TestSuite,
    config: RunConfig,
    intent_filter: str | None = None,
) -> TestRun:
    """Execute all intents in a test suite.

    Args:
        suite: The test suite to run.
        config: Run configuration.
        intent_filter: Optional intent name to run only one intent.

    Returns:
        TestRun with all results.
    """
    logger.info(f"Starting test suite: {suite.name}")
    logger.info(f"Model: {config.model}, Mode: {config.mode}, Trials: {config.trials}")

    # Get tool definitions from MCP server
    tools, tool_descriptions = await _get_mcp_tools(config)

    test_run = TestRun(
        commit_hash=_get_commit_hash(),
        model=config.model,
        mode=config.mode,
        trials_per_prompt=config.trials,
        max_attempts=config.max_attempts,
        tool_descriptions=tool_descriptions,
    )

    # Filter intents if requested
    intents = suite.intents
    if intent_filter:
        intents = [i for i in intents if i.name == intent_filter]
        if not intents:
            available = [i.name for i in suite.intents]
            raise ValueError(
                f"Intent '{intent_filter}' not found. Available: {available}"
            )

    # Run each intent
    session = None  # Live mode would establish a persistent session
    for intent in intents:
        result = await run_intent(intent, config, tools, session)
        test_run.results.append(result)

    return test_run
