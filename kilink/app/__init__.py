import logging

from flask import Flask, request
from flask_babel import Babel
from flask_cors import CORS

from sqlalchemy import create_engine

from kilink.app.config import config, LANGUAGES
from kilink.app import backend, loghelper

# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'
app.config["PROPAGATE_EXCEPTIONS"] = False

app.babel = Babel(app)
app.cors = CORS(app)

# load config
config.load_file("configs/development.yaml")

# log setup
handlers = loghelper.setup_logging(config['log_directory'], verbose=True)
for h in handlers:
    app.logger.addHandler(h)
    h.setLevel(logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# set up the backend
engine = create_engine(config["db_engine"], echo=True)
kilinkbackend = backend.KilinkBackend(engine)


from kilink.app import linkode


@app.babel.localeselector
def get_locale():
    """Return the best matched language supported."""
    return request.accept_languages.best_match(LANGUAGES.keys())
