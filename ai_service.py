"""
ai_service.py
--------------
All AI/LLM logic lives here, fully isolated from weather-fetching and from
Flask routing. Two interchangeable providers are supported behind a single
`AIProvider` interface:

  * OpenAIProvider    -> uses the OpenAI *Responses* API (`client.responses.create`)
  * AnthropicProvider -> uses the Claude *Messages* API (`client.messages.create`)

`AIService` is the only class the rest of the app talks to. It builds
prompts (via prompt.py), calls whichever provider is configured, and parses
the results into plain Python data structures.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict

from prompt import PromptBuilder
from weather_service import WeatherData


class AIServiceError(Exception):
    """Raised when the AI provider fails or returns something unusable."""


class WeatherInsights(TypedDict):
    explanation: str
    clothing: str
    travel: str
    sports: str
    comfort_score: int
    comfort_label: str


class ChatMessage(TypedDict):
    role: str  # "user" | "assistant"
    content: str


# --------------------------------------------------------------------------
# Provider interface + implementations
# --------------------------------------------------------------------------


class AIProvider(ABC):
    """Common interface every AI backend must implement."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 900,
    ) -> str:
        """Return the raw text response for a single-turn (system, user) prompt."""

    @abstractmethod
    def generate_chat(
        self,
        system_prompt: str,
        history: List[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Return the raw text response for a multi-turn conversation."""


class OpenAIProvider(AIProvider):
    """Wraps OpenAI's newest Responses API (`client.responses.create`)."""

    def __init__(self, api_key: str, model: str) -> None:
        # Imported lazily so the package is only required if this provider
        # is actually selected.
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 900,
    ) -> str:
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=system_prompt,
                input=user_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            return self._extract_text(response)
        except Exception as exc:  # noqa: BLE001 - surface as a domain error
            raise AIServiceError(f"OpenAI request failed: {exc}") from exc

    def generate_chat(
        self,
        system_prompt: str,
        history: List[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        try:
            # The Responses API accepts a list of role/content turns directly.
            input_turns = [{"role": m["role"], "content": m["content"]} for m in history]
            response = self._client.responses.create(
                model=self._model,
                instructions=system_prompt,
                input=input_turns,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            return self._extract_text(response)
        except Exception as exc:  # noqa: BLE001
            raise AIServiceError(f"OpenAI request failed: {exc}") from exc

    @staticmethod
    def _extract_text(response: Any) -> str:
        # `output_text` is the convenience property on the Responses API
        # result that concatenates all text output segments.
        text = getattr(response, "output_text", None)
        if text:
            return text.strip()
        raise AIServiceError("OpenAI response contained no text output.")


class AnthropicProvider(AIProvider):
    """Wraps Claude's Messages API (`client.messages.create`)."""

    def __init__(self, api_key: str, model: str) -> None:
        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key)
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 900,
    ) -> str:
        return self.generate_chat(
            system_prompt,
            [{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_chat(
        self,
        system_prompt: str,
        history: List[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                system=system_prompt,
                messages=[{"role": m["role"], "content": m["content"]} for m in history],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
            text = "".join(parts).strip()
            if not text:
                raise AIServiceError("Anthropic response contained no text output.")
            return text
        except AIServiceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise AIServiceError(f"Anthropic request failed: {exc}") from exc


def build_provider(
    provider_name: str,
    *,
    openai_api_key: str,
    openai_model: str,
    anthropic_api_key: str,
    anthropic_model: str,
) -> AIProvider:
    """Factory: construct the configured AIProvider implementation."""
    if provider_name == "openai":
        return OpenAIProvider(api_key=openai_api_key, model=openai_model)
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=anthropic_api_key, model=anthropic_model)
    raise AIServiceError(f"Unknown AI provider '{provider_name}'.")


# --------------------------------------------------------------------------
# High-level service used by the Flask app
# --------------------------------------------------------------------------


class AIService:
    """
    Domain-level AI operations for the weather assistant. Translates weather
    data into prompts (via PromptBuilder), calls the configured provider, and
    parses results into clean Python objects. Flask routes should only ever
    talk to this class, never to a provider directly.
    """

    def __init__(self, provider: AIProvider, *, temperature: float = 0.7, max_tokens: int = 900) -> None:
        self._provider = provider
        self._temperature = temperature
        self._max_tokens = max_tokens

    # -- feature: full insight bundle for one city -------------------------
    def get_weather_insights(self, weather: WeatherData) -> WeatherInsights:
        system, user = PromptBuilder.weather_insights(weather)
        raw = self._provider.generate(
            system, user, temperature=self._temperature, max_tokens=self._max_tokens
        )
        data = self._parse_json_object(raw)

        try:
            score = int(data["comfort_score"])
        except (KeyError, ValueError, TypeError):
            score = 50
        score = max(0, min(100, score))

        return WeatherInsights(
            explanation=str(data.get("explanation", "")).strip(),
            clothing=str(data.get("clothing", "")).strip(),
            travel=str(data.get("travel", "")).strip(),
            sports=str(data.get("sports", "")).strip(),
            comfort_score=score,
            comfort_label=str(data.get("comfort_label", "Moderate")).strip(),
        )

    # -- feature: compare multiple cities -----------------------------------
    def compare_cities(self, weather_list: List[WeatherData]) -> str:
        if len(weather_list) < 2:
            raise AIServiceError("At least two cities are required for a comparison.")
        system, user = PromptBuilder.compare_cities(weather_list)
        return self._provider.generate(
            system, user, temperature=self._temperature, max_tokens=self._max_tokens
        )

    # -- feature: open-ended chat -------------------------------------------
    def chat(
        self,
        message: str,
        history: List[ChatMessage],
        weather_context: Optional[WeatherData] = None,
    ) -> str:
        system, user = PromptBuilder.chat(message, weather_context)
        turns: List[ChatMessage] = [*history, {"role": "user", "content": user}]
        return self._provider.generate_chat(
            system, turns, temperature=self._temperature, max_tokens=500
        )

    # -- feature: suggested prompt chips ------------------------------------
    def suggested_prompts(self, weather: Optional[WeatherData]) -> List[str]:
        system, user = PromptBuilder.suggested_prompts(weather)
        raw = self._provider.generate(system, user, temperature=0.8, max_tokens=200)
        parsed = self._parse_json_array(raw)
        if parsed:
            return [str(item) for item in parsed][:4]
        return [
            "What should I wear today?",
            "Is it a good day for a run?",
            "Compare this city to Paris",
            "Will it rain later?",
        ]

    # -- internals ------------------------------------------------------------
    @staticmethod
    def _strip_code_fences(text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @classmethod
    def _parse_json_object(cls, text: str) -> Dict[str, Any]:
        cleaned = cls._strip_code_fences(text)
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        # Fallback: try to locate the first {...} block in the text.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
        raise AIServiceError("Could not parse a structured response from the AI model.")

    @classmethod
    def _parse_json_array(cls, text: str) -> Optional[List[Any]]:
        cleaned = cls._strip_code_fences(text)
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return None
