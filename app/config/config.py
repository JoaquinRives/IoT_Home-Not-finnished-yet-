import os
import pathlib

# Path to config file
PATH_CONFIG = pathlib.Path(__file__).resolve().parent

# Path to the app
APP_ROOT = pathlib.Path(PATH_CONFIG).resolve().parent

# Path to data
DATA_DIR = APP_ROOT / 'data'

# Logging file
LOG_FILE = APP_ROOT / 'log_file.log'


# Configuration of the flask app
class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'this-needs-to-be-changed'
    SERVER_PORT = 5000
    BASIC_AUTH_FORCE = True
    BASIC_AUTH_USERNAME = 'joaquin'
    BASIC_AUTH_PASSWORD = 'qwerty'


class ProductionConfig(Config):
    DEBUG = False
    SERVER_ADDRESS: os.environ.get('SERVER_ADDRESS', '0.0.0.0')
    SERVER_PORT: os.environ.get('SERVER_PORT', '5000')


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True