import pandas as pd
from scipy import signal
import plotly
import plotly.graph_objs as go
import datetime as dt
import plotly.io as pio
from app.config import config

pio.renderers.default = "browser"


def datetime_convert(x):
    """ Convert str to datetime format"""
    x = dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
    return x


def create_chart1():
    # Columns of the data that we want to plot
    features = []  # TODO

    # Time range to plot on hours
    time_range = config.TIME_RANGE_CHART_1

    # Import sensor data
    df = pd.read_csv(config.SENSOR_DATA_FILE, sep=";")

    # Give it the right format
    df['time_stamp'] = df['time_stamp'].apply(datetime_convert)

    df['minute'] = df['time_stamp'].apply(lambda x: x.minute)
    df['hour'] = df['time_stamp'].apply(lambda x: x.hour)
    df['day'] = df['time_stamp'].apply(lambda x: x.day)
    df['month'] = df['time_stamp'].apply(lambda x: x.month)
    df['year'] = df['time_stamp'].apply(lambda x: x.year)

    #  Filter the data for the time range that we want to plot
    time_range_start = dt.datetime.now() - dt.timedelta(hours=time_range)
    df = df[df['time_stamp'] > time_range_start]

    # Create the plot
    time = df['time_stamp']
    humidity = df['onboard humidity']
    temperature = df['off-chip temperature']

    trace1 = go.Scatter(
        x=time,
        y=signal.savgol_filter(humidity,  # Smoothing
                               11,  # window size used for filtering
                               3),  # order of fitted polynomial
        mode='lines',
        line=dict(dash='dot', color='royalblue'),
        name='humidity'
    )

    trace2 = go.Scatter(
        x=time,
        y=signal.savgol_filter(temperature,  # Smoothing
                               11,  # window size used for filtering
                               3),  # order of fitted polynomial
        mode='lines',
        line=dict(color='red'),
        name='temp'
    )

    data = [trace1, trace2]

    layout = go.Layout(yaxis=dict(range=[-10, 30]))

    fig = go.Figure(data=data, layout=layout)

    plotly.offline.plot(fig, filename='app/static/chart1.html', auto_open=False)
