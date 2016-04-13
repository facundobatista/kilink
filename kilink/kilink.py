# Copyright 2011-2016 Facundo Batista
# All Rigths Reserved

"""The server for kilink."""

import logging

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)

from flask.ext.assets import Environment
# from flask_assets import Environment
from flask_babel import Babel
# from flask_babel import gettext as _
from sqlalchemy import create_engine

import backend
import loghelper

from config import config, LANGUAGES

from webclient.webclient import webclient
from api.api import api
# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'
app.config["PROPAGATE_EXCEPTIONS"] = False

app.register_blueprint(webclient)
app.register_blueprint(api)

babel = Babel(app)

# flask-assets
assets = Environment(app)
assets.cache = "/tmp/"
assets.init_app(app)

# logger
logger = logging.getLogger('kilink.kilink')


@app.errorhandler(backend.KilinkNotFoundError)
def handle_not_found_error(error):
    """Return 404 on kilink not found"""
    if request.url_rule.endpoint.startswith('api_'):
        response = jsonify({'message': error.message})
    else:
        response = render_template('_404.html')

    logger.debug(error.message)
    return response, 404


@babel.localeselector
def get_locale():
    """Return the best matched language supported."""
    return request.accept_languages.best_match(LANGUAGES.keys())


if __name__ == "__main__":
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
    app.kilinkbackend = backend.KilinkBackend(engine)
    app.kilinkNotFoundError = backend.KilinkNotFoundError
    app.run(debug=True, host='0.0.0.0')
