import plotly.express as px
from pandas import Series
import plotly.io as pio
import json


def get_graphs(temp_ts: Series) -> dict:
    """Plot graphs using the temperature forecast data.

    Args:
        temp_ts (Series): Air temperature time series data.

    Returns:
        dict: A 24h forecast line plot and 10d forecast bar plot as JSON objects.
    """
    return {
        "24h": plot_24hr_forecast(temp_ts),
        "10d": plot_10day_forecast(temp_ts),
    }


def plot_24hr_forecast(temp_ts: Series) -> dict:
    """Get a graph of the air temperature over the next 24 hours.

    Args:
        temp_ts (Series): Air temperature time series data.

    Returns:
        dict: A line graph of the 24hr air temperature forecast as a JSON object.
    """
    temp24H = temp_ts.iloc[2:26]
    fig = px.line(
        y=temp24H,
        height=280,
        x=temp24H.index.strftime("%#I %p"),
        title="<b> 24 Hour Forecast </b>",
        line_shape='spline',
        text=round(temp24H, 0)
    )

    configure_fig(fig, temp24H.min() - 0.5, temp24H.max() + 0.5, "Time", "Temperature (°C)")

    fig.update_traces(
        hovertemplate="<b>Time</b>: %{x}<br><b>Temp</b>: %{y}°C<br>",
        marker_size=4,
        line_smoothing=1,
        textposition='top center',
        line=dict(color="#2C3E50", width=2)
    )

    return json.loads(pio.to_json(fig))


def plot_10day_forecast(temp_ts: Series) -> dict:
    """Get a bar graph of the maximum and minimum temperature over the next 10 days.

    Args:
        temp_ts (Series): Air temperature time series data.

    Returns:
        dict: A bar graph of the 10-day max & min temperature forecast as a JSON object.
    """
    temp10D = temp_ts.resample("1D").agg(["max", "min"])
    fig = px.bar(
        temp10D,
        barmode="group",
        color_discrete_sequence=["#ec3453", "#0099cc"],
        height=250,
        title="<b> 10 Day Forecast </b>"
    )

    configure_fig(fig, None, None, "Day", "Temperature (°C)")

    fig.update_traces(hovertemplate="<b>%{y}°C</b>")

    return json.loads(pio.to_json(fig))


def configure_fig(fig, y_min=None, y_max=None, x_title="", y_title=""):
    """Apply common configuration to a Plotly figure.

    Args:
        fig (Figure): The Plotly figure to configure.
        y_min (float, optional): Minimum value for the y-axis. Defaults to None.
        y_max (float, optional): Maximum value for the y-axis. Defaults to None.
        x_title (str, optional): Title for the x-axis. Defaults to "".
        y_title (str, optional): Title for the y-axis. Defaults to "".
    """
    fig.update_xaxes(title_text=f"<b>{x_title}</b>", fixedrange=True, showgrid=False)
    fig.update_yaxes(title_text=y_title, fixedrange=True, range=[y_min, y_max] if y_min is not None and y_max is not None else None)
    
    fig.update_layout(
        paper_bgcolor="#F9F9F9",
        plot_bgcolor="#F9F9F9",
        font=dict(color='#000000'),
        xaxis=dict(showgrid=True, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridcolor='lightgray'),
        margin=dict(l=30, t=30, r=10, b=10),
        font_family="serif",
        hovermode="x unified",
        legend_title_text=y_title
    )
