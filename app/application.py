
from flask import Flask
from flask_basicauth import BasicAuth
import logging

from app.logger import set_logger

logger = logging.getLogger(__name__)
logger = set_logger(logger)


def create_app():
    """Create a flask app instance."""

    flask_app = Flask('app')
    #flask_app.config.from_object(config_object) # TODO

    flask_app.config['BASIC_AUTH_FORCE'] = True
    flask_app.config['SECRET_KEY'] = "powerful secret key"

    # Basic Authentication ("Sign in" security to have access to the app)
    basic_auth = BasicAuth(flask_app)

    flask_app.config['BASIC_AUTH_USERNAME'] = 'joaquin'
    flask_app.config['BASIC_AUTH_PASSWORD'] = 'qwerty'

    # import blueprints
    from app.controller import app
    flask_app.register_blueprint(app)
    logger.info('Application instance created')

    return flask_app