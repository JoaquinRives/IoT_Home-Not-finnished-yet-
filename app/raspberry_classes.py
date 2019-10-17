from flask import flash
import RPi.GPIO as GPIO
import time
import threading
from app.timer import timer_func
from app.config import config
from app.camera_management import detect_motion, pi_surveillance
from imutils.video import VideoStream
from picamera import PiCamera
import logging
import smbus
import datetime
import os


logger = logging.getLogger(__name__)
logger = config.config_logger(logger, type='main')

sensor_logger = logging.getLogger(__name__)
sensor_logger = config.config_logger(sensor_logger, type="sensor")


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
            t_now = int(self.get_sensorhub_data()["off-chip temperature"]) #TODO

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
        self.timer_threads[gpio] = threading.Thread(target=timer_func, args=((gpio,) + self.timer_settings[gpio]))
        self.timer_threads[gpio].start()
        self.set_status(gpio, 'timer')
        
        flash(f'Timer activated: {self.timer_settings[gpio][0]} (ON) - {self.timer_settings[gpio][1]} (Off), '
                f'Repeat: {self.timer_settings[gpio][2]}')
        logger.info(f'Timer activated: {self.timer_settings[gpio][0]} (ON) - {self.timer_settings[gpio][1]} (Off), '
                f'Repeat: {self.timer_settings[gpio][2]}')
        

    def start_auto(self, gpio):
        self.auto_threads[gpio] = threading.Thread(target=self.auto_mode, args=((gpio,) + self.auto_settings[gpio]))
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
        self.vs = VideoStream(src=0).start()
        self.webcam_Sts = 'On'
        
        self.webcam_thread = threading.Thread(target=detect_motion, args=(36, self.vs,))
        self.webcam_thread.daemon = True
        self.webcam_thread.start()
        
        logger.info("Webcam activated!")


    def stop_webcam(self):
        self.vs.stop()
        self.vs = None
        self.webcam_Sts = 'Off'

        self.webcam_thread.do_run = False
        self.webcam_thread.join()
        self.webcam_thread = None
        
        logger.info("Webcam deactivated!")


    def start_surveillance(self):
        self.pi_camera = PiCamera()
        self.pi_camera_Sts = 'On'

        self.surveillance_thread = threading.Thread(target=pi_surveillance, args=(self.pi_camera,))
        #self.urveillancem_thread.daemon = True
        self.surveillance_thread.start()
        
        flash("Security Alarm activated!")
        logger.info("Security Alarm activated!")


    def stop_surveillance(self):
        self.pi_camera.stop_preview() # TODO borrar
        self.pi_camera.close()
        self.pi_camera_Sts = 'Off'

        self.surveillance_thread.do_run = False
        self.surveillance_thread.join()
        self.surveillance_thread = None

        flash("Security Alarm deactivated!")
        logger.info("Security Alarm deactivated!")


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
            data["off-chip temperature"] = 'nan'
        elif aReceiveBuf[STATUS_REG] & 0x02 :
            logger.warning("No external temperature sensor!")
            data["off-chip temperature"] = 'nan'
        else :
            data["off-chip temperature"] = str(aReceiveBuf[TEMP_REG])
        
        # Light intensity detection
        if aReceiveBuf[STATUS_REG] & 0x04 :
            #main_logger.warning("Onboard brightness sensor overrange!")
            data["brightness"] = 'nan'
        elif aReceiveBuf[STATUS_REG] & 0x08 :
            #main_logger.warning("Onboard brightness sensor failure!")
            data["brightness"] = 'nan'
        else :
            data["brightness"] = str((aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L]))

        # OnBoard temperature sensor
        data["onboard temperature"] = str(aReceiveBuf[ON_BOARD_TEMP_REG])

        # Humidity sensor
        data["onboard humidity"] = str(aReceiveBuf[ON_BOARD_HUMIDITY_REG])

        if aReceiveBuf[ON_BOARD_SENSOR_ERROR] != 0 :
            logger.warning("Onboard temperature and humidity sensor data may not be up to date!")

        # Pressure sensor
        if aReceiveBuf[BMP280_STATUS] == 0 :
            data["barometer temperature"] = str(aReceiveBuf[BMP280_TEMP_REG])
            data["barometer pressure"] = str((aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16))
        else :
            logger.warning("Onboard barometer works abnormally!")
            data["barometer temperature"] = 'nan'
            data["barometer pressure"] = 'nan'

        # Human detection
        if aReceiveBuf[HUMAN_DETECT] == 1 :
            data["humans detected"] = '1'
        else:
            data["humans detected"] = '0'

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

            # TODO: delete prints

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
                #print("Current off-chip sensor temperature = %d Celsius" % aReceiveBuf[TEMP_REG])
                data.append(str(aReceiveBuf[TEMP_REG]))
            
            # Light intensity detection
            if aReceiveBuf[STATUS_REG] & 0x04 :
                #sensor_logger.warning("Onboard brightness sensor overrange!")
                data.append('nan')
            elif aReceiveBuf[STATUS_REG] & 0x08 :
                #sensor_logger.warning("Onboard brightness sensor failure!")
                data.append('nan')
            else :
                #print("Current onboard sensor brightness = %d Lux" % (aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L]))
                data.append(str((aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L])))

            # OnBoard temperature sensor
            #print("Current onboard sensor temperature = %d Celsius" % aReceiveBuf[ON_BOARD_TEMP_REG])
            data.append(str(aReceiveBuf[ON_BOARD_TEMP_REG]))

            # Humidity sensor
            #print("Current onboard sensor humidity = %d %%" % aReceiveBuf[ON_BOARD_HUMIDITY_REG])
            data.append(str(aReceiveBuf[ON_BOARD_HUMIDITY_REG]))

            if aReceiveBuf[ON_BOARD_SENSOR_ERROR] != 0 :
                sensor_logger.warning("Onboard temperature and humidity sensor data may not be up to date!")

            # Pressure sensor
            if aReceiveBuf[BMP280_STATUS] == 0 :
                #print("Current barometer temperature = %d Celsius" % aReceiveBuf[BMP280_TEMP_REG])
                data.append(str(aReceiveBuf[BMP280_TEMP_REG]))
                #print("Current barometer pressure = %d pascal" % (aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16))
                data.append(str((aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16)))
            else :
                sensor_logger.warning("Onboard barometer works abnormally!")
                data.append('nan')
                data.append('nan')

            # Human detection
            if aReceiveBuf[HUMAN_DETECT] == 1 :
                #print("Live body detected within 5 seconds!")
                data.append('1')
            else:
                #print("No humans detected!")
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

