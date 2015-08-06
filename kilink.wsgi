import os
import sys

activate_this = '/home/kilink/.virtualenvs/kilink/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0, "/home/kilink/project/production/")
sys.path.insert(0, "/home/kilink/project/production/kilink/")

import backend
import kilink
import loghelper
from sqlalchemy import create_engine
from config import config

config.load()

# log setup
handlers = loghelper.setup_logging(config['log_directory'])
for h in handlers:
    kilink.app.logger.addHandler(h)

# set up the backend
engine = create_engine(config["db_engine"])
kilink.kilinkbackend = backend.KilinkBackend(engine)

application = kilink.app
