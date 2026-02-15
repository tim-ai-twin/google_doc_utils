"""YAML test suite loader and validation."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import PromptStyle, PromptVariant, TestSuite, UserIntent


class ValidationError(Exception):
    """Raised when a YAML test definition is invalid."""


def load_test_suite(path: str) -> TestSuite:
    """Load a test suite from a YAML file or directory of YAML files.

    Args:
        path: Path to a YAML file or directory containing YAML files.

    Returns:
        TestSuite with all intents loaded.

    Raises:
        FileNotFoundError: If path does not exist.
        ValidationError: If YAML structure is invalid.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Test suite path not found: {path}")

    if p.is_file():
        return _load_single_file(p)
    elif p.is_dir():
        return _load_directory(p)
    else:
        raise ValidationError(f"Path is neither a file nor directory: {path}")


def _load_directory(directory: Path) -> TestSuite:
    """Load and merge all YAML files in a directory."""
    yaml_files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
    if not yaml_files:
        raise ValidationError(f"No YAML files found in directory: {directory}")

    all_intents: list[UserIntent] = []
    suite_name = directory.name
    metadata: dict = {}

    for yaml_file in yaml_files:
        suite = _load_single_file(yaml_file)
        all_intents.extend(suite.intents)
        if suite.metadata:
            metadata.update(suite.metadata)
        if suite.name != "unnamed":
            suite_name = suite.name

    return TestSuite(name=suite_name, intents=all_intents, metadata=metadata)


def _load_single_file(filepath: Path) -> TestSuite:
    """Load a test suite from a single YAML file."""
    try:
        with open(filepath) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in {filepath}: {e}") from e

    if not isinstance(data, dict):
        raise ValidationError(f"YAML root must be a mapping in {filepath}")

    # Extract suite metadata
    suite_data = data.get("suite", {})
    suite_name = suite_data.get("name", "unnamed") if suite_data else "unnamed"
    defaults = suite_data.get("defaults", {}) if suite_data else {}

    # Parse intents
    raw_intents = data.get("intents", [])
    if not raw_intents:
        raise ValidationError(f"No intents defined in {filepath}")

    intents = [_parse_intent(raw, filepath) for raw in raw_intents]

    return TestSuite(name=suite_name, intents=intents, metadata=defaults)


def _parse_intent(raw: dict, filepath: Path) -> UserIntent:
    """Parse a single intent from raw YAML data."""
    if not isinstance(raw, dict):
        raise ValidationError(f"Intent must be a mapping in {filepath}")

    # Required fields
    name = raw.get("name")
    if not name:
        raise ValidationError(f"Intent missing 'name' in {filepath}")

    expected_tools = raw.get("expected_tools")
    if not expected_tools or not isinstance(expected_tools, list):
        raise ValidationError(f"Intent '{name}' missing 'expected_tools' list in {filepath}")

    raw_variants = raw.get("variants")
    if not raw_variants or not isinstance(raw_variants, list):
        raise ValidationError(f"Intent '{name}' missing 'variants' list in {filepath}")

    # Optional fields
    description = raw.get("description", "")
    order_sensitive = raw.get("order_sensitive", True)
    expected_tools_alt = raw.get("expected_tools_alt", [])

    variants = [_parse_variant(v, name, filepath) for v in raw_variants]

    return UserIntent(
        name=name,
        description=description,
        expected_tools=expected_tools,
        expected_tools_alt=expected_tools_alt,
        variants=variants,
        order_sensitive=order_sensitive,
    )


def _parse_variant(raw: dict, intent_name: str, filepath: Path) -> PromptVariant:
    """Parse a single prompt variant from raw YAML data."""
    if not isinstance(raw, dict):
        raise ValidationError(
            f"Variant must be a mapping in intent '{intent_name}' in {filepath}"
        )

    text = raw.get("text")
    if not text:
        raise ValidationError(
            f"Variant missing 'text' in intent '{intent_name}' in {filepath}"
        )

    style_str = raw.get("style")
    if not style_str:
        raise ValidationError(
            f"Variant missing 'style' in intent '{intent_name}' in {filepath}"
        )

    try:
        style = PromptStyle(style_str)
    except ValueError as e:
        valid = ", ".join(s.value for s in PromptStyle)
        raise ValidationError(
            f"Invalid style '{style_str}' in intent '{intent_name}' in {filepath}. "
            f"Valid styles: {valid}"
        ) from e

    context = raw.get("context")
    return PromptVariant(text=text, style=style, context=context)
