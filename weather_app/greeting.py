import requests
import requests_cache
import wikipedia
import pandas as pd
import plotly.express as px
from io import StringIO

FLUSH_PERIOD = 10 * 60  # 10 minutes in seconds
requests_cache.install_cache(expire_after=FLUSH_PERIOD)


def greet(ip_address):
    location_data = get_location(ip_address)
    temp_data = get_temperature(location_data['lat'],
                                location_data['lon'],
                                location_data['timezone'])
    temp_C = temp_data.iloc[0][0]
    temp_F = convert_to_fahr(temp_C)
    wiki_query = wikipedia.search(f"""{location_data['city']},
                                  {location_data['country']}""")[0]
    wiki_summary = wikipedia.summary(wiki_query)

    weather_info = {
        'graphs': plot_forecast(temp_data),
        'headline': f"""It's {temp_C :.0f} &degC ({temp_F :.0f} &degF) in
                    {location_data['city']}, {location_data['country']}
                    right now.""",
        'summary': wiki_summary,
        'ip_address': ip_address
    }
    return weather_info


def get_location(ip_address):
    """Return city, country, latitude, and longitude for a given IP address."""
    response = requests.get(f'http://ip-api.com/json/{ip_address}',
                            headers={'User-Agent': 'Aderoju'})
    data = response.json()
    keys = ('city', 'country', 'lat', 'lon', 'timezone')

    return {key: data[key] for key in keys}


def get_temperature(lat, lon, timezone):
    url_base = 'https://api.met.no/weatherapi/locationforecast/2.0/compact'

    response = requests.get(url_base, params={'lat': lat, 'lon': lon},headers={'User-Agent': 'Aderoju'})
    data = response.json()['properties']['timeseries']

    times = [entry['time'] for entry in data]
    temps = [entry['data']['instant']['details']['air_temperature']
             for entry in data]
    humid = [entry['data']['instant']['details']['relative_humidity']
             for entry in data]
    temp_data = pd.DataFrame({'temp':temps,'humid': humid}, index=times)
    temp_data.index = (pd.to_datetime(temp_data.index)
                         .tz_convert(timezone))
    return temp_data


def plot_forecast(data):
    """
    Plot line graph of 24hr forecast, and bar graph of 10-day max & min.
    """
    temp24H = data[1:25]
    temp24H_graph = StringIO()
    fig = px.area(data,y='temp', x=data.index,
                  title="24 Hour Forecast", width=1200, height=700,pattern_shape_sequence=["."])
    fig = px.area(data, y='humid', x=data.index,pattern_shape_sequence=["+"])
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Air temperature (C) and Humidity')

    fig.write_html(temp24H_graph, include_plotlyjs='cdn',
                   full_html=False)

    temp10D = data['temp'].resample('1D').agg(['max', 'min'])
    temp10D_graph = StringIO()
    fig2 = px.bar(temp10D,
                  barmode='group', title="10 Day Forecast", width=1200,
                  height=700,
                  text_auto=True,pattern_shape_sequence=[".", "+"])
    fig2.update_xaxes(title_text='Date')
    fig2.update_yaxes(title_text='Air temperature in deg C')
    fig2.write_html(temp10D_graph, include_plotlyjs='cdn',
                    full_html=False)
    return temp24H_graph, temp10D_graph


def convert_to_fahr(temp_C):
    """Convert degrees to Celsius to Fahrenheit."""
    return 9 / 5 * temp_C + 32


def get_local_IP_address():
    return requests.get('https://api.ipify.org').text


if __name__ == '__main__':
    import sys

    print(greet(sys.argv[1]))
