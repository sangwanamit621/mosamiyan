from datetime import datetime
from typing import Tuple


def deg_to_cardinal(deg: float) -> str:
    """Convert wind direction in degrees to a 16-point compass cardinal direction."""
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    idx = int((deg + 11.25) / 22.5) % 16
    return directions[idx]


def wmo_code_to_condition(code: int) -> Tuple[str, str]:
    """
    Map WMO weather interpretation code to (Condition Description, Condition Code).
    """
    mapping = {
        0: ("Clear Sky", "clear_day"),
        1: ("Mainly Clear", "mainly_clear"),
        2: ("Partly Cloudy", "partly_cloudy"),
        3: ("Overcast", "overcast"),
        45: ("Fog", "fog"),
        48: ("Depositing Rime Fog", "fog"),
        51: ("Light Drizzle", "drizzle_light"),
        53: ("Moderate Drizzle", "drizzle_moderate"),
        55: ("Dense Drizzle", "drizzle_dense"),
        56: ("Light Freezing Drizzle", "freezing_drizzle"),
        57: ("Dense Freezing Drizzle", "freezing_drizzle"),
        61: ("Slight Rain", "rain_light"),
        62: ("Moderate Rain", "rain_moderate"),
        63: ("Moderate Rain", "rain_moderate"),
        65: ("Heavy Rain", "rain_heavy"),
        66: ("Light Freezing Rain", "freezing_rain"),
        67: ("Heavy Freezing Rain", "freezing_rain"),
        71: ("Slight Snow", "snow_light"),
        73: ("Moderate Snow", "snow_moderate"),
        75: ("Heavy Snow", "snow_heavy"),
        77: ("Snow Grains", "snow_grains"),
        80: ("Slight Rain Showers", "rain_showers"),
        81: ("Moderate Rain Showers", "rain_showers"),
        82: ("Violent Rain Showers", "rain_heavy"),
        85: ("Slight Snow Showers", "snow_showers"),
        86: ("Heavy Snow Showers", "snow_showers"),
        95: ("Thunderstorm", "thunderstorm"),
        96: ("Thunderstorm with Slight Hail", "thunderstorm_hail"),
        99: ("Thunderstorm with Heavy Hail", "thunderstorm_hail")
    }
    return mapping.get(code, ("Unknown", "cloudy"))


def uv_to_category(uv: float) -> str:
    """Categorize UV index according to WHO standards."""
    if uv < 3.0:
        return "Low"
    elif uv < 6.0:
        return "Moderate"
    elif uv < 8.0:
        return "High"
    elif uv < 11.0:
        return "Very High"
    else:
        return "Extreme"


def aqi_to_category(aqi: int) -> str:
    """Categorize US AQI value."""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


def compute_lifestyle_indices(
    temp_c: float,
    humidity: float,
    wind_kmh: float,
    precip_prob: int,
    uv_index: float,
    is_rain_in_12h: bool = False
) -> dict:
    """Compute outdoor running, car wash, and sun protection indices."""
    # Outdoor Running Score
    score = 100.0
    if temp_c < 10.0:
        score -= (10.0 - temp_c) * 2.5
    elif temp_c > 18.0:
        score -= (temp_c - 18.0) * 3.5

    if temp_c > 22.0 and humidity > 70:
        score -= (humidity - 70) * 0.4

    if wind_kmh > 20.0:
        score -= (wind_kmh - 20.0) * 1.2

    score -= (precip_prob * 0.35)
    final_score = int(max(0, min(100, round(score))))

    if final_score >= 80:
        running_rating = "Optimal"
        running_summary = "Great running weather. Comfortable temperatures and dry conditions."
    elif final_score >= 60:
        running_rating = "Good"
        running_summary = "Good running conditions with mild conditions."
    elif final_score >= 40:
        running_rating = "Fair"
        running_summary = "Passable conditions; prepare for breeze or humidity."
    else:
        running_rating = "Poor"
        running_summary = "Less favorable conditions for outdoor runs."

    # Car Wash
    if is_rain_in_12h or precip_prob > 40:
        car_wash_rating = "Poor"
        car_wash_summary = "Rain expected soon. Not recommended to wash your vehicle."
    elif precip_prob > 20:
        car_wash_rating = "Fair"
        car_wash_summary = "Possible light precipitation in forecast."
    else:
        car_wash_rating = "Great"
        car_wash_summary = "Clear dry skies ahead. Perfect day for a car wash!"

    # Sun Protection
    if uv_index >= 8:
        burn_mins = 15
        sun_rec = "Very High UV! Wear SPF 50+, hat, and sunglasses."
    elif uv_index >= 6:
        burn_mins = 25
        sun_rec = "High UV. Apply SPF 30+ sunscreen and seek midday shade."
    elif uv_index >= 3:
        burn_mins = 45
        sun_rec = "Moderate UV. SPF 15-30 recommended around midday."
    else:
        burn_mins = 90
        sun_rec = "Low UV. Minimal protection required."

    return {
        "outdoor_running": {
            "score": final_score,
            "rating": running_rating,
            "summary": running_summary
        },
        "car_wash": {
            "rating": car_wash_rating,
            "summary": car_wash_summary
        },
        "sun_protection": {
            "time_to_burn_mins": burn_mins,
            "recommendation": sun_rec
        }
    }
