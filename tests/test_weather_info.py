from weather_app.auxiliary import (get_location, get_location_by_coords,
                                   get_weather_info,convert_to_fahr)

class TestUtilityFunctions:
    WEATHER_INFO = get_weather_info(
        lat=6.4474, lon=3.3903,timezone="Africa/Lagos")
    
    LOCATION_BY_IP = get_location("102.93.9.182")

    LOCATION_BY_COORD = get_location_by_coords(lat=6.4474, lon=3.3903)


    def test_get_location(self):
        
        assert self.LOCATION_BY_IP == {
            "city": "Lagos",
            "country": "Nigeria",
            "lat": 6.4474,
            "lon": 3.3903,
            "timezone": "Africa/Lagos",
        }

    def test_get_location_by_coords(self):

        assert isinstance(self.LOCATION_BY_COORD, dict)
        assert self.LOCATION_BY_COORD['city'] == self.LOCATION_BY_IP['city']
        assert self.LOCATION_BY_COORD['country'] == self.LOCATION_BY_IP['country']

    def test_convert_to_fahr(self):
        temp_Cs = [-40, 0, 100]
        temp_Fs = [-40, 32, 212]

        for temp_C, temp_F in zip(temp_Cs, temp_Fs):
            assert convert_to_fahr(temp_C) == temp_F

    def test_weather_info(self):
            columns = self.WEATHER_INFO.columns
            assert set(columns) == {"temperature", "humidity", "wind_speed","cloud","symbol"}
            assert self.WEATHER_INFO.shape[0] > 0
            assert isinstance(self.WEATHER_INFO.index[0],object)
