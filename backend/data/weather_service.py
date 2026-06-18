import os
import time
import httpx
import asyncio
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
        weather_condition: 'sunny', 'rainy', 'cloudy'
        prob_rain: 0.0 to 1.0
        """
        # If no API key is set, use fallback logic immediately
        if not OWM_API_KEY:
            logger.warning("No OWM_API_KEY found, using mock weather data.")
            return "sunny", 0.1

        # Check cache
        if time.time() - self._cache_time < CACHE_DURATION and "condition" in self._cache:
            return self._cache["condition"], self._cache["prob_rain"]

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                response.raise_for_status()
                data = response.json()

                # Parse the weather condition
                weather_id = data["weather"][0]["id"]
                
                # OpenWeatherMap condition codes: https://openweathermap.org/weather-conditions
                # 2xx Thunderstorm, 3xx Drizzle, 5xx Rain
                if 200 <= weather_id <= 531:
                    condition = "rainy"
                    prob_rain = 0.8
                # 800 Clear
                elif weather_id == 800:
                    condition = "sunny"
                    prob_rain = 0.05
                # 801-804 Clouds
                elif 801 <= weather_id <= 804:
                    condition = "cloudy"
                    prob_rain = 0.2
                else:
                    # Fallback for mist, snow, etc.
                    condition = "cloudy"
                    prob_rain = 0.3

                # Update cache
                self._cache["condition"] = condition
                self._cache["prob_rain"] = prob_rain
                self._cache_time = time.time()

                return condition, prob_rain

        except Exception as e:
            logger.error(f"Failed to fetch live weather: {e}")
            # Fallback on failure
            return "sunny", 0.1

weather_service = WeatherService()
