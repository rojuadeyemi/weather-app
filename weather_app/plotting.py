import plotly.express as px
import plotly.io as pio
import json

def get_graphs(temp_ts) -> dict:

    return {
        "24h": plot_24hr_forecast(temp_ts),
        "10d": plot_10day_forecast(temp_ts),
    }


def plot_24hr_forecast(weather_data) -> dict:
    
    now = weather_data.index[1]
    from datetime import  timedelta

    temp24H = weather_data.loc[
        (weather_data.index > now) &
        (weather_data.index <= now + timedelta(hours=24)),
        "temperature"
    ]

    fig = px.line(
        y=temp24H,
        height=280,
        x=temp24H.index.strftime("%I %p").str.lstrip("0"),
        title="<b> 24 Hour Forecast </b>",
        line_shape='spline',
        text=temp24H.round(1)
    )

    configure_fig(fig, temp24H.min() - 1, temp24H.max() + 1, "", "Temperature (°C)")

    fig.update_traces(
        hovertemplate="<b>Time</b>: %{x}<br><b>Temp</b>: %{y}°C<br>",
        marker_size=4,
        line_smoothing=1,
        textposition='top center',
        line=dict(color="#2C3E50", width=2),
        textfont_size=10
    )

    return json.loads(pio.to_json(fig))

def plot_10day_forecast(weather_data) -> dict:
    temp10D = weather_data["temperature"].resample("1D").agg(["max", "min"])

    fig = px.bar(
        temp10D,
        barmode="group",
        color_discrete_sequence=["#ec3453", "#0099cc"],
        height=250,
        title="<b> 10 Day Forecast </b>",
        text_auto=True
    )

    configure_fig(fig, None, None, "Day", "Temp(°C)")

    fig.update_traces(textposition="outside",
        hovertemplate="<b>%{y}°C</b>",
        textfont_size=10
    )

    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

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
