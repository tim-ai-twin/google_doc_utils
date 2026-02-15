# Data Model: MCP Discoverability Testing

**Feature**: 002-mcp-discoverability-testing
**Date**: 2026-02-13

## Entities

### UserIntent

Represents a named user goal the MCP server should support.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Unique identifier (e.g., "edit-section") |
| description | string | Human-readable explanation of the intent |
| expected_tools | list[string] | Ordered list of tool names that should be called |
| order_sensitive | bool | Whether tool order matters (default: true) |
| prompt_variants | list[PromptVariant] | Different phrasings of this intent |

### PromptVariant

A specific phrasing of a user intent for testing.

| Field | Type | Description |
|-------|------|-------------|
| text | string | The natural-language prompt to send to the LLM |
| style | enum | Category: "explicit", "natural", "indirect", "ambiguous" |
| context | string (optional) | Additional context provided with the prompt (e.g., a document ID) |

### TestSuite

A collection of intents loaded from YAML files.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Suite name (e.g., "default") |
| intents | list[UserIntent] | All intents in this suite |
| metadata | dict | Suite-level config (default trials, max attempts) |

### TestRun

A single execution of a test suite (or subset).

| Field | Type | Description |
|-------|------|-------------|
| id | string | UUID for this run |
| timestamp | datetime | When the run started |
| commit_hash | string | Git commit hash of the MCP server |
| model | string | LLM model used (e.g., "claude-sonnet-4-20250514") |
| mode | enum | "mock" or "live" |
| trials_per_prompt | int | Number of independent trials (default: 10) |
| max_attempts | int | Max tool calls per trial before failure |
| tool_descriptions | dict[str, str] | Snapshot of all MCP tool descriptions at test time |
| results | list[IntentResult] | Results per intent |

### IntentResult

Aggregate results for a single intent across all its prompt variants and trials.

| Field | Type | Description |
|-------|------|-------------|
| intent_name | string | Reference to UserIntent.name |
| variant_results | list[VariantResult] | Results per prompt variant |
| first_attempt_rate | float | % of trials where first tool call was correct (across all variants) |
| success_rate | float | % of trials that eventually succeeded |
| failure_rate | float | % of trials that exhausted max attempts |

### VariantResult

Results for a single prompt variant across its trials.

| Field | Type | Description |
|-------|------|-------------|
| prompt_text | string | The prompt that was tested |
| prompt_style | string | Style category of the prompt |
| trials | list[TrialResult] | Individual trial results |
| first_attempt_rate | float | % of trials with correct first tool call |
| success_rate | float | % of trials that succeeded |
| avg_attempts | float | Mean attempts-to-success (excluding failures) |
| most_common_first_tool | string | Tool most frequently called first |
| desire_path | list[DesirePathEntry] | Aggregated tool selection patterns |

### TrialResult

Result of a single independent trial of a prompt.

| Field | Type | Description |
|-------|------|-------------|
| trial_number | int | 1-indexed trial number |
| success | bool | Whether the expected tool sequence was completed |
| attempts | list[AttemptRecord] | Every tool call made, in order |
| total_attempts | int | Number of tool calls made |

### AttemptRecord

A single tool call made by the LLM during a trial.

| Field | Type | Description |
|-------|------|-------------|
| sequence_position | int | 1-indexed position in the conversation |
| tool_name | string | Name of the tool called |
| parameters | dict | Parameters the LLM provided |
| classification | enum | "correct", "right_tool_wrong_params", "wrong_tool", "no_tool_call" |
| matched_expected_step | int (optional) | Which step in expected_tools this satisfied (if any) |

### DesirePathEntry

Aggregated pattern of what the LLM tries for a given intent/variant.

| Field | Type | Description |
|-------|------|-------------|
| tool_name | string | A tool that was called |
| frequency | int | How many trials called this tool (at any position) |
| avg_position | float | Average position in the call sequence |
| as_first_call | int | How many trials used this as the first tool call |

## State Transitions

### Trial Lifecycle

```
PENDING → RUNNING → COMPLETED (success=true)
                  → FAILED (success=false, max attempts reached)
                  → ERROR (server/LLM error)
```

### Test Run Lifecycle

```
CREATED → EXECUTING (trials running) → COMPLETED (report generated)
                                     → PARTIAL (some trials errored, report generated with warnings)
```

## Relationships

```
TestSuite 1──* UserIntent 1──* PromptVariant
TestRun 1──* IntentResult 1──* VariantResult 1──* TrialResult 1──* AttemptRecord
VariantResult 1──* DesirePathEntry
```
