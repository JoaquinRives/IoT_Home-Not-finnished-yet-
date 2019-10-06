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
