from flask import flash
import RPi.GPIO as GPIO
import threading
from app.auto_mode import auto_func
from app.timer import timer_func
from app.config import config
from app.camera_management import detect_motion, pi_surveillance
from imutils.video import VideoStream
from picamera import PiCamera
import logging

logger = logging.getLogger(__name__)
logger = config.config_logger(logger)


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
        self.pi_camera = None
        self.pi_camera_Sts = 'Off'


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


    def start_timer(self, gpio):
        self.timer_threads[gpio] = threading.Thread(target=timer_func, args=((gpio,) + self.timer_settings[gpio]))
        self.timer_threads[gpio].start()
        self.set_status(gpio, 'timer')
        
        flash(f'Timer activated: {self.timer_settings[gpio][0]} (ON) - {self.timer_settings[gpio][1]} (Off), '
                f'Repeat: {self.timer_settings[gpio][2]}')
        logger.info(f'Timer activated: {self.timer_settings[gpio][0]} (ON) - {self.timer_settings[gpio][1]} (Off), '
                f'Repeat: {self.timer_settings[gpio][2]}')
        

    def start_auto(self, gpio):
        self.auto_threads[gpio] = threading.Thread(target=auto_func, args=((gpio,) + self.auto_settings[gpio]))
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


    def clean_up(self):
        """ Reset RPi GPIOs """
        logger.info(f'=> Cleaning up GPIOs before exiting...')
        GPIO.cleanup()

