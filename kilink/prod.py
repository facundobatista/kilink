"""Run service in production."""

from kilink import main, loghelper
from kilink.config import config


config.load_config()
loghelper.setup_logging(main.app.logger)
application = main.app
