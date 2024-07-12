from ipaddress import ip_address
from pathlib import Path
import pandas as pd


from weather_app.weather_info import (
    convert_to_fahr,
    get_forecast_detail,
    get_external_IP_address,
    get_location,
    get_temperature_time_series,
    get_weather_icons,
    get_weather_info,
)


class TestUtilityFunctions:
    def test_get_location(self):
        
        location = get_location("8.8.8.8")
        
        assert location == {
            "city": "Ashburn",
            "country": "United States",
            "lat": 39.03,
            "lon": -77.5,
            "timezone": "America/New_York",
        }

    def test_get_external_IP(self):
        ext_ip_address = get_external_IP_address()
        assert isinstance(ext_ip_address, str)
        assert ip_address(ext_ip_address).version == 4

    def test_convert_to_fahr(self):
        temp_Cs = [-40, 0, 100]
        temp_Fs = [-40, 32, 212]

        for temp_C, temp_F in zip(temp_Cs, temp_Fs):
            assert convert_to_fahr(temp_C) == temp_F


class TestWeatherFunctions:

    weather_info = get_weather_info(
        lat=39.03, lon=-77.5, timezone="America/New_York"
    )

    def test_weather_info(self):
        for hour_data in self.weather_info:
            assert set(hour_data.keys()) == {"time", "data"}
            assert set(self.weather_info[0]["data"].keys()) == {
            "instant",
            "next_12_hours",
            "next_1_hours",
            "next_6_hours",
        }

    def test_get_forecast_detail(self):

        weather_info = self.weather_info[:14]
        time_info = [entry["time"] for entry in weather_info]

        details = ('dew_point_temperature','wind_speed','relative_humidity',
               'cloud_area_fraction_medium','air_pressure_at_sea_level',"air_temperature")
        columns = ("dew_point","wind_speed","humidity","cloud_area","pressure","temperatue")

        climatic_info ={
            col:[entry["data"]["instant"]["details"][detail] for entry in weather_info] 
            for col, detail in zip(columns,details)}

        climatic_data = pd.DataFrame(climatic_info, index=time_info)

        climatic_data.index = pd.to_datetime(climatic_data.index).tz_convert("America/New_York")

        metrics = get_forecast_detail(self.weather_info,timezone="America/New_York")
        
        assert metrics == {f"{time}h": {
        "Pressure": f"{climatic_data.loc[climatic_data.index[time+1],'pressure']}hPa",
        "Temperature": f"{climatic_data.loc[climatic_data.index[time+1],'temperatue']}°C",
        "Cloud": f"{climatic_data.loc[climatic_data.index[time+1],'cloud_area']}%",
        "Humidity": f"{climatic_data.loc[climatic_data.index[time+1],'humidity']}%",
        "Dew point": f"{climatic_data.loc[climatic_data.index[time+1],'dew_point']}°",
        "Wind": f"{round(climatic_data.loc[climatic_data.index[time+1],'wind_speed']*3.6,1)}km/h",
    } for time in [1, 6, 12]
    }

    def test_get_icons(self):
        icon_dir = Path("weather_app/static/weather-icons")
        icon_list = [file.stem for file in icon_dir.iterdir()]

        icon_dict = get_weather_icons(self.weather_info[0])

        for timepoint in {"1h", "6h", "12h"}:
            assert icon_dict[timepoint] in icon_list

    def test_get_temperature_time_series(self):
        data = get_temperature_time_series(
            weather_data=self.weather_info, timezone="America/New_York"
        )
        assert isinstance(data, pd.Series)
        assert data.index.tz.zone == "America/New_York"
