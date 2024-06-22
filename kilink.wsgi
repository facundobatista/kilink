import sys

sys.path.insert(0, '/home/kilink/.virtualenvs/kilink/lib/python3.8/site-packages')
sys.path.insert(0, "/home/kilink/project/production/")


from kilink import main, loghelper
from kilink.config import config


config.load_config()
loghelper.setup_logging(main.app.logger)
application = main.app
