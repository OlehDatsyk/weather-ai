"""
app.py
------
Flask application entry point. This module only wires HTTP routes to the
domain services (`WeatherService`, `AIService`) — it contains no weather
parsing logic and no prompt text of its own. Run with:

    python app.py

or, for production, via gunicorn (see README.md).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request

from ai_service import AIService, AIServiceError, ChatMessage, build_provider
from config import ConfigError, config
from weather_service import (
    CityNotFoundError,
    InvalidCityInputError,
    WeatherAPIError,
    WeatherAPITimeoutError,
    WeatherData,
    WeatherService,
)

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("weather-ai")


def create_app() -> Flask:
    """Application factory: builds and configures the Flask app."""
    flask_app = Flask(__name__)
    flask_app.config["JSON_SORT_KEYS"] = False
    flask_app.secret_key = config.SECRET_KEY or "dev-only-insecure-key"

    problems = config.validate()
    if problems:
        for problem in problems:
            logger.warning("Configuration issue: %s", problem)

    # Services are created once and reused across requests. They are
    # stateless and therefore safe to share.
    weather_service = WeatherService(
        api_key=config.WEATHER_API_KEY,
        base_url=config.WEATHER_API_BASE_URL,
        units=config.WEATHER_UNITS,
    )

    ai_service: Optional[AIService] = None
    ai_init_error: Optional[str] = None
    try:
        provider = build_provider(
            config.AI_PROVIDER,
            openai_api_key=config.OPENAI_API_KEY,
            openai_model=config.OPENAI_MODEL,
            anthropic_api_key=config.ANTHROPIC_API_KEY,
            anthropic_model=config.ANTHROPIC_MODEL,
        )
        ai_service = AIService(
            provider,
            temperature=config.AI_TEMPERATURE,
            max_tokens=config.AI_MAX_TOKENS,
        )
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, don't crash boot
        ai_init_error = str(exc)
        logger.warning("AI service could not be initialized: %s", exc)

    # ----------------------------------------------------------------
    # Pages
    # ----------------------------------------------------------------

    @flask_app.route("/")
    def index() -> str:
        return render_template("index.html", ai_provider=config.AI_PROVIDER)

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _require_ai() -> AIService:
        if ai_service is None:
            raise AIServiceError(
                ai_init_error or "AI service is not configured. Check your API key."
            )
        return ai_service

    def _json_body() -> Dict[str, Any]:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise InvalidCityInputError("Request body must be a JSON object.")
        return data

    def _weather_dict(weather: WeatherData) -> Dict[str, Any]:
        return weather.to_dict()

    def _validate_history(raw_history: Any) -> List[ChatMessage]:
        if raw_history is None:
            return []
        if not isinstance(raw_history, list):
            raise InvalidCityInputError("history must be a list.")
        cleaned: List[ChatMessage] = []
        for item in raw_history[-config.MAX_HISTORY_MESSAGES :]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                cleaned.append({"role": role, "content": content.strip()[:4000]})
        return cleaned

    # ----------------------------------------------------------------
    # API: current weather + full AI insight bundle
    # ----------------------------------------------------------------

    @flask_app.post("/api/weather")
    def api_weather():
        body = _json_body()
        city = body.get("city", "")
        weather = weather_service.get_current_weather(city)

        insights = None
        insights_error = None
        try:
            insights = _require_ai().get_weather_insights(weather)
        except AIServiceError as exc:
            insights_error = str(exc)
            logger.warning("AI insights failed for %s: %s", city, exc)

        return jsonify(
            {
                "weather": _weather_dict(weather),
                "insights": insights,
                "insights_error": insights_error,
            }
        )

    # ----------------------------------------------------------------
    # API: compare multiple cities
    # ----------------------------------------------------------------

    @flask_app.post("/api/compare")
    def api_compare():
        body = _json_body()
        cities = body.get("cities", [])
        if not isinstance(cities, list) or len(cities) < 2:
            raise InvalidCityInputError("Provide at least two city names to compare.")
        if len(cities) > config.MAX_CITIES_COMPARE:
            raise InvalidCityInputError(
                f"You can compare at most {config.MAX_CITIES_COMPARE} cities at once."
            )

        weather_list = [weather_service.get_current_weather(c) for c in cities]
        comparison = _require_ai().compare_cities(weather_list)

        return jsonify(
            {
                "cities": [_weather_dict(w) for w in weather_list],
                "comparison": comparison,
            }
        )

    # ----------------------------------------------------------------
    # API: open-ended chat
    # ----------------------------------------------------------------

    @flask_app.post("/api/chat")
    def api_chat():
        body = _json_body()
        message = body.get("message", "")
        if not isinstance(message, str) or not message.strip():
            raise InvalidCityInputError("message must be a non-empty string.")
        if len(message) > 1000:
            raise InvalidCityInputError("message is too long (max 1000 characters).")

        history = _validate_history(body.get("history"))

        weather_context: Optional[WeatherData] = None
        context_city = body.get("context_city")
        if isinstance(context_city, str) and context_city.strip():
            try:
                weather_context = weather_service.get_current_weather(context_city)
            except WeatherServiceErrorTuple:
                weather_context = None  # non-fatal: chat still works without context

        reply = _require_ai().chat(message.strip(), history, weather_context)
        return jsonify({"reply": reply})

    # ----------------------------------------------------------------
    # API: suggested prompt chips
    # ----------------------------------------------------------------

    @flask_app.post("/api/suggestions")
    def api_suggestions():
        body = _json_body()
        weather_context: Optional[WeatherData] = None
        context_city = body.get("context_city")
        if isinstance(context_city, str) and context_city.strip():
            try:
                weather_context = weather_service.get_current_weather(context_city)
            except WeatherServiceErrorTuple:
                weather_context = None

        prompts = _require_ai().suggested_prompts(weather_context)
        return jsonify({"suggestions": prompts})

    # ----------------------------------------------------------------
    # Error handling
    # ----------------------------------------------------------------

    @flask_app.errorhandler(InvalidCityInputError)
    def handle_invalid_input(exc: InvalidCityInputError):
        return jsonify({"error": str(exc), "type": "invalid_input"}), 400

    @flask_app.errorhandler(CityNotFoundError)
    def handle_city_not_found(exc: CityNotFoundError):
        return jsonify({"error": str(exc), "type": "city_not_found"}), 404

    @flask_app.errorhandler(WeatherAPITimeoutError)
    def handle_weather_timeout(exc: WeatherAPITimeoutError):
        return jsonify({"error": str(exc), "type": "weather_timeout"}), 504

    @flask_app.errorhandler(WeatherAPIError)
    def handle_weather_error(exc: WeatherAPIError):
        logger.error("Weather API error: %s", exc)
        return jsonify({"error": str(exc), "type": "weather_error"}), 502

    @flask_app.errorhandler(AIServiceError)
    def handle_ai_error(exc: AIServiceError):
        logger.error("AI service error: %s", exc)
        return jsonify({"error": str(exc), "type": "ai_error"}), 502

    @flask_app.errorhandler(404)
    def handle_404(_exc):
        return jsonify({"error": "Not found.", "type": "not_found"}), 404

    @flask_app.errorhandler(500)
    def handle_500(exc):
        logger.exception("Unhandled server error: %s", exc)
        return jsonify({"error": "Internal server error.", "type": "server_error"}), 500

    return flask_app


# A tuple of the weather exceptions that are safe to swallow when weather
# context is merely "nice to have" (e.g. for chat grounding), not required.
WeatherServiceErrorTuple = (
    InvalidCityInputError,
    CityNotFoundError,
    WeatherAPIError,
    WeatherAPITimeoutError,
)


app = create_app()


if __name__ == "__main__":
    try:
        config.require_valid()
    except ConfigError as exc:
        logger.warning("%s", exc)
        logger.warning("Starting anyway in case only optional keys are missing...")

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
