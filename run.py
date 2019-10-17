from app.application import create_app
from app.config.config import DevelopmentConfig, ProductionConfig


application = create_app(
    config_object=DevelopmentConfig)


if __name__ == '__main__':
    application.run(threaded=True, use_reloader=True)