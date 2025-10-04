"""
Weather service for OpenWeatherMap API integration
"""
import httpx
from typing import Dict, Any, Optional
from config import settings


async def fetch_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch weather data from OpenWeatherMap API"""
    if not settings.openweather_api_key:
        return generate_mock_weather_data(lat, lon)
    
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": settings.openweather_api_key,
            "units": "metric"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "temperature": round(data["main"]["temp"], 1),
                "humidity": data["main"]["humidity"],
                "wind_speed": round(data["wind"]["speed"], 1),
                "wind_direction": data["wind"].get("deg", 0),
                "pressure": data["main"]["pressure"],
                "visibility": round(data.get("visibility", 10000) / 1000, 1),  # Convert to km
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "data_source": "OpenWeatherMap API"
            }
            
    except Exception as e:
        print(f"Weather API error: {e}")
        return generate_mock_weather_data(lat, lon)


def generate_mock_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    """Generate realistic mock weather data"""
    import random
    from datetime import datetime, timezone
    
    # Seasonal temperature variation
    now = datetime.now(timezone.utc)
    month = now.month
    
    # Base temperature by latitude
    base_temp = 20 - (abs(lat) - 30) * 0.5  # Rough temperature gradient
    
    # Seasonal adjustment
    seasonal_temp = base_temp + 10 * (1 - abs(month - 6) / 6)  # Warmer in summer
    
    # Random variation
    temp = seasonal_temp + random.uniform(-5, 5)
    
    return {
        "temperature": round(temp, 1),
        "humidity": random.randint(30, 90),
        "wind_speed": round(random.uniform(0, 15), 1),
        "wind_direction": random.randint(0, 360),
        "pressure": random.randint(980, 1030),
        "visibility": round(random.uniform(5, 20), 1),
        "description": random.choice(["clear sky", "few clouds", "scattered clouds", "overcast clouds"]),
        "icon": "01d",
        "data_source": "Simulated Weather Data"
    }
