"""Unit tests for YAML test suite loader."""


import pytest
import yaml

from extended_google_doc_utils.discoverability.loader import (
    ValidationError,
    load_test_suite,
)
from extended_google_doc_utils.discoverability.models import PromptStyle


@pytest.fixture
def valid_yaml_content():
    return {
        "suite": {"name": "test-suite", "defaults": {"trials": 5}},
        "intents": [
            {
                "name": "test-intent",
                "description": "A test intent",
                "expected_tools": ["tool_a", "tool_b"],
                "order_sensitive": True,
                "variants": [
                    {"text": "Do the thing", "style": "natural"},
                    {"text": "Explicitly do the thing", "style": "explicit"},
                ],
            }
        ],
    }


@pytest.fixture
def yaml_file(valid_yaml_content, tmp_path):
    filepath = tmp_path / "test.yaml"
    with open(filepath, "w") as f:
        yaml.dump(valid_yaml_content, f)
    return str(filepath)


class TestLoadTestSuite:
    def test_load_valid_yaml(self, yaml_file):
        suite = load_test_suite(yaml_file)
        assert suite.name == "test-suite"
        assert len(suite.intents) == 1
        assert suite.intents[0].name == "test-intent"
        assert suite.intents[0].expected_tools == ["tool_a", "tool_b"]
        assert suite.intents[0].order_sensitive is True
        assert len(suite.intents[0].variants) == 2
        assert suite.intents[0].variants[0].style == PromptStyle.NATURAL
        assert suite.intents[0].variants[1].style == PromptStyle.EXPLICIT
        assert suite.metadata == {"trials": 5}

    def test_load_directory(self, valid_yaml_content, tmp_path):
        # Write two YAML files
        for i, name in enumerate(["a.yaml", "b.yaml"]):
            content = dict(valid_yaml_content)
            content["intents"] = [
                {
                    "name": f"intent-{i}",
                    "description": f"Intent {i}",
                    "expected_tools": ["tool_a"],
                    "variants": [{"text": f"Prompt {i}", "style": "natural"}],
                }
            ]
            with open(tmp_path / name, "w") as f:
                yaml.dump(content, f)

        suite = load_test_suite(str(tmp_path))
        assert len(suite.intents) == 2

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_test_suite("/nonexistent/path.yaml")

    def test_empty_directory(self, tmp_path):
        with pytest.raises(ValidationError, match="No YAML files"):
            load_test_suite(str(tmp_path))

    def test_missing_intents(self, tmp_path):
        filepath = tmp_path / "bad.yaml"
        with open(filepath, "w") as f:
            yaml.dump({"suite": {"name": "bad"}}, f)
        with pytest.raises(ValidationError, match="No intents"):
            load_test_suite(str(filepath))

    def test_missing_intent_name(self, tmp_path):
        filepath = tmp_path / "bad.yaml"
        with open(filepath, "w") as f:
            yaml.dump(
                {
                    "intents": [
                        {
                            "expected_tools": ["tool_a"],
                            "variants": [{"text": "test", "style": "natural"}],
                        }
                    ]
                },
                f,
            )
        with pytest.raises(ValidationError, match="missing 'name'"):
            load_test_suite(str(filepath))

    def test_missing_expected_tools(self, tmp_path):
        filepath = tmp_path / "bad.yaml"
        with open(filepath, "w") as f:
            yaml.dump(
                {
                    "intents": [
                        {
                            "name": "test",
                            "variants": [{"text": "test", "style": "natural"}],
                        }
                    ]
                },
                f,
            )
        with pytest.raises(ValidationError, match="missing 'expected_tools'"):
            load_test_suite(str(filepath))

    def test_missing_variant_text(self, tmp_path):
        filepath = tmp_path / "bad.yaml"
        with open(filepath, "w") as f:
            yaml.dump(
                {
                    "intents": [
                        {
                            "name": "test",
                            "expected_tools": ["tool_a"],
                            "variants": [{"style": "natural"}],
                        }
                    ]
                },
                f,
            )
        with pytest.raises(ValidationError, match="missing 'text'"):
            load_test_suite(str(filepath))

    def test_invalid_style(self, tmp_path):
        filepath = tmp_path / "bad.yaml"
        with open(filepath, "w") as f:
            yaml.dump(
                {
                    "intents": [
                        {
                            "name": "test",
                            "expected_tools": ["tool_a"],
                            "variants": [{"text": "test", "style": "invalid_style"}],
                        }
                    ]
                },
                f,
            )
        with pytest.raises(ValidationError, match="Invalid style"):
            load_test_suite(str(filepath))

    def test_malformed_yaml(self, tmp_path):
        filepath = tmp_path / "bad.yaml"
        with open(filepath, "w") as f:
            f.write(": invalid: yaml: {{{{")
        with pytest.raises(ValidationError, match="Invalid YAML"):
            load_test_suite(str(filepath))

    def test_variant_with_context(self, tmp_path):
        filepath = tmp_path / "ctx.yaml"
        with open(filepath, "w") as f:
            yaml.dump(
                {
                    "intents": [
                        {
                            "name": "test",
                            "expected_tools": ["tool_a"],
                            "variants": [
                                {
                                    "text": "test prompt",
                                    "style": "natural",
                                    "context": "doc_id=123",
                                }
                            ],
                        }
                    ]
                },
                f,
            )
        suite = load_test_suite(str(filepath))
        assert suite.intents[0].variants[0].context == "doc_id=123"

    def test_order_sensitive_default(self, tmp_path):
        filepath = tmp_path / "default.yaml"
        with open(filepath, "w") as f:
            yaml.dump(
                {
                    "intents": [
                        {
                            "name": "test",
                            "expected_tools": ["tool_a"],
                            "variants": [{"text": "test", "style": "natural"}],
                        }
                    ]
                },
                f,
            )
        suite = load_test_suite(str(filepath))
        assert suite.intents[0].order_sensitive is True
