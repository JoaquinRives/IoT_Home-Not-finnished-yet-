from flask import flash
import RPi.GPIO as GPIO
from app.timer import timer_func
from app.camera_management import detect_motion
from imutils.video import VideoStream
from picamera import PiCamera
import smbus
import os
from app.pyimagesearch.tempimage import TempImage
from picamera.array import PiRGBArray
from app.config import config
import warnings
import threading
import dropbox
import datetime
import imutils
import time
import cv2
import logging
from app.emailer_classes import EmailSender

email_sender = EmailSender()

logger = logging.getLogger(__name__)
logger = config.config_logger(logger, type='main')

sensor_logger = logging.getLogger("sensor_logger")
sensor_logger = config.config_logger(sensor_logger, type="sensor")

security_system_logger = logging.getLogger("security_logger")
security_system_logger = config.config_logger(security_system_logger, type="security_system")




class Raspberry1:
    def __init__(self):
        # Set RPi GPIO board mode
        GPIO.setmode(config.BOARD_MODE)

        # Define GPIOs Relay
        self.relay1 = config.RELAY_1  # Light
        self.relay2 = config.RELAY_2  # Heater
        self.relay3 = config.RELAY_3
        self.relay4 = config.RELAY_4

        # GPIOs Status (Off/On, normal/timer/auto)
        self.gpios_Sts =  [(None, None) for i in range(28)]

        # Relay 4 Channel (5V active low - outputMax AC250V)
        self.set_relays()

        # Timer
        self.relays_with_timer = config.RELAYS_WITH_TIMER
        self.timer_threads = [None for i in range(28)]  # Timer: One thread for each GPIO of the raspberry
        self.timer_settings = [(None, None, None) for i in range(28)]

        # Auto-Mode
        self.relays_with_auto = config.RELAYS_WITH_AUTO
        self.auto_threads = [None for i in range(28)]  # Automatic-mode (Heater): One thread for each GPIO of the raspberry
        self.auto_settings = [(None, None) for i in range(28)]

        # Webcam
        self.webcam_Sts = 'Off'
        self.webcam_thread = None
        self.vs = None

        # Surveillance camera
        self.surveillance_thread = None
        self.pi_camera = None
        self.pi_camera_Sts = 'Off'

        # Data collection
        self.data_collection_thread = None

        # Security alarm logging
        with open(config.SECURITY_SYSTEM_LOG_FILE, 'r') as f:
            self.number_of_lines = sum([1 for line in f])
            self.end_positon = f.seek(0, os.SEEK_END)
            # List of new messages to display in the Security Log textbox of index.html
            self.security_log_messages = []


    def set_relays(self):
         # Define GPIOs as output
        GPIO.setup(self.relay1, GPIO.OUT)
        GPIO.setup(self.relay2, GPIO.OUT)
        GPIO.setup(self.relay3, GPIO.OUT)
        GPIO.setup(self.relay4, GPIO.OUT)
         # Turn relays OFF
        GPIO.output(self.relay1, GPIO.HIGH)
        GPIO.output(self.relay2, GPIO.HIGH)
        GPIO.output(self.relay3, GPIO.HIGH)
        GPIO.output(self.relay4, GPIO.HIGH)
        # GPIO status
        self.set_status(self.relay1, 'normal')
        self.set_status(self.relay2, 'normal')
        self.set_status(self.relay3, 'normal')
        self.set_status(self.relay4, 'normal')


    def set_gpio(self, gpio, output):
        """ Set GPIO output """
        if output == 'low':
            GPIO.output(gpio, GPIO.LOW)
        if output == 'high':
            GPIO.output(gpio, GPIO.HIGH)


    def set_status(self, gpio, mode):
        OnOff = 'On' if GPIO.input(gpio) == 0 else 'Off'  # Get current input (HIGH/LOW = 1/0 = Off/On)
        self.gpios_Sts[gpio] = (OnOff, mode)  # (Off/On, normal/timer/auto)


    def get_status(self, gpio):
        OnOff = 'On' if GPIO.input(gpio) == 0 else 'Off'  # Get current input (HIGH/LOW = 1/0 = Off/On)
        mode = self.gpios_Sts[gpio][1]  # Get mode (normal/timer/auto)

        return (OnOff, mode)


    def auto_mode(self, actuator, temp, t_range):
        # Temperature we want to maintain constant
        t_keep = int(temp)
        t_max, t_min = t_keep + int(t_range),  t_keep - int(t_range)

        t = threading.currentThread()

        while getattr(t, "do_run", True):
            # Get current temperature
            t_now = int(self.get_sensorhub_data()["off-chip temperature"])

            if int(t_now) > int(t_max):
                # Turn off if the temperature goes above the limit
                GPIO.output(actuator, GPIO.HIGH)
                self.set_status(actuator, 'auto')
            elif t_now < t_min:
                # Turn on if the temperature falls below the limit
                GPIO.output(actuator, GPIO.LOW)
                self.set_status(actuator, 'auto')
            else:
                logger.warning(f"Sensor failure on Auto-Mode: Temp(C)={t_now}")

            time.sleep(6)


    def start_timer(self, gpio):
        self.timer_threads[gpio] = threading.Thread(
            target=timer_func, args=((gpio,) + self.timer_settings[gpio]))
        self.timer_threads[gpio].start()
        self.set_status(gpio, 'timer')

        flash(f'Timer activated: {self.timer_settings[gpio][0]} (ON) - {self.timer_settings[gpio][1]} (Off), '
                f'Repeat: {self.timer_settings[gpio][2]}')
        logger.info(f'Timer activated: {self.timer_settings[gpio][0]} (ON) - {self.timer_settings[gpio][1]} (Off), '
                f'Repeat: {self.timer_settings[gpio][2]}')


    def start_auto(self, gpio):
        self.auto_threads[gpio] = threading.Thread(
            target=self.auto_mode, args=((gpio,) + self.auto_settings[gpio]))
        self.auto_threads[gpio].start()
        self.set_status(gpio, 'auto')

        flash(f'Auto-Mode activated : {self.auto_settings[gpio][0]}∓{self.auto_settings[gpio][1]} C°')
        logger.info(f'Auto-Mode activated : {self.auto_settings[gpio][0]}∓{self.auto_settings[gpio][1]} C°')


    def stop_timer(self, gpio):
        if self.timer_threads[gpio]:
            self.timer_threads[gpio].do_run = False
            self.timer_threads[gpio].join()
            self.timer_threads[gpio] = None
            self.set_status(gpio, 'normal')

            flash("Timer deactivated!")
            logger.info("Timer deactivated!")


    def stop_auto(self, gpio):
        if self.auto_threads[gpio]:
            self.auto_threads[gpio].do_run = False
            self.auto_threads[gpio].join()
            self.auto_threads[gpio] = None
            self.set_status(gpio, 'normal')

            flash("Auto-Mode deactivated!")
            logger.info("Auto-Mode deactivated!")


    def start_webcam(self):
        if self.pi_camera_Sts == 'On':
            self.stop_surveillance()

        if self.webcam_Sts == 'Off':
            self.vs = VideoStream(src=0).start()
            self.webcam_Sts = 'On'

            self.webcam_thread = threading.Thread(target=detect_motion, args=(36, self.vs,))
            self.webcam_thread.daemon = True
            self.webcam_thread.start()

            logger.info("Webcam activated!")


    def stop_webcam(self):
        if self.webcam_Sts == 'On':
            self.vs.stop()
            self.vs = None
            self.webcam_Sts = 'Off'

            self.webcam_thread.do_run = False
            self.webcam_thread.join()
            self.webcam_thread = None

            logger.info("Webcam deactivated!")


    def start_surveillance(self):
        if  self.webcam_Sts == 'On':
            self.stop_webcam()

        if self.pi_camera_Sts == 'Off':
            self.pi_camera = PiCamera()
            self.pi_camera_Sts = 'On'

            self.surveillance_thread = threading.Thread(target=self.pi_surveillance, args=(self.pi_camera,))
            self.surveillance_thread.daemon = True
            self.surveillance_thread.start()

            self.security_log_messages = []

            flash("Security Alarm activated!")
            logger.info("Security Alarm activated!")
            security_system_logger.info("Security Alarm activated!")


    def stop_surveillance(self):
        if self.pi_camera_Sts == 'On':
            done = False
            while not done:
                try:
                    self.pi_camera.close()
                    time.sleep(2)
                    done = True

                except:
                    logger.warning("Exception regarding the buffer when closing pi_camera")
                    done = False

            self.pi_camera_Sts = 'Off'

            flash("Security Alarm deactivated!")
            logger.info("Security Alarm deactivated!")
            security_system_logger.info("Security Alarm deactivated!")


    def pi_surveillance(self, pi_camera):
        warnings.filterwarnings("ignore")

        if config.surveillance_config["use_dropbox"]:
            # Connect to dropbox and start the session authorization process
            client = dropbox.Dropbox(config.surveillance_config["dropbox_access_token"])
            logger.info("dropbox account linked")

        # Initialize the camera and grab a reference to the raw camera capture
        camera = pi_camera
        camera.resolution = tuple(config.surveillance_config["resolution"])
        camera.framerate = config.surveillance_config["fps"]
        rawCapture = PiRGBArray(camera, size=tuple(config.surveillance_config["resolution"]))

        # Allow the camera to warmup, then initialize the average frame, last
        # uploaded timestamp, and frame motion counter
        logger.info("warming up camera...")
        time.sleep(config.surveillance_config["camera_warmup_time"])
        avg = None
        lastUploaded = datetime.datetime.now()
        lastEmailed = datetime.datetime.now()

        recent_captures = tuple()

        motionCounter = 0

        for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            # Grab the raw NumPy array representing the image and initialize
            # the timestamp and occupied/unoccupied text
            frame = f.array
            timestamp = datetime.datetime.now()
            text = "Unoccupied"

            # Resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # If the average frame is None, initialize it
            if avg is None:
                avg = gray.copy().astype("float")
                rawCapture.truncate(0)
                continue

            # Accumulate the weighted average between the current frame and previous frames,
            # then compute the difference between the current frame and running average
            cv2.accumulateWeighted(gray, avg, 0.5)
            frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

            # Threshold the delta image, dilate the thresholded image to fill
            # in holes, then find contours on thresholded image
            thresh = cv2.threshold(frameDelta, config.surveillance_config["delta_thresh"], 255,
                                cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            # Loop over the contours
            for c in cnts:
                # Df the contour is too small, ignore it
                if cv2.contourArea(c) < config.surveillance_config["min_area"]:
                    continue

                # Compute the bounding box for the contour, draw it on the frame, and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = "Occupied"

            # Draw the text and timestamp on the frame
            ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
            cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.35, (0, 0, 255), 1)

            # Check to see if the room is occupied
            if text == "Occupied":
                # Check to see if enough time has passed between uploads
                if (timestamp - lastUploaded).seconds >= config.surveillance_config["min_upload_seconds"]:
                    # Increment the motion counter
                    motionCounter += 1

                    # Check to see if the number of frames with consistent motion is high enough
                    if motionCounter >= config.surveillance_config["min_motion_frames"]:
                        logger.info('Security Alarm: Movement detected!')
                        security_system_logger.info('Movement detected in the room!')

                        # Save capture in the surveillance_captures directory
                        cv2.imwrite(f"{config.surveillance_config['captures_folder']}/{ts}.jpg", frame)
                        logger.info(f"Capture saved: {config.surveillance_config['captures_folder']}/{ts}.jpg")

                        # Add capture to recent captures
                        recent_captures= (f"{config.surveillance_config['captures_folder']}/{ts}.jpg",) + recent_captures

                        # Check to see if dropbox sohuld be used
                        if config.surveillance_config["use_dropbox"]:
                            # write the image to temporary file
                            t = TempImage()
                            cv2.imwrite(t.path, frame)

                            # upload the image to Dropbox and cleanup the tempory image
                            path = "/{timestamp}.jpg".format(timestamp=ts)
                            client.files_upload(open(t.path, "rb").read(), path)
                            t.cleanup()

                            logger.info("Dropbox upload: {}".format(ts))
                            security_system_logger.info(f"Capture uploaded to Dropbox: www.{config.surveillance_config['dropbox_base_path']}")

                        if config.surveillance_config["email_alert"]:
                            if (timestamp - lastEmailed).seconds >= config.surveillance_config["min_email_seconds"]:

                                # Send email notification with the most recent captures
                                email_sender.send_email(
                                    subject="Security Alarm",
                                    message=f"The Surveillance Camera detected movement in your room. <br> {config.surveillance_config['dropbox_base_path']}",
                                    attach_images=recent_captures[:config.surveillance_config["max_images_email"]]
                                )
                                logger.info(f"Email security notification sent to {config.TO_ADDR}")
                                security_system_logger.info(f"Email notification sent to '{config.TO_ADDR}'")

                                # Update the last_emailed timestamp and recent_captures
                                lastEmailed = timestamp
                                recent_captures = tuple()

                        # Update the last uploaded timestamp and reset the motion counter
                        lastUploaded = timestamp
                        motionCounter = 0

            # Otherwise, the room is not occupied
            else:
                motionCounter = 0

            # Clear the stream in preparation for the next frame
            rawCapture.truncate(0)


    def security_log_updater(self):
        """ 
        Returns the messages to display in the scrollable 
        textbox of the security log (index.html)
        """
        last_number_of_lines = self.number_of_lines
        last_end_position = self.end_positon

        try:
            with open(config.SECURITY_SYSTEM_LOG_FILE, 'r') as f:
                # Count the current number of lines
                number_of_lines_now = sum([1 for line in f])

                # Check if something has been added since last time
                if number_of_lines_now > last_number_of_lines:
                    # Set the pointer before the new lines
                    f.seek(last_end_position, 0)

                    # Append the new messages to the alarm_log list
                    for line in f.readlines():
                        self.security_log_messages.append(line)

                    # Update the number of lines and the end position
                    self.number_of_lines = number_of_lines_now
                    self.end_positon = f.seek(0, os.SEEK_END)

                    return self.security_log_messages[::-1]

                else:
                    return self.security_log_messages[::-1]

        except Exception as e:
            self.security_log_messages.append(e)


    def get_sensorhub_data(self):
        DEVICE_BUS = 1
        DEVICE_ADDR = 0x17

        TEMP_REG = 0x01
        LIGHT_REG_L = 0x02
        LIGHT_REG_H = 0x03
        STATUS_REG = 0x04
        ON_BOARD_TEMP_REG = 0x05
        ON_BOARD_HUMIDITY_REG = 0x06
        ON_BOARD_SENSOR_ERROR = 0x07
        BMP280_TEMP_REG = 0x08
        BMP280_PRESSURE_REG_L = 0x09
        BMP280_PRESSURE_REG_M = 0x0A
        BMP280_PRESSURE_REG_H = 0x0B
        BMP280_STATUS = 0x0C
        HUMAN_DETECT = 0x0D

        bus = smbus.SMBus(DEVICE_BUS)

        aReceiveBuf = []

        aReceiveBuf.append(0x00)

        data = {}

        # Thermal infrarred
        for i in range(TEMP_REG,HUMAN_DETECT + 1):
            aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))

        # External temperature detection (probe)
        if aReceiveBuf[STATUS_REG] & 0x01 :
            logger.warning("Off-chip temperature sensor overrange!")
            data["off_chip_temperature"] = 'nan'
        elif aReceiveBuf[STATUS_REG] & 0x02 :
            logger.warning("No external temperature sensor!")
            data["off_chip_temperature"] = 'nan'
        else :
            data["off_chip_temperature"] = str(aReceiveBuf[TEMP_REG])

        # Light intensity detection
        if aReceiveBuf[STATUS_REG] & 0x04 :
            # main_logger.warning("Onboard brightness sensor overrange!")
            data["brightness"] = 'nan'
        elif aReceiveBuf[STATUS_REG] & 0x08 :
            # main_logger.warning("Onboard brightness sensor failure!")
            data["brightness"] = 'nan'
        else :
            data["brightness"] = str((aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L]))

        # OnBoard temperature sensor
        data["onboard_temperature"] = str(aReceiveBuf[ON_BOARD_TEMP_REG])

        # Humidity sensor
        data["onboard_humidity"] = str(aReceiveBuf[ON_BOARD_HUMIDITY_REG])

        if aReceiveBuf[ON_BOARD_SENSOR_ERROR] != 0 :
            logger.warning("Onboard temperature and humidity sensor data may not be up to date!")

        # Pressure sensor
        if aReceiveBuf[BMP280_STATUS] == 0 :
            data["barometer_temperature"] = str(aReceiveBuf[BMP280_TEMP_REG])
            data["barometer_pressure"] = str((aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16))
        else :
            logger.warning("Onboard barometer works abnormally!")
            data["barometer_temperature"] = 'nan'
            data["barometer_pressure"] = 'nan'

        # Human detection
        if aReceiveBuf[HUMAN_DETECT] == 1 :
            data["humans_detected"] = '1'
        else:
            data["humans_detected"] = '0'

        return data


    def data_collection(self):
        """ Function for collecting and saving sensors data """

        t = threading.currentThread()

        while getattr(t, "do_run", True):
            DEVICE_BUS = 1
            DEVICE_ADDR = 0x17

            TEMP_REG = 0x01
            LIGHT_REG_L = 0x02
            LIGHT_REG_H = 0x03
            STATUS_REG = 0x04
            ON_BOARD_TEMP_REG = 0x05
            ON_BOARD_HUMIDITY_REG = 0x06
            ON_BOARD_SENSOR_ERROR = 0x07
            BMP280_TEMP_REG = 0x08
            BMP280_PRESSURE_REG_L = 0x09
            BMP280_PRESSURE_REG_M = 0x0A
            BMP280_PRESSURE_REG_H = 0x0B
            BMP280_STATUS = 0x0C
            HUMAN_DETECT = 0x0D

            bus = smbus.SMBus(DEVICE_BUS)

            aReceiveBuf = []

            aReceiveBuf.append(0x00)

            data = []
            data.append(str(datetime.datetime.now()))

            # Thermal infrarred
            for i in range(TEMP_REG,HUMAN_DETECT + 1):
                aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))

            # External temperature detection (probe)
            if aReceiveBuf[STATUS_REG] & 0x01 :
                sensor_logger.warning("Off-chip temperature sensor overrange!")
                data.append('nan')
            elif aReceiveBuf[STATUS_REG] & 0x02 :
                sensor_logger.warning("No external temperature sensor!")
                data.append('nan')
            else :
                data.append(str(aReceiveBuf[TEMP_REG]))

            # Light intensity detection
            if aReceiveBuf[STATUS_REG] & 0x04 :
                #sensor_logger.warning("Onboard brightness sensor overrange!")
                data.append('nan')
            elif aReceiveBuf[STATUS_REG] & 0x08 :
                #sensor_logger.warning("Onboard brightness sensor failure!")
                data.append('nan')
            else :
                data.append(str((aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L])))

            # OnBoard temperature sensor
            data.append(str(aReceiveBuf[ON_BOARD_TEMP_REG]))

            # Humidity sensor
            data.append(str(aReceiveBuf[ON_BOARD_HUMIDITY_REG]))

            if aReceiveBuf[ON_BOARD_SENSOR_ERROR] != 0 :
                sensor_logger.warning(
                    "Onboard temperature and humidity sensor data may not be up to date!")

            # Pressure sensor
            if aReceiveBuf[BMP280_STATUS] == 0 :
                data.append(str(aReceiveBuf[BMP280_TEMP_REG]))
                data.append(str((aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16)))
            else :
                sensor_logger.warning("Onboard barometer works abnormally!")
                data.append('nan')
                data.append('nan')

            # Human detection
            if aReceiveBuf[HUMAN_DETECT] == 1 :
                data.append('1')
            else:
                data.append('0')

            data_row = ";".join(data) + "\n"

            data_header = "time_stamp;off-chip temperature;brightness;onboard temperature;onboard humidity;" \
                "barometer temperature;barometer pressure;humans detected\n"

            sensor_data_file = config.SENSOR_DATA_FILE

            # Create the sensors_data file and add the "header" if the file doesn't exist or it is empty
            if not os.path.exists(config.SENSOR_DATA_FILE) or not os.path.getsize(config.SENSOR_DATA_FILE) > 0:
                try:
                    with open(sensor_data_file, 'w') as f:
                        f.write(data_header)
                except Exception as e:
                    sensor_logger.warning(f"Failure writing header to sensor_data.txt - Exception: {e}")

            # Append row of data to the sensors data file
            try:
                with open(sensor_data_file, 'a') as f:
                    f.write(data_row)

            except Exception as e:
                sensor_logger.warning(f"Failure writing row of data to sensor_data.txt - Exception: {e}")

            time.sleep(10)


    def start_data_collection(self):
        self.data_collection_thread = threading.Thread(target=self.data_collection)
        self.data_collection_thread.start()

        logger.info(f'Data collection activated')


    def stop_data_collection(self):
        self.data_collection_thread.do_run = False
        self.data_collection_thread.join()
        self.data_collection_thread = None

        logger.info(f'Data collection deactivated')


    def clean_up(self):
        """ Reset RPi GPIOs """
        logger.info(f'=> Cleaning up GPIOs before exiting...')
        GPIO.cleanup()

