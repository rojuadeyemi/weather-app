
def process_weather_forecast(lat=None, lon=None):

    from weather_app.auxiliary import get_location_by_coords, get_weather_info,convert_to_fahr
    location = get_location_by_coords(lat, lon)
    
    weather_data = get_weather_info(location["lat"], location["lon"])

    current = weather_data.iloc[1]
    symbol = current["symbol"] or "clearsky_day"
    temp_c = current["temperature"]
    temp_F = convert_to_fahr(temp_c)
    forecast, icons = build_forecast(weather_data)

    from weather_app.plotting import get_graphs

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

def build_forecast(weather):
    now = weather.index[1]

    from datetime import timedelta
    targets = {
        "1h": now + timedelta(hours=1),
        "3h": now + timedelta(hours=3),
        "6h": now + timedelta(hours=6),
    }

    result = {}
    symbol = {}

    for label, target_time in targets.items():

        # temperature window
        window = weather[(weather.index > now) & (weather.index <= target_time)]

        if window.empty:
            continue

        row = window.iloc[-1]

        # SYMBOL shifted back by 1 hour
        symbol_time = target_time - timedelta(hours=1)

        past_window = weather[weather.index <= symbol_time]

        if not past_window.empty:
            symbol_row = past_window.iloc[-1]
            symbol[label] = symbol_row.get("symbol", None)
        else:
            symbol[label] = row.get('symbol', None)

        result[label] = {
            "Temperature": f"{row['temperature']}°C",
            "Humidity": f"{row['humidity']}%",
            "Wind": f"{round(row['wind_speed'] * 3.6, 1)} km/h",
            "Cloud Cover": f"{row['cloud']}%"
        }

    return result, symbol
