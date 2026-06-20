import os
import time
import httpx

import logging
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

OWM_API_KEY = os.getenv("OWM_API_KEY", "")
# Hyderabad coordinates
LAT = 17.3850
LON = 78.4867
CACHE_DURATION = 900  # 15 minutes in seconds

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0

    async def get_live_weather(self) -> Tuple[str, float]:
        """
        Returns a tuple: (weather_condition, prob_rain)
        weather_condition: 'sunny', 'rain', 'cloudy'
        prob_rain: 0.0 to 1.0
        """
        # Check cache
        if (
            time.time() - self._cache_time < CACHE_DURATION
            and "condition" in self._cache
        ):
            return self._cache["condition"], self._cache["prob_rain"]

        try:
            weather_base = os.getenv("WEATHER_API_BASE", "https://api.open-meteo.com")
            url = f"{weather_base}/v1/forecast?latitude={LAT}&longitude={LON}&current=precipitation,weather_code&timezone=Asia/Kolkata"
            timeout_sec = float(os.getenv("WEATHER_TIMEOUT_SEC", 5.0))
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout_sec)
                response.raise_for_status()
                data = response.json()

                current = data.get("current", {})
                weather_code = current.get("weather_code", 0)
                precipitation = current.get("precipitation", 0.0)

                # WMO Weather interpretation codes
                # 0: Clear sky
                # 1, 2, 3: Mainly clear, partly cloudy, and overcast
                # 51, 53, 55: Drizzle
                # 61, 63, 65: Rain
                # 80, 81, 82: Rain showers
                # 95, 96, 99: Thunderstorm

                if weather_code == 0:
                    condition = "sunny"
                    prob_rain = 0.05
                elif 1 <= weather_code <= 3 or 45 <= weather_code <= 48:
                    condition = "cloudy"
                    prob_rain = 0.2
                else:
                    condition = "rain"
                    # If it's actively raining, probability is high
                    prob_rain = 0.8
                    if precipitation > 2.0:
                        prob_rain = 0.95

                # Update cache
                self._cache["condition"] = condition
                self._cache["prob_rain"] = prob_rain
                self._cache_time = time.time()

                return condition, prob_rain

        except Exception as e:
            logger.error(f"Failed to fetch live weather from Open-Meteo: {e}")
            # Fallback on failure and cache it so we don't spam the API
            self._cache["condition"] = "sunny"
            self._cache["prob_rain"] = 0.1
            self._cache_time = time.time()
            return "sunny", 0.1


weather_service = WeatherService()
