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
    temp_C = temp_data[0]
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
    temp_data = pd.Series(temps, index=times)
    temp_data.index = (pd.to_datetime(temp_data.index)
                         .tz_convert(timezone))
    return temp_data


def plot_forecast(data):
    """
    Plot line graph of 24hr forecast, and bar graph of 10-day max & min.
    """
    temp24 = data[:24]
    temp24H_graph = StringIO()
    fig = px.line(y=temp24, x=temp24.index,
                  title="24 Hour Forecast", width=1200, height=900)
    
    fig.update_xaxes(title_text='Date',fixedrange=True, gridcolor="#ccc")
    fig.update_yaxes(title_text="Air temperature in °C",
        fixedrange=True,
        gridcolor="#ccc",
    )
    fig.update_layout(
        font_family="serif",
        paper_bgcolor="#ffffcc",
        plot_bgcolor="#ffffcc",
        margin=dict(l=50, t=50, r=10, b=10),
    )
    fig.update_traces(
        hovertemplate="<b>Time</b>: %{x}<br><b>Temp</b>: %{y}°C<br>",
        marker_size=4,
    )
    fig.write_html(temp24H_graph, include_plotlyjs='cdn',
                   full_html=False)

    temp10D = data.resample('1D').agg(['max', 'min'])
    temp10D_graph = StringIO()
    fig2 = px.bar(temp10D,
                  barmode='group', title="10 Day Forecast", width=1200,
                  height=900,
                  text_auto=True)
    fig2.update_xaxes(title_text='Date')
    fig2.update_yaxes(fixedrange=True,
        showgrid=True,
        gridcolor="#ccc",
        title="Air temperature in °C")
    fig2.update_layout(
        font_family="serif",
        hovermode="x unified",
        paper_bgcolor="#ffffcc",
        plot_bgcolor="#ffffcc",
        margin=dict(l=50, t=50, r=10, b=10),
    )
    fig2.update_traces(hovertemplate="<b>%{y}°C</b>")
    # Write graph to text buffer
    fig2.write_html(temp10D_graph, include_plotlyjs='cdn',
                    full_html=False)
    return temp24H_graph, temp10D_graph


def convert_to_fahr(temp_C):
    """Convert degrees to Celsius to Fahrenheit."""
    return 9 / 5 * temp_C + 32


def get_local_IP_address():
    return requests.get("https://ident.me/", headers={"User-Agent": "Aderoju"}).text


if __name__ == '__main__':
    import sys

    print(greet(sys.argv[1]))
