import os
import sys

sys.path.insert(0, '/home/kilink/.virtualenvs/kilink/lib/python3.8/site-packages')
sys.path.insert(0, "/home/kilink/project/production/")

from kilink import backend, main, loghelper
from sqlalchemy import create_engine
from kilink.config import config 

config.load_config()
loghelper.setup_logging(kilink.app.logger)

# get config data
auth_config = config["db_auth_config"]
auth_file = os.path.abspath(os.path.join(os.path.dirname(__file__), auth_config))
with open(auth_file) as fh:
    vals = [x.strip() for x in fh.readlines()]
auth_data = dict(zip(("user", "pass"), vals))
engine_data = config["db_engine"].format(**auth_data)

# set up the backend
engine = create_engine(engine_data)
main.kilinkbackend = backend.KilinkBackend(engine)

application = main.app


