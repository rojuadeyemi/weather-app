import pandas as pd
import requests
import datetime as dt
import requests_cache

from weather_app.plotting import get_graphs

# requests_cache configuration
FLUSH_PERIOD = 10 * 60  # 10 minutes in seconds
requests_cache.install_cache(expire_after=FLUSH_PERIOD)

def process_weather_forecast(ip_address: str) -> dict:
    """Gather weather and location-related information.

    Args:
        ip_address (str): An IPv4/IPv6 address, or a domain name.

    Returns:
        dict: Weather and location info.
    """
    
    # get location information such as latitude, longitude and timezone
    location = get_location(ip_address)

    # Using latitude, longitude and timezone, obtain the time-series data for the weather (a list of dictionaries)
    weather_info = get_weather_info(location["lat"], location["lon"], location["timezone"])
    
    # Using latitude, longitude and timezone, obtain the time-series data for only temperature (Pandas Series)
    temperature_ts = get_temperature_time_series(weather_info, timezone=location["timezone"])

    # Obtain the next 1hr, 6hr and 12hr of the weather data 
    forecast=get_forecast_detail(weather_info,location["timezone"])

    # Obtain the current hour temperature value and convert to Farrheit
    temp_C = weather_info[0]["data"]["instant"]["details"]['air_temperature']
    temp_F = convert_to_fahr(temp_C)

    # Obtain the current hour Humidity
    humidity = weather_info[0]["data"]["instant"]["details"]['relative_humidity']
    
    # Obtain the current hour Cloud fraction
    cloud_fraction = weather_info[0]["data"]["instant"]["details"]['cloud_area_fraction']

    # Obtain the current hour Cloud fraction
    wind_speed = weather_info[0]["data"]["instant"]["details"]['wind_speed']

    climatic_cond = climatic_condition(temp_C,humidity,cloud_fraction,wind_speed)
    
    return dict(
        graphs=get_graphs(temperature_ts),
        headline=(
            f"It's {temp_C :.0f}°C ({temp_F :.0f}°F) in {location['city']},"
            f" {location['country']} right now."
        ),
        climatic = climatic_cond+' • '+dt.datetime.now().strftime("%a %d, %I:%M %p"),
        forecast=forecast,
        ip_address=ip_address,
        weather_icons=get_weather_icons(weather_info[1]),
        )


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


def get_weather_info(lat: float, lon: float, timezone: str) -> list:
    """Get weather forecast data for a given location.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        timezone (str): Time zone information e.g. 'GMT'.

    Returns:
        dict: Weather forecast data in JSON.
    """
    return requests.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/complete",
        params={"lat": lat, "lon": lon},
        headers={"User-Agent": "Aderoju"},
    ).json()["properties"]["timeseries"]

def get_weather_icons(current_weather: dict) -> dict:
    """Fetch the appropriate icons to illustrate the weather for the next
    few hours.

    Args:
        current_weather (dict): Weather forecast for the current hour.

    Returns:
        dict: Weather forecast icons for the next 1, 6 and 12 hours.
    """
    return {
        f"{time}h": current_weather["data"][f"next_{time}_hours"]["summary"][
            "symbol_code"
        ]
        for time in [1, 6, 12]
    }


def get_temperature_time_series(
    weather_data: list, timezone: str
) -> pd.Series:
    """Get air temperature forecasts as a time-zone-aware pandas Series.

    Args:
        weather_data (list): Time series data with hourly weather forecasts.
        timezone (str): Time zone information e.g. 'GMT'.

    Returns:
        pandas.Series: Air temperature forecast time series data.
    """
    time_info = [entry["time"] for entry in weather_data]

    temp_info = [
        entry["data"]["instant"]["details"]["air_temperature"]
        for entry in weather_data
    ]

    temp_data = pd.Series(temp_info, index=time_info)

    # Make the index time-zone aware
    temp_data.index = pd.to_datetime(temp_data.index).tz_convert(timezone)

    return temp_data


def convert_to_fahr(temp_C: float) -> float:
    """Convert temperature from degrees Celcius/centigrade to Fahrenheit.

    Args:
        temp_C (float): Temperature in degrees Celcius/centigrade.

    Returns:
        float: Temperature in degrees Fahrenheit.
    """
    return 9 / 5 * temp_C + 32


def get_external_IP_address() -> str:
    """Get the client's IP address via a GET request to an API service.

    Returns:
        str: An IPv4 or IPv6 address.
    """
    return requests.get(
        "https://ident.me/", headers={"User-Agent": "Aderoju"}
    ).text

def get_forecast_detail(weather_data: list, timezone: str) -> dict:
    """Get climatic details forecasts as a time-zone-aware pandas DataFrame.

    Args:
        weather_data (list): Time series data with hourly weather forecasts.
        timezone (str): Time zone information e.g. 'GMT'.

    Returns:
        dict: climatic information forecast time series data.
    """
    # Extract the current hour data plus the next 12 hours hourly data
    weather_data = weather_data[:14]

    time_info = [entry["time"] for entry in weather_data]
    
    details = ('dew_point_temperature','wind_speed','relative_humidity',
               'cloud_area_fraction_medium','air_pressure_at_sea_level',"air_temperature")
        
    columns = ("dew_point","wind_speed","humidity","cloud_area","pressure","temperatue")

    climatic_info ={
            col:[entry["data"]["instant"]["details"][detail] for entry in weather_data] 
            for col, detail in zip(columns,details)}
    
    climatic_data = pd.DataFrame(climatic_info, index=time_info)

    # Make the index time-zone aware
    climatic_data.index = pd.to_datetime(climatic_data.index).tz_convert(timezone)
    
    return  {f"{time}h": {
        "Pressure": f"{climatic_data.loc[climatic_data.index[time+1],'pressure']}hPa",
        "Temperature": f"{climatic_data.loc[climatic_data.index[time+1],'temperatue']}°C",
        "Cloud": f"{climatic_data.loc[climatic_data.index[time+1],'cloud_area']}%",
        "Humidity": f"{climatic_data.loc[climatic_data.index[time+1],'humidity']}%",
        "Dew point": f"{climatic_data.loc[climatic_data.index[time+1],'dew_point']}°",
        "Wind": f"{round(climatic_data.loc[climatic_data.index[time+1],'wind_speed']*3.6,1)}km/h",
    } for time in [1, 6, 12]
    }

def climatic_condition(temperature:float,humidity:float, 
                       cloud_fraction:float,wind_speed:float) ->str:
    
    """Get climatic condition as a string.

    Args:
        temperature (float): Location temperature value.
        humidity (float): Location humidity value.
        cloud_fraction (float): Location cloud area fraction value.
        wind_speed (float): Location wind speed value.

    Returns:
        str: climatic condition of the input values.
    """

    if temperature < 25:
        if humidity > 80:
            if cloud_fraction > 75 and wind_speed >8:
                return "Heavy Rainfall"
            if 50 <= cloud_fraction <= 75 and wind_speed < 5:
                return "Light Rain"
            if cloud_fraction < 50 and wind_speed < 5:
                return "Cloudy"
        if humidity > 80 and wind_speed < 8:
            return "Light Rain"
        return "Cloudy"
    if temperature < 27:
        if humidity > 80 and wind_speed < 8:
            return "Light Rain"
        if 60 <= humidity <= 80 and cloud_fraction > 75 and 5 <= wind_speed <= 10:
            return "Rainy"
        if 60 <= humidity <= 80 and 50 <= cloud_fraction <= 75 and 5 <= wind_speed <= 10:
            return "Light Rain"
        if 60 <= humidity <= 80 and cloud_fraction < 50 and 5 <= wind_speed <= 10:
            return "Cloudy"
        
    if 25 <= temperature <= 30:
        if 40 <= humidity <= 60:
            if cloud_fraction > 75 and 10 <= wind_speed <= 20:
                return "Overcast"
            if cloud_fraction <= 75 and 10 <= wind_speed <= 20:
                return "Partly Cloudy"
            if cloud_fraction < 50 and 10 <= wind_speed <= 20:
                return "Clear Sky"
        if humidity < 40 and cloud_fraction == 0 and wind_speed > 20:
            return "Very Dry"
        if humidity > 80 and wind_speed < 8:
            return "Mostly Cloudy"
        if humidity < 80 and wind_speed < 8:
            return "Partly Sunny"
    if temperature > 30:
        if humidity < 40:
            if cloud_fraction > 75 and wind_speed > 20:
                return "Hot and Humid"
            if 50 <= cloud_fraction <= 75 and wind_speed > 20:
                return "Hot"
            if cloud_fraction < 50 and wind_speed > 20:
                return "Very Hot"
    if cloud_fraction > 75 and wind_speed > 20:
        return "Stormy"
    if wind_speed > 30 and temperature > 30:
        return "Intense Sun"

    return "Unknown"