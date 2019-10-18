from flask import request, redirect, Blueprint, session
from app.raspberry_classes import Raspberry1
from app.forms import Timer_form, Auto_form
import atexit
import logging
from flask import Response
from flask import render_template
import threading
from app.camera_management import generate_video_feed
from app.chart_creator import create_chart
import app.config.config as config

logger = logging.getLogger(__name__)
logger = config.config_logger(logger)

app = Blueprint('app', __name__)

# Create a instance of the Raspberry
rp1 = Raspberry1()

# Start collecting data from the sensors
rp1.start_data_collection()

# Create the chart with the sensors data and keep it updated
chart_thread = threading.Thread(target=create_chart, args=(config.CHART_SETTINGS_1,))
chart_thread.start()


def before_exit():
    """ To execute before exiting """

    logger.info("Before exiting function started...")

    global chart_thread, data_collection_thread
    
    # Stop all threads
    if chart_thread:
        logger.info("Stopping chart thread")
        chart_thread.do_run = False
        chart_thread.join()
        chart_thread = None

    if rp1.data_collection_thread:
        logger.info("Stopping data collection thread")
        rp1.stop_data_collection()

    if rp1.webcam_thread:
        logger.info("Stopping webcam thread")
        rp1.stop_webcam()

    if rp1.surveillance_thread:
        logger.info("Stopping surveillance thread")
        rp1.stop_surveillance()

    if not all(thread is None for thread in rp1.timer_threads):
        logger.info("Stopping timer threads")
        for thread in rp1.timer_threads:
            if thread:
                rp1.stop_timer(rp1.timer_threads.index(thread))
    
    if not all(thread is None for thread in rp1.auto_threads):
        logger.info("Stopping auto threads")
        for thread in rp1.auto_threads:
            if thread:
                rp1.stop_auto(rp1.auto_threads.index(thread))
    
    # Reset the GPIOs before exit the App
    rp1.clean_up()

    logger.info("Before exiting function finnish")


@app.route('/health', methods=['GET'])
def health():
    if request.method == 'GET':
        logger.info('health status OK')
        return 'ok'


@app.route("/")
@app.route('/index')
def index():
    
    # Get data from the sensors
    data = rp1.get_sensorhub_data()

    # Scrollable textbox of the security log
    security_log_messages = rp1.security_log_updater()

    # Read Status and pass everything to the index.html
    template_data = {
        "relay1_Sts": rp1.get_status(rp1.relay1),
        "relay2_Sts": rp1.get_status(rp1.relay2),
        "relay3_Sts": rp1.get_status(rp1.relay3),
        "relay4_Sts": rp1.get_status(rp1.relay4),
        "webcam_Sts": rp1.webcam_Sts,
        "off_chip_temperature": data["off_chip_temperature"],
        "brightness": data["brightness"],
        "onboard_temperature": data["onboard_temperature"],
        "onboard_humidity": data["onboard_humidity"],
        "barometer_temperature": data["barometer_temperature"],
        "barometer_pressure": data["barometer_pressure"],
        "humans_detected": data["humans_detected"],
        "camera_Sts": rp1.pi_camera_Sts,
        "webcam_Sts":  rp1.webcam_Sts,
        "security_log_messages": security_log_messages
    }
    return render_template('index.html', **template_data)


@app.route("/video_feed")
def video_feed():
    # Return the response generated along with the specific media type (mime type)
    return Response(generate_video_feed(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/webcam/<action>")
def webcam(action):
    if action == 'On':
        rp1.start_webcam()

    elif action == 'Off':
        rp1.stop_webcam()

    return redirect("/index")


@app.route("/securityAlarm/<action>")
def surveillance(action):
    if action == 'On':
        rp1.start_surveillance()

    elif action == 'Off':
        rp1.stop_surveillance()

    return redirect("/index")


@app.route("/<deviceName>/<unit>/<action>")
def actions(deviceName, unit, action):
    
    logger.info(f'=> /{deviceName}/{unit}/{action}')

    # Devices
    if deviceName == 'Relays':
        
        # Units
        if unit == '1':
            actuator = rp1.relay1
        if unit == '2':
            actuator = rp1.relay2
        if unit == '3':
            actuator = rp1.relay3
        if unit == '4':
            actuator = rp1.relay4

        # Actions
        if actuator in rp1.relays_with_auto:
            if action == 'On' or action == 'Off':
                if rp1.auto_threads[actuator]:  # Stop thread if running
                    rp1.stop_auto(actuator)  
                    
            if action == 'auto':
                if rp1.auto_threads[actuator]:  # Stop thread if already running
                    rp1.stop_auto(actuator)  
                else:
                    if rp1.auto_settings[actuator]:
                        rp1.start_auto(actuator)

        if actuator in rp1.relays_with_timer:
            if action == 'On' or action == 'Off':
                if rp1.timer_threads[actuator]:  # Stop thread if already running
                    rp1.stop_timer(actuator)  
            if action == 'timer':
                if rp1.timer_threads[actuator]:  # Stop thread if already running
                    rp1.stop_timer(actuator) 
                else:
                    if rp1.timer_settings[actuator]:
                        rp1.start_timer(actuator)

        if action == "On":
            rp1.set_gpio(actuator, 'low')
        if action == "Off":
            rp1.set_gpio(actuator, 'high')
            
    return redirect("/index")


@app.route("/timer/<deviceName>/<unit>", methods=['GET', 'POST'])
def timer(deviceName, unit):
    
    logger.info(f'=> /timer/{deviceName}/{unit}')

    # Devices
    if deviceName == 'Relays':
        # Units
        if unit == '1':
            actuator = rp1.relay1
        if unit == '2':
            actuator = rp1.relay2
        if unit == '3':
            actuator = rp1.relay3
        if unit == '4':
            actuator = rp1.relay4

    # Check if the Timer is already running:
    if rp1.timer_threads[actuator]:
        rp1.stop_timer(actuator)
        
        return redirect("/index")

    else:
        # To pass a variable betweem web pages
        session['device_timer'] = deviceName
        session['unit_timer'] = unit 
        session['actuator_timer'] = actuator

        return render_template('set_timer.html')


@app.route("/set_timer", methods=['GET', 'POST'])
def set_timer():
    
    form = Timer_form()

    # Retrive variables from session
    deviceName = session.get('device_timer', None)
    unit = session.get('unit_timer', None)
    actuator = session.get('actuator_timer', None)

    if request.method == 'POST':
        time_on = request.form['time_on']
        time_off = request.form['time_off']
        try:
            repeat = request.form['repeat']
        except:
            repeat = 'off'

        rp1.timer_settings[actuator] = (time_on, time_off, repeat)

        # Check if the Auto-Mode is running:
        if rp1.auto_threads[actuator]:
                    rp1.stop_auto(actuator)

    return redirect(f"/{deviceName}/{unit}/timer")


@app.route("/auto/<deviceName>/<unit>", methods=['GET', 'POST'])
def auto(deviceName, unit):
    
    logger.info(f'=> /auto/{deviceName}/{unit}')

    # Devices
    if deviceName == 'Relays':
        # Units
        if unit == '1':
            actuator = rp1.relay1
        if unit == '2':
            actuator = rp1.relay2
        if unit == '3':
            actuator = rp1.relay3
        if unit == '4':
            actuator = rp1.relay4

    # Check if the auto-mode is already running:
    if rp1.auto_threads[actuator]:
        rp1.stop_auto(actuator)
        
        return redirect("/index")
    else:        
        # To pass a variable between web pages
        session['device_auto'] = deviceName
        session['unit_auto'] = unit 
        session['actuator_auto'] = actuator

        return render_template('set_auto.html')


@app.route("/set_auto", methods=['GET', 'POST'])
def set_auto():
    
    form = Auto_form()

    # Retrive variables from session
    deviceName = session.get('device_auto', None)
    unit = session.get('unit_auto', None)
    actuator = session.get('actuator_auto', None)

    if request.method == 'POST':
        temperature = request.form['temperature']
        temp_range = request.form['temp_range']

        rp1.auto_settings[actuator] = (temperature, temp_range)

        # Check if the Timer is running:
        if rp1.timer_threads[actuator]:
                    rp1.stop_timer(actuator)

    return redirect(f"/{deviceName}/{unit}/auto")


atexit.register(before_exit)