"""
config.py
---------
Centralized application configuration.

All secrets and environment-specific values are loaded from environment
variables (via python-dotenv for local development). Nothing sensitive is
ever hardcoded here. Call `Config.validate()` at startup to fail fast with a
clear error message if required configuration is missing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

# Load variables from a local .env file, if present. In production
# (Render, Railway, Docker, etc.) real environment variables are used
# instead and this call is a harmless no-op.
load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    """Immutable application configuration, populated from the environment."""

    # --- Flask ---------------------------------------------------------
    SECRET_KEY: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    DEBUG: bool = field(default_factory=lambda: _get_bool("FLASK_DEBUG", False))
    HOST: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    PORT: int = field(default_factory=lambda: _get_int("PORT", 5000))

    # --- Weather provider ------------------------------------------------
    WEATHER_API_KEY: str = field(default_factory=lambda: os.getenv("WEATHER_API_KEY", ""))
    WEATHER_API_BASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5"
        )
    )
    WEATHER_UNITS: str = field(default_factory=lambda: os.getenv("WEATHER_UNITS", "metric"))

    # --- AI provider -----------------------------------------------------
    # "openai" (Responses API) or "anthropic" (Messages API)
    AI_PROVIDER: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai").lower())

    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    OPENAI_MODEL: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1"))

    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    ANTHROPIC_MODEL: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    )

    AI_MAX_TOKENS: int = field(default_factory=lambda: _get_int("AI_MAX_TOKENS", 900))
    AI_TEMPERATURE: float = field(
        default_factory=lambda: float(os.getenv("AI_TEMPERATURE", "0.7"))
    )

    # --- Misc / limits -----------------------------------------------------
    MAX_CITIES_COMPARE: int = field(default_factory=lambda: _get_int("MAX_CITIES_COMPARE", 4))
    MAX_HISTORY_MESSAGES: int = field(default_factory=lambda: _get_int("MAX_HISTORY_MESSAGES", 12))

    def validate(self) -> List[str]:
        """
        Validate that required configuration is present.

        Returns a list of human-readable problems. An empty list means the
        configuration is valid. This never raises so the caller can decide
        whether missing config is fatal (e.g. at boot) or just a warning.
        """
        problems: List[str] = []

        if not self.WEATHER_API_KEY:
            problems.append(
                "WEATHER_API_KEY is not set. Get a free key at "
                "https://openweathermap.org/api and add it to your .env file."
            )

        if self.AI_PROVIDER not in {"openai", "anthropic"}:
            problems.append(
                f"AI_PROVIDER='{self.AI_PROVIDER}' is invalid. Use 'openai' or 'anthropic'."
            )

        if self.AI_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            problems.append(
                "OPENAI_API_KEY is not set. Get a key at "
                "https://platform.openai.com/api-keys and add it to your .env file."
            )

        if self.AI_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            problems.append(
                "ANTHROPIC_API_KEY is not set. Get a key at "
                "https://console.anthropic.com/settings/keys and add it to your .env file."
            )

        if not self.SECRET_KEY:
            problems.append(
                "SECRET_KEY is not set. Generate one with "
                "`python -c \"import secrets; print(secrets.token_hex(32))\"`."
            )

        return problems

    def require_valid(self) -> None:
        """Raise ConfigError with all problems listed, or return silently."""
        problems = self.validate()
        if problems:
            bullet_list = "\n".join(f"  - {p}" for p in problems)
            raise ConfigError(
                "Invalid configuration detected:\n"
                f"{bullet_list}\n\n"
                "Copy .env.example to .env and fill in the missing values."
            )


# Single shared instance used throughout the app.
config = Config()
