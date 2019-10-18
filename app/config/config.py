import os
import pathlib
import logging
import RPi.GPIO as GPIO

# Path to config file
PATH_CONFIG = pathlib.Path(__file__).resolve().parent

# Path to the app
APP_ROOT = pathlib.Path(PATH_CONFIG).resolve().parent

# Logging file
LOG_FILE = APP_ROOT / 'log_file.log'

# Logging file sensor errors 
SENSOR_ERROR_LOG_FILE = APP_ROOT / 'sensors_data/sensor_error.log'

# Sensors data file
SENSOR_DATA_FILE = APP_ROOT / 'sensors_data/sensor_data.txt'

# Logging file security system 
SECURITY_SYSTEM_LOG_FILE = APP_ROOT / 'surveillance_data/security.log'

# Surveillance captures directory
SURVEILLANCE_CAPTURES_DIR = APP_ROOT / 'surveillance_data/captures'


# Flask app
class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'this-needs-to-be-changed'
    SERVER_PORT = 5000
    BASIC_AUTH_FORCE = True
    BASIC_AUTH_USERNAME = 'joaquin'
    BASIC_AUTH_PASSWORD = 'qwerty'  # Change password


class ProductionConfig(Config):
    DEBUG = False
    SERVER_ADDRESS: os.environ.get('SERVER_ADDRESS', '192.168.1.37')
    SERVER_PORT: os.environ.get('SERVER_PORT', '80')


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    THREADED = True
    USE_RELOADER = False


class TestingConfig(Config):
    TESTING = True


# Raspberry_Pi
BOARD_MODE = GPIO.BCM

RELAY_1 = 5  # Light
RELAY_2 = 6  # Heater
RELAY_3 = 13
RELAY_4 = 19

RELAYS_WITH_AUTO = [RELAY_2]
RELAYS_WITH_TIMER = [RELAY_1, RELAY_2, RELAY_3, RELAY_4]

# Logger
FORMAT_MAIN_LOGGER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s —"
    "%(funcName)s:%(lineno)d — %(message)s")

FORMAT_SENSOR_LOGGER = logging.Formatter(
    "%(asctime)s — %(lineno)d — %(message)s")

FORMAT_SECURITY_SYSTEM_LOGGER = logging.Formatter(
    "%(asctime)s - %(message)s")


def config_logger(logger, type="main"):
    if type == "main":
        
        # Config level
        logging.basicConfig(
            level=logging.DEBUG)  # To log everything, by default it only logs warning and above.

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(LOG_FILE)
        c_handler.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.INFO)

        # Create formatters and add it to handlers
        c_handler.setFormatter(FORMAT_MAIN_LOGGER)
        f_handler.setFormatter(FORMAT_MAIN_LOGGER)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        logger.propagate = False

        return logger
    
    elif type == "sensor":
        
        # Config level
        logging.basicConfig(
            level=logging.DEBUG)  # To log everything, by default it only logs warning and above.

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(SENSOR_ERROR_LOG_FILE)
        c_handler.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.INFO)

        # Create formatters and add it to handlers
        c_handler.setFormatter(FORMAT_SENSOR_LOGGER)
        f_handler.setFormatter(FORMAT_SENSOR_LOGGER)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        logger.propagate = False

        return logger

    elif type == "security_system":
        
        # Config level
        logging.basicConfig(
            level=logging.DEBUG)  # To log everything, by default it only logs warning and above.

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(SECURITY_SYSTEM_LOG_FILE)
        c_handler.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.INFO)

        # Create formatters and add it to handlers
        c_handler.setFormatter(FORMAT_SECURITY_SYSTEM_LOGGER)
        f_handler.setFormatter(FORMAT_SECURITY_SYSTEM_LOGGER)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        logger.propagate = False

        return logger

    else:
        raise Exception("Argument 'type=' is not valid")


# Security Alarm

surveillance_config = {
    "use_dropbox": False,
    "email_alert": True,
    "captures_folder": SURVEILLANCE_CAPTURES_DIR,
    "dropbox_access_token": "YOUR_DROPBOX_ACCESS_TOKEN",
    "dropbox_base_path": "https://www.dropbox.com/home/Apps/rpi_iot_home/home/Apps/rpi_iot_home",
    "min_upload_seconds": 3.0,
    "min_email_seconds": 30.0,
    "max_images_email": 5,
    "min_motion_frames": 8,
    "camera_warmup_time": 2,
    "delta_thresh": 5,
    "resolution": [640, 480],
    "fps": 16,
    "min_area": 5000
}

# Email Notifications
FROM_ADDR = 'joaquin.raspberry.pi.1@gmail.com'
PASSWORD = 'password'  # TODO: replace with the real password
TO_ADDR = 'joakin9408@gmail.com'
SMTP_SERVER = 'Smtp.gmail.com:587'


# Chart 1
CHART_SETTINGS_1 = {
    'chart_name': 'sensor_chart',
    'features': ['off-chip temperature', 'onboard humidity'],
    'time_range': None,
    'y_axis': [0, 45],
    'format': {
        'off-chip temperature': {
            'mode': 'lines',
            'line': dict(dash='solid', color='red'),
            'name': 'temp'
        },
        'onboard humidity': {
            'mode': 'lines',
            'line': dict(dash='dot', color='royalblue'),
            'name': 'humidity'
        }
    }
}