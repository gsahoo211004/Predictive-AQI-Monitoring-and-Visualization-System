import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

# AQI level descriptions
AQI_LEVELS = {
    1: {"label": "Good",        "color": "#00E400", "advice": "Air quality is satisfactory. Enjoy outdoor activities."},
    2: {"label": "Fair",        "color": "#FFFF00", "advice": "Acceptable air quality. Sensitive individuals should limit prolonged outdoor exposure."},
    3: {"label": "Moderate",    "color": "#FF7E00", "advice": "Members of sensitive groups may experience health effects. Limit outdoor activities."},
    4: {"label": "Poor",        "color": "#FF0000", "advice": "Everyone may begin to experience health effects. Avoid prolonged outdoor exertion."},
    5: {"label": "Very Poor",   "color": "#8F3F97", "advice": "Health warnings of emergency conditions. Everyone should avoid outdoor activity."},
}


def get_current_aqi(lat: float, lon: float) -> dict:
    """
    Fetch current AQI and pollutant data for given coordinates.
    """
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        aqi = data["list"][0]["main"]["aqi"]
        components = data["list"][0]["components"]
        timestamp = data["list"][0]["dt"]

        return {
            "aqi": aqi,
            "aqi_label": AQI_LEVELS[aqi]["label"],
            "aqi_color": AQI_LEVELS[aqi]["color"],
            "advice": AQI_LEVELS[aqi]["advice"],
            "components": {
                "CO":   round(components.get("co", 0), 2),
                "NO":   round(components.get("no", 0), 2),
                "NO2":  round(components.get("no2", 0), 2),
                "O3":   round(components.get("o3", 0), 2),
                "SO2":  round(components.get("so2", 0), 2),
                "PM2.5": round(components.get("pm2_5", 0), 2),
                "PM10": round(components.get("pm10", 0), 2),
                "NH3":  round(components.get("nh3", 0), 2),
            },
            "timestamp": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "lat": lat,
            "lon": lon,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_aqi_forecast(lat: float, lon: float) -> list:
    """
    Fetch AQI forecast data for the next 4 days.
    Returns a list of hourly AQI readings.
    """
    url = "http://api.openweathermap.org/data/2.5/air_pollution/forecast"
    params = {"lat": lat, "lon": lon, "appid": API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        forecast = []
        for item in data["list"]:
            forecast.append({
                "timestamp": datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d %H:%M"),
                "aqi": item["main"]["aqi"],
                "aqi_label": AQI_LEVELS[item["main"]["aqi"]]["label"],
                "pm2_5": item["components"].get("pm2_5", 0),
                "pm10":  item["components"].get("pm10", 0),
                "o3":    item["components"].get("o3", 0),
                "no2":   item["components"].get("no2", 0),
            })
        return forecast
    except Exception as e:
        return []


def get_location_name(lat: float, lon: float) -> str:
    """
    Reverse geocode coordinates to get a human-readable location name.
    """
    url = "http://api.openweathermap.org/geo/1.0/reverse"
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data:
            name = data[0].get("name", "")
            country = data[0].get("country", "")
            return f"{name}, {country}"
        return f"{lat:.2f}, {lon:.2f}"
    except:
        return f"{lat:.2f}, {lon:.2f}"


if __name__ == "__main__":
    # Test with Chennai coordinates
    print("Testing AQI fetch for Chennai...")
    result = get_current_aqi(13.0827, 80.2707)
    if result["status"] == "success":
        print(f"Location: Chennai")
        print(f"AQI: {result['aqi']} - {result['aqi_label']}")
        print(f"Advice: {result['advice']}")
        print(f"PM2.5: {result['components']['PM2.5']} µg/m³")
        print(f"Timestamp: {result['timestamp']}")
    else:
        print(f"Error: {result['message']}")