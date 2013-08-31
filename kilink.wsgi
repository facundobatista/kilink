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

config.load_file("/home/kilink/project/production/configs/production.yaml")

# get config data
auth_config = config["db_auth_config"]
auth_file = os.path.abspath(os.path.join(os.path.dirname(__file__), auth_config))
with open(auth_file) as fh:
    vals = [x.strip() for x in fh.readlines()]
auth_data = dict(zip(("user", "pass"), vals))
engine_data = config["db_engine"].format(**auth_data)

# log setup
loghelper.setup_logging(config['log_directory'])

# set up the backend
engine = create_engine(engine_data)
kilink.kilinkbackend = backend.KilinkBackend(engine)

application = kilink.app
