import requests
import requests_cache
from weather_app.plotting import get_graphs
from datetime import  timedelta
requests_cache.install_cache(expire_after=600)
import pandas as pd

WEATHER_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"


def process_weather_forecast(ip_address=None, lat=None, lon=None):
    """
    Lightweight weather processor (frontend handles time).
    """

    location = (
        get_location_by_coords(lat, lon)
        if lat is not None and lon is not None
        else get_location(ip_address or get_external_IP_address())
    )

    weather_data = get_weather_info(location["lat"], location["lon"])

    current = weather_data.iloc[1]
    symbol = current["symbol"] or "clearsky_day"
    temp_c = current["temperature"]
    temp_F = convert_to_fahr(temp_c)
    forecast, icons = build_forecast(weather_data)

    return {
        "graphs": get_graphs(weather_data),
        "headline": f"{temp_c:.0f}°C ({temp_F :.0f}°F) in {location['city']}, {location['country']}",
        "climatic": map_weather_condition(symbol),
        "symbol": symbol,
        "forecast": forecast,
        "weather_icons": icons,
    }

def map_weather_condition(symbol_code: str) -> str:
    """Convert API weather symbol code into human-readable condition."""

    mapping = {
        # Clear / fair
        "clearsky_day": "Clear Sky",
        "clearsky_night": "Clear Night",
        "fair_day": "Fair",
        "fair_night": "Fair",

        # Cloudy
        "partlycloudy_day": "Partly Cloudy",
        "partlycloudy_night": "Partly Cloudy",
        "cloudy": "Cloudy",

        # Rain
        "lightrain": "Light Rain",
        "lightrainshowers_day": "Light Rain Showers",
        "rain": "Rainy",
        "rainshowers_day": "Rain Showers",
        "heavyrain": "Heavy Rainfall",
        "heavyrainshowers_day": "Heavy Rain Showers",

        # Thunder
        "lightrainshowersandthunder_day": "Light Rain & Thunder",
        "rainandthunder": "Rain & Thunder",
        "heavyrainandthunder": "Heavy Rain & Thunder",

        # Snow
        "snow": "Snow",
        "heavysnow": "Heavy Snow",

        # Fog
        "fog": "Foggy",
    }

    # Remove suffix like "_day" / "_night" / "_polartwilight"
    base_code = symbol_code.replace("_polartwilight", "")

    return mapping.get(base_code, base_code.replace("_", " ").title())

def get_location_by_coords(lat, lon):
    response = requests.get(
        "http://ip-api.com/json/",
        params={"query": f"{lat},{lon}"}
    ).json()

    return {
        "city": response.get("city", "Unknown"),
        "country": response.get("country", "Unknown"),
        "lat": lat,
        "lon": lon,
        "timezone": response.get("timezone", "UTC"),
    }

def get_location(ip_address: str) -> dict:
    """Get city, country, latitude, longitude and timezone information for a
    location, based on IP address.

    Args:
        ip_address (str): An IPv4/IPv6 address, or a domain name.

    Returns:
        dict: Location details.
    """
    location_info = requests.get(
        f"http://ip-api.com/json/{ip_address}",
        headers={"User-Agent": "Aderoju"},
    ).json()

    return {
        key: location_info[key]
        for key in ("city", "country", "lat", "lon", "timezone")
    }


def get_weather_info(lat: float, lon: float):
    response = requests.get(
        WEATHER_URL,
        params={"lat": lat, "lon": lon},
        headers={"User-Agent": "Aderoju"},
    ).json()["properties"]["timeseries"]

    records = []

    for entry in response:
        details = entry["data"]["instant"]["details"]

        # safely get symbol_code
        symbol = (
            entry.get("data", {})
            .get("next_1_hours", {})
            .get("summary", {})
            .get("symbol_code")
        )

        records.append({
            "time": entry["time"],
            "temperature": details.get("air_temperature"),
            "humidity": details.get("relative_humidity"),
            "wind_speed": details.get("wind_speed"),
            "cloud": details.get("cloud_area_fraction"),
            "symbol": symbol
        })

    df = pd.DataFrame(records)

    # convert time
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")

    return df

def convert_to_fahr(temp_C: float) -> float:

    return 9 / 5 * temp_C + 32


def get_external_IP_address() -> str:

    return requests.get(
        "https://ident.me/", headers={"User-Agent": "Aderoju"}
    ).text

def build_forecast(weather):

    now = weather.index[1]

    targets = {
        "1h": now + timedelta(hours=1),
        "6h": now + timedelta(hours=6),
        "12h": now + timedelta(hours=12),
    }

    result = {}
    symbol = {}

    for label, target_time in targets.items():

        # get future rows only
        future = weather[(weather.index > now) & (weather.index <= target_time)]

        if not future.empty:
            row = future.iloc[-1]  # last future point

        symbol[label] = row.get('symbol')  # safer key

        result[label] = {
            "Temperature": f"{row['temperature']}°C",
            "Humidity": f"{row['humidity']}%",
            "Wind": f"{round(row['wind_speed'] * 3.6, 1)} km/h",
            "Cloud": f"{row['cloud']}%"
        }

    return result, symbol
