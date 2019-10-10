from flask import Flask
from flask_basicauth import BasicAuth
import logging
from app.config.config import config_logger

logger = logging.getLogger(__name__)
logger = config_logger(logger)


def create_app(*, config_object):
    """Create a flask app instance."""

    flask_app = Flask('app')
    flask_app.config.from_object(config_object)

    # Basic Authentication ("Sign in" security to have access to the app)
    basic_auth = BasicAuth(flask_app)


    # import blueprints
    from app.controller import app
    flask_app.register_blueprint(app)
    logger.info('Application instance created')

    return flask_app