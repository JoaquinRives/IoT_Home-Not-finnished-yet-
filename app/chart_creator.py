import pandas as pd
from scipy import signal
import plotly
import logging
import plotly.graph_objs as go
import datetime as dt
import threading
from app.config import config
import time
# import plotly.io as pio
# pio.renderers.default = "browser"

logger = logging.getLogger(__name__)
logger = config.config_logger(logger)

def datetime_convert(x):
    """ Convert str to datetime format"""
    x = dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
    return x


def create_chart(chart_settings):
    """ Creates html charts (like the one embeded in index.html) and keeps them updated """

    chart_name = chart_settings['chart_name']

    t = threading.currentThread()

    next_update = dt.datetime.now()  # next_update: It indicates when to update the chart

    while getattr(t, "do_run", True):  # To stop the thread with a Flag
        
        # Create a new chart every 20 min to keep it updated
        if next_update <= dt.datetime.now():
            # Import sensor data
            df = pd.read_csv(config.SENSOR_DATA_FILE, sep=";")

            df.replace(to_replace="nan", value=None, inplace=True)

            # Columns of the data that we want to use
            features_to_plot = chart_settings["features"]
            features_to_use = ['time_stamp'] + features_to_plot

            df = df[[col for col in df.columns if col in features_to_use]]

            # Convert time_stamp string to datatime type
            df['time_stamp'] = df['time_stamp'].apply(datetime_convert)

            #  Filter the data for the time range that we want to plot
            if chart_settings["time_range"]:
                n_days = chart_settings["time_range"]  # Number of days to plot
                startign_date = dt.datetime.now() - dt.timedelta(days=n_days)
                df = df[df['time_stamp'] > startign_date]

            # Create the plot
            x_axis = df['time_stamp']

            data = []

            for feature in features_to_plot:
                try:
                    trace = go.Scatter(
                        x=x_axis,
                        y=signal.savgol_filter(df[feature],  # Smoothing
                                            11,  # window size used for filtering
                                            3),  # order of fitted polynomial
                        mode=chart_settings["format"][feature]['mode'],
                        line=chart_settings["format"][feature]['line'],
                        name=chart_settings["format"][feature]['name'])
                except:
                    trace = go.Scatter(
                        x=x_axis,
                        y=signal.savgol_filter(df[feature],  # Smoothing
                                            11,  # window size used for filtering
                                            3),  # order of fitted polynomial
                        mode='lines',
                        line=dict(dash='solid', color='red'),
                        name=feature)

                data.append(trace)

            layout = go.Layout(yaxis=dict(range=chart_settings["y_axis"]))
            fig = go.Figure(data=data, layout=layout)
            fig.update_layout(xaxis_rangeslider_visible=True)
            filename = str(config.APP_ROOT) + f"/static/{chart_name}.html"
            plotly.offline.plot(fig, filename=filename, auto_open=False)

            logger.info("Sensor chart updated")

            # Set the next update in 20 min and go to sleep
            next_update = dt.datetime.now() + dt.timedelta(minutes=15)
            time.sleep(10)

        else:
            time.sleep(10)
