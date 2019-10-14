from flask import request, render_template, redirect, Blueprint, session, Response
from app.raspberry_classes import Raspberry1
from app.forms import Timer_form, Auto_form
import time
import atexit
import logging
from app.config.config import config_logger

##########################
from app.pyimagesearch.motion_detection import SingleMotionDetector
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2
from app.live_video_feed import detect_motion, generate

outputFrame = None
lock = threading.Lock()

vs = None

##########################

logger = logging.getLogger(__name__)
logger = config_logger(logger)

app = Blueprint('app', __name__)

# Create a instance of the Raspberry
rp1 = Raspberry1()

rp1.start_webcam()   ################################################


@app.route('/health', methods=['GET'])
def health():
    if request.method == 'GET':
        logger.info('health status OK')
        return 'ok'


@app.route("/")
@app.route('/index')
def index():
    
    # Read GPIOs Status
    template_data = {
        'relay1_Sts': rp1.get_status(rp1.relay1),
        'relay2_Sts': rp1.get_status(rp1.relay2),
        'relay3_Sts': rp1.get_status(rp1.relay3),
        'relay4_Sts': rp1.get_status(rp1.relay4),
    }
    return render_template('index.html', **template_data) # reload=time.time()

####################################################
# def detect_motion(frameCount):
# 	# grab global references to the video stream, output frame, and
# 	# lock variables
# 	global vs, outputFrame, lock

# 	# initialize the motion detector and the total number of frames
# 	# read thus far
# 	md = SingleMotionDetector(accumWeight=0.1)
# 	total = 0

# 	# loop over frames from the video stream
# 	while True:
# 		# read the next frame from the video stream, resize it,
# 		# convert the frame to grayscale, and blur it
# 		frame = vs.read()
# 		frame = imutils.resize(frame, width=400)
# 		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# 		gray = cv2.GaussianBlur(gray, (7, 7), 0)

# 		# grab the current timestamp and draw it on the frame
# 		timestamp = datetime.datetime.now()
# 		cv2.putText(frame, timestamp.strftime(
# 			"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
# 			cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

# 		# if the total number of frames has reached a sufficient
# 		# number to construct a reasonable background model, then
# 		# continue to process the frame
# 		if total > frameCount:
# 			# detect motion in the image
# 			motion = md.detect(gray)

# 			# cehck to see if motion was found in the frame
# 			if motion is not None:
# 				# unpack the tuple and draw the box surrounding the
# 				# "motion area" on the output frame
# 				(thresh, (minX, minY, maxX, maxY)) = motion
# 				cv2.rectangle(frame, (minX, minY), (maxX, maxY),
# 					(0, 0, 255), 2)
		
# 		# update the background model and increment the total number
# 		# of frames read thus far
# 		md.update(gray)
# 		total += 1

# 		# acquire the lock, set the output frame, and release the
# 		# lock
# 		with lock:
# 			outputFrame = frame.copy()
		
# def generate():
# 	# grab global references to the output frame and lock variables
# 	global outputFrame, lock

# 	# loop over frames from the output stream
# 	while True:
# 		# wait until the lock is acquired
# 		with lock:
# 			# check if the output frame is available, otherwise skip
# 			# the iteration of the loop
# 			if outputFrame is None:
# 				continue

# 			# encode the frame in JPEG format
# 			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

# 			# ensure the frame was successfully encoded
# 			if not flag:
# 				continue

# 		# yield the output frame in the byte format
# 		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
# 			bytearray(encodedImage) + b'\r\n')



@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")


###################################################


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


# Reset the GPIOs before exit the App
atexit.register(rp1.clean_up)

####################################################
	# start a thread that will perform motion detection
# t = threading.Thread(target=detect_motion, args=(
#     36,))
# t.daemon = True
# t.start()


# release the video stream pointer
#vs.stop() # TODO


###########################################################


