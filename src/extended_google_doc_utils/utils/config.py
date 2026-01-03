"""Configuration utilities for environment detection and setup."""

import os
from enum import Enum


class EnvironmentType(Enum):
    """Environment where the code is running."""

    LOCAL_DEVELOPMENT = "local_development"  # Developer machine
    GITHUB_ACTIONS = "github_actions"  # CI/CD
    CLOUD_AGENT = "cloud_agent"  # Remote agent

    @classmethod
    def detect(cls) -> "EnvironmentType":
        """Auto-detect environment based on environment variables.

        Returns:
            EnvironmentType: Detected environment type

        Detection logic:
        - GITHUB_ACTIONS: if GITHUB_ACTIONS env var is set
        - CLOUD_AGENT: if CLOUD_AGENT env var is set
        - LOCAL_DEVELOPMENT: default fallback
        """
        if os.getenv("GITHUB_ACTIONS"):
            return cls.GITHUB_ACTIONS
        elif os.getenv("CLOUD_AGENT"):
            return cls.CLOUD_AGENT
        else:
            return cls.LOCAL_DEVELOPMENT
