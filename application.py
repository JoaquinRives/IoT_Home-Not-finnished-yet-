from flask import Flask, flash ,request 
from flask_basicauth import BasicAuth
from raspberry import Raspberry_1
from flask import render_template, redirect, url_for
import RPi.GPIO as GPIO
from forms import Timer_form, Auto_form
from flask import Flask, session
import time


rp1 = Raspberry_1()

app = Flask(__name__)

app.config['BASIC_AUTH_FORCE'] = True
app.config['SECRET_KEY'] = "powerful secret key"

# Basic Authentication
basic_auth = BasicAuth(app)

app.config['BASIC_AUTH_USERNAME'] = 'joaquin'
app.config['BASIC_AUTH_PASSWORD'] = 'qwerty'


@app.route("/")
@app.route('/index')
def index():
    # Read Sensors Status
    # #TODO Change this to live data???????????
    template_data = {
        'relay1_Sts': rp1.get_status(rp1.relay1),
        'relay2_Sts': rp1.get_status(rp1.relay2),
        'relay3_Sts': rp1.get_status(rp1.relay3),
        'relay4_Sts': rp1.get_status(rp1.relay4),
    }
    return render_template('index.html', **template_data, reload=time.time())


@app.route("/<deviceName>/<unit>/<action>")
def actions(deviceName, unit, action):
    
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

    return redirect(url_for('index'))


@app.route("/timer/<deviceName>/<unit>", methods=['GET', 'POST'])
def timer(deviceName, unit):
    
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
        
        return redirect(url_for('index'))

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

    print(form.errors)
    if request.method == 'POST':
        time_on = request.form['time_on']
        time_off = request.form['time_off']
        try:
            repeat = request.form['repeat']
        except:
            repeat = 'off'

        print(time_on, time_off, repeat)
        rp1.timer_settings[actuator] = (time_on, time_off, repeat)

        # Check if the Auto-Mode is running:
        if rp1.auto_threads[actuator]:
                    rp1.stop_auto(actuator)

    return redirect(f"/{deviceName}/{unit}/timer")


@app.route("/auto/<deviceName>/<unit>", methods=['GET', 'POST'])
def auto(deviceName, unit):
    
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
        
        return redirect(url_for('index'))

    else:        
        # To pass a variable between web pages
        session['device_auto'] = deviceName
        session['unit_auto'] = unit 
        session['actuator_auto'] = actuator

        return render_template('set_auto.html') #**template_data)


@app.route("/set_auto", methods=['GET', 'POST'])
def set_auto():
    
    form = Auto_form()

    # Retrive variables from session
    deviceName = session.get('device_auto', None)
    unit = session.get('unit_auto', None)
    actuator = session.get('actuator_auto', None)

    print(form.errors)
    if request.method == 'POST':
        temperature = request.form['temperature']
        temp_range = request.form['temp_range']

        print(temperature, temp_range, unit, actuator)

        rp1.auto_settings[actuator] = (temperature, temp_range)

        # Check if the Timer is running:
        if rp1.timer_threads[actuator]:
                    rp1.stop_timer(actuator)

    return redirect(f"/{deviceName}/{unit}/auto")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)


