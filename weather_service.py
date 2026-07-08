"""
weather_service.py
-------------------
All communication with the external weather provider (OpenWeatherMap) lives
here, completely isolated from the AI logic and from Flask. Callers get back
a plain, typed `WeatherData` object regardless of the underlying provider's
JSON shape, which keeps the rest of the app decoupled from that provider.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------


class WeatherServiceError(Exception):
    """Base class for all weather-service failures."""


class InvalidCityInputError(WeatherServiceError):
    """Raised when the supplied city name fails validation."""


class CityNotFoundError(WeatherServiceError):
    """Raised when the weather provider has no data for the given city."""


class WeatherAPIError(WeatherServiceError):
    """Raised when the weather provider returns an unexpected error."""


class WeatherAPITimeoutError(WeatherServiceError):
    """Raised when the request to the weather provider times out."""


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

# Only letters (incl. accented), spaces, hyphens, apostrophes and commas
# (for "City, Country Code" style queries) are allowed as input.
_CITY_NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-',.]{1,100}$")


@dataclass(frozen=True)
class WeatherData:
    """Normalized, provider-agnostic weather snapshot for a single city."""

    city: str
    country: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: float
    temp_min_c: float
    temp_max_c: float
    humidity_pct: int
    pressure_hpa: int
    wind_speed_ms: float
    wind_direction_deg: int
    visibility_m: int
    cloudiness_pct: int
    condition_main: str
    condition_description: str
    condition_icon: str
    sunrise: str
    sunset: str
    observed_at: str
    units: str = "metric"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------
# Service
# --------------------------------------------------------------------------


class WeatherService:
    """Thin, typed client around the OpenWeatherMap current-weather endpoint."""

    def __init__(self, api_key: str, base_url: str, units: str = "metric", timeout: int = 8) -> None:
        if not api_key:
            raise WeatherAPIError("Weather API key is missing.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._units = units
        self._timeout = timeout

    # -- public API -------------------------------------------------------

    def get_current_weather(self, city: str) -> WeatherData:
        """Fetch and normalize current weather for a single city name."""
        clean_city = self._validate_city(city)

        response = self._request(
            "/weather",
            params={"q": clean_city, "appid": self._api_key, "units": self._units},
        )
        return self._parse_current(response)

    def get_current_weather_many(self, cities: List[str]) -> List[WeatherData]:
        """Fetch weather for several cities, stopping at the first hard failure."""
        return [self.get_current_weather(city) for city in cities]

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _validate_city(city: str) -> str:
        if not isinstance(city, str):
            raise InvalidCityInputError("City name must be text.")
        clean = city.strip()
        if not clean:
            raise InvalidCityInputError("City name cannot be empty.")
        if not _CITY_NAME_PATTERN.match(clean):
            raise InvalidCityInputError(
                "City name contains invalid characters. Use letters, spaces, "
                "hyphens, apostrophes, or 'City, Country' format only."
            )
        return clean

    def _request(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            resp = requests.get(url, params=params, timeout=self._timeout)
        except requests.exceptions.Timeout as exc:
            raise WeatherAPITimeoutError("The weather service took too long to respond.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise WeatherAPIError("Could not connect to the weather service.") from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAPIError(f"Weather service request failed: {exc}") from exc

        if resp.status_code == 404:
            raise CityNotFoundError(f"No weather data found for that city.")
        if resp.status_code == 401:
            raise WeatherAPIError("Weather API key was rejected by the provider (401).")
        if resp.status_code == 429:
            raise WeatherAPIError("Weather API rate limit exceeded. Try again shortly.")
        if not resp.ok:
            raise WeatherAPIError(f"Weather service returned HTTP {resp.status_code}.")

        try:
            return resp.json()
        except ValueError as exc:
            raise WeatherAPIError("Weather service returned an invalid response.") from exc

    def _parse_current(self, payload: Dict[str, Any]) -> WeatherData:
        try:
            main: Dict[str, Any] = payload["main"]
            wind: Dict[str, Any] = payload.get("wind", {})
            sys_: Dict[str, Any] = payload.get("sys", {})
            weather_list: List[Dict[str, Any]] = payload.get("weather", [])
            condition = weather_list[0] if weather_list else {}
            coord: Dict[str, Any] = payload.get("coord", {})

            return WeatherData(
                city=payload.get("name", "Unknown"),
                country=sys_.get("country", "—"),
                latitude=float(coord.get("lat", 0.0)),
                longitude=float(coord.get("lon", 0.0)),
                temperature_c=float(main["temp"]),
                feels_like_c=float(main.get("feels_like", main["temp"])),
                temp_min_c=float(main.get("temp_min", main["temp"])),
                temp_max_c=float(main.get("temp_max", main["temp"])),
                humidity_pct=int(main.get("humidity", 0)),
                pressure_hpa=int(main.get("pressure", 0)),
                wind_speed_ms=float(wind.get("speed", 0.0)),
                wind_direction_deg=int(wind.get("deg", 0)),
                visibility_m=int(payload.get("visibility", 0)),
                cloudiness_pct=int(payload.get("clouds", {}).get("all", 0)),
                condition_main=condition.get("main", "Unknown"),
                condition_description=condition.get("description", "unknown"),
                condition_icon=condition.get("icon", "01d"),
                sunrise=self._epoch_to_iso(sys_.get("sunrise")),
                sunset=self._epoch_to_iso(sys_.get("sunset")),
                observed_at=datetime.now(timezone.utc).isoformat(),
                units=self._units,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherAPIError("Unexpected response shape from weather provider.") from exc

    @staticmethod
    def _epoch_to_iso(epoch: Optional[int]) -> str:
        if not epoch:
            return "—"
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
