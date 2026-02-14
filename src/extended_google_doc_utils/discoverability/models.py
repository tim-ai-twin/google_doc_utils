"""Data models for MCP discoverability testing."""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Classification(str, Enum):
    """Classification of a tool call against expected tools."""

    CORRECT = "correct"
    RIGHT_TOOL_WRONG_PARAMS = "right_tool_wrong_params"
    WRONG_TOOL = "wrong_tool"
    NO_TOOL_CALL = "no_tool_call"


class PromptStyle(str, Enum):
    """Style category for prompt variants."""

    EXPLICIT = "explicit"
    NATURAL = "natural"
    INDIRECT = "indirect"
    AMBIGUOUS = "ambiguous"


@dataclass
class PromptVariant:
    """A specific phrasing of a user intent for testing."""

    text: str
    style: PromptStyle
    context: str | None = None


@dataclass
class UserIntent:
    """A named user goal with expected tool call sequence."""

    name: str
    description: str
    expected_tools: list[str]
    variants: list[PromptVariant]
    order_sensitive: bool = True


@dataclass
class TestSuite:
    """A collection of intents loaded from YAML files."""

    __test__ = False  # Prevent pytest from collecting this as a test class

    name: str
    intents: list[UserIntent]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunConfig:
    """Configuration for a test run."""

    model: str = "claude-haiku-4-5-20251001"
    mode: str = "mock"  # "mock" or "live"
    trials: int = 1
    max_attempts: int = 10
    max_tokens_per_trial: int = 0  # 0 = no limit
    mcp_server_command: list[str] = field(
        default_factory=lambda: [sys.executable, "-m", "extended_google_doc_utils.mcp.server"]
    )
    credentials_path: str | None = None


@dataclass
class AttemptRecord:
    """A single tool call made by the LLM during a trial."""

    sequence_position: int
    tool_name: str
    parameters: dict[str, Any]
    classification: Classification
    matched_expected_step: int | None = None
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class TrialResult:
    """Result of a single independent trial of a prompt."""

    trial_number: int
    success: bool
    attempts: list[AttemptRecord]
    total_attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    budget_exceeded: bool = False

    def __post_init__(self):
        if self.total_attempts == 0:
            self.total_attempts = len(self.attempts)
        if self.input_tokens == 0:
            self.input_tokens = sum(a.input_tokens for a in self.attempts)
        if self.output_tokens == 0:
            self.output_tokens = sum(a.output_tokens for a in self.attempts)


@dataclass
class DesirePathEntry:
    """Aggregated pattern of what the LLM tries for a given intent/variant."""

    tool_name: str
    frequency: int
    avg_position: float
    as_first_call: int


@dataclass
class VariantResult:
    """Results for a single prompt variant across its trials."""

    prompt_text: str
    prompt_style: str
    trials: list[TrialResult]
    first_attempt_rate: float = 0.0
    success_rate: float = 0.0
    avg_attempts: float = 0.0
    most_common_first_tool: str = ""
    desire_path: list[DesirePathEntry] = field(default_factory=list)


@dataclass
class IntentResult:
    """Aggregate results for a single intent across all variants and trials."""

    intent_name: str
    variant_results: list[VariantResult]
    first_attempt_rate: float = 0.0
    success_rate: float = 0.0
    failure_rate: float = 0.0


@dataclass
class TestRun:
    """A single execution of a test suite (or subset)."""

    __test__ = False  # Prevent pytest from collecting this as a test class

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    commit_hash: str = ""
    model: str = ""
    mode: str = "mock"
    trials_per_prompt: int = 10
    max_attempts: int = 10
    tool_descriptions: dict[str, str] = field(default_factory=dict)
    results: list[IntentResult] = field(default_factory=list)
