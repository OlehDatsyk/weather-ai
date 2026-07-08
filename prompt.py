"""
prompt.py
---------
Every prompt the app sends to an AI model lives here, and nowhere else.
Keeping prompt text out of ai_service.py means the wording, tone, and output
contracts can be tuned without touching any transport/networking code, and
makes each prompt independently testable.

Each builder returns a (system_prompt, user_prompt) tuple.
"""

from __future__ import annotations

import json
from typing import List, Tuple

from weather_service import WeatherData

PromptPair = Tuple[str, str]

_BASE_PERSONA = (
    "You are Skyline, a friendly and knowledgeable weather assistant embedded "
    "in a web app. You explain meteorological conditions in clear, warm, "
    "conversational language for a general audience — never jargon-heavy, "
    "never robotic. You are concise: prefer short paragraphs and, where "
    "helpful, short bullet lists. You never invent numeric weather data — "
    "you only reason about the figures you are given."
)


class PromptBuilder:
    """Static factory of (system, user) prompt pairs for each AI feature."""

    # ---------------------------------------------------------------
    # 1. Combined per-city insight bundle (explanation, clothing,
    #    travel, sports, comfort score) — one call, structured JSON.
    # ---------------------------------------------------------------
    @staticmethod
    def weather_insights(weather: WeatherData) -> PromptPair:
        system = (
            f"{_BASE_PERSONA}\n\n"
            "You will be given live weather data for one city as JSON. "
            "Respond with ONLY a single valid JSON object (no markdown fences, "
            "no commentary before or after) with exactly these keys:\n"
            '  "explanation": string — a 2-3 sentence, plain-language read of '
            "current conditions, as if chatting with a friend.\n"
            '  "clothing": string — 2-4 sentences of specific clothing '
            "recommendations suited to the temperature, wind, and precipitation.\n"
            '  "travel": string — 2-4 sentences on whether it is a good day to '
            "travel/commute, and any precautions (driving, flights, walking).\n"
            '  "sports": string — 2-4 sentences recommending which outdoor or '
            "indoor activities/sports suit these conditions best, and which to avoid.\n"
            '  "comfort_score": integer 0-100 — a single overall weather comfort '
            "score where 100 is ideal, pleasant weather and 0 is extremely "
            "uncomfortable/dangerous.\n"
            '  "comfort_label": string — a 1-3 word label for the score, e.g. '
            '"Very Pleasant", "Uncomfortable", "Harsh".\n'
            "Base every judgement strictly on the supplied data."
        )
        user = (
            "Here is the current weather snapshot:\n"
            f"{json.dumps(weather.to_dict(), indent=2)}\n\n"
            "Produce the JSON object described in the system prompt."
        )
        return system, user

    # ---------------------------------------------------------------
    # 2. Multi-city comparison
    # ---------------------------------------------------------------
    @staticmethod
    def compare_cities(weather_list: List[WeatherData]) -> PromptPair:
        system = (
            f"{_BASE_PERSONA}\n\n"
            "You will be given live weather data for two or more cities as a "
            "JSON array. Write a comparison in clear, natural language "
            "(markdown allowed: headings, bold, bullet lists). Structure your "
            "answer as:\n"
            "1. A one-sentence headline verdict (which city currently has the "
            "most pleasant weather, and why).\n"
            "2. A short bullet comparing temperature, precipitation/condition, "
            "wind, and humidity across the cities.\n"
            "3. A short recommendation for which city best suits: outdoor "
            "activities, travel, and staying indoors/cozy.\n"
            "Base every judgement strictly on the supplied data. Keep the whole "
            "answer under 220 words."
        )
        payload = [w.to_dict() for w in weather_list]
        user = (
            "Here is the current weather snapshot for each city:\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            "Write the comparison now."
        )
        return system, user

    # ---------------------------------------------------------------
    # 3. Open-ended chat / Q&A, optionally grounded in a city's weather
    # ---------------------------------------------------------------
    @staticmethod
    def chat(message: str, weather_context: WeatherData | None) -> PromptPair:
        system = (
            f"{_BASE_PERSONA}\n\n"
            "Answer the user's question conversationally in plain text or light "
            "markdown. If real-time data (like tomorrow's exact forecast for a "
            "city you were not given data for) is not available to you, say so "
            "honestly and offer general climate/seasonal knowledge instead of "
            "inventing numbers. Keep responses under 150 words unless the "
            "question clearly needs more detail."
        )
        if weather_context is not None:
            context_note = (
                "The user currently has this live weather snapshot open in the "
                f"app, use it if relevant to their question:\n"
                f"{json.dumps(weather_context.to_dict(), indent=2)}\n\n"
            )
        else:
            context_note = (
                "No city is currently loaded in the app for this user.\n\n"
            )
        user = f"{context_note}User question: {message}"
        return system, user

    # ---------------------------------------------------------------
    # 4. Suggested follow-up prompts (used to seed the chat UI)
    # ---------------------------------------------------------------
    @staticmethod
    def suggested_prompts(weather: WeatherData | None) -> PromptPair:
        system = (
            "You generate short, tappable suggested-question chips for a "
            "weather-assistant chat UI. Respond with ONLY a valid JSON array "
            "of 4 short strings (max 8 words each), no markdown fences, no "
            "commentary."
        )
        if weather is not None:
            user = (
                "The user currently has this city loaded:\n"
                f"{json.dumps(weather.to_dict(), indent=2)}\n\n"
                "Suggest 4 short, relevant questions they might ask next."
            )
        else:
            user = (
                "No city is loaded yet. Suggest 4 short, generic starter "
                "questions about weather, clothing, travel, or comparing cities."
            )
        return system, user
