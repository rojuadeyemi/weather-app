import requests
import requests_cache
import pandas as pd
requests_cache.install_cache(expire_after=600)

def get_location(ip_address: str) -> dict:

    location_info = requests.get(
        f"http://ip-api.com/json/{ip_address}",
        headers={"User-Agent": "Aderoju"},
    timeout=5).json()

    return {
        key: location_info[key]
        for key in ("city", "country", "lat", "lon", "timezone")
    }

def get_location_by_coords(lat: float, lon: float) -> dict:
    res = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={
            "lat": lat,
            "lon": lon,
            "format": "json"
        },
        headers={"User-Agent": "weather-app"},timeout=5
    ).json()

    addr = res.get("address", {})

    response = requests.get(
            "http://ip-api.com/json/",
            params={"query": f"{lat},{lon}"}
        ,timeout=5).json()

    return {
        "city": (
            addr.get("name")
            or addr.get("suburb")
            or addr.get("county")
            or addr.get("state")
            or "Unknown"
        ),
        "country": addr.get("state", "Unknown"),
        "lat": lat,
        "lon": lon,
        "timezone": response.get("timezone", "UTC")
    }

def get_weather_info(lat: float, lon: float,timezone:str):
    response = requests.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/complete",
        params={"lat": lat, "lon": lon},
        headers={"User-Agent": "Aderoju"},timeout=5
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
    df = df.set_index("time")
    df.index = pd.to_datetime(df.index).tz_convert(timezone)

    return df

def convert_to_fahr(temp_C: float) -> float:

    return 9 / 5 * temp_C + 32
