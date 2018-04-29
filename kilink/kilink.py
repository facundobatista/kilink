# Copyright 2011-2017 Facundo Batista
# All Rights Reserved

"""The server for kilink."""

import logging

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    make_response
)

from flask_babel import Babel
from flask_cors import CORS
from sqlalchemy import create_engine

import backend
import loghelper

from config import config, LANGUAGES
from decorators import measure
from metrics import StatsdClient


# logger
logger = logging.getLogger('kilink.kilink')

# metrics
metrics = StatsdClient("linkode")


# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'
app.config["PROPAGATE_EXCEPTIONS"] = False

babel = Babel(app)
cors = CORS(app)


@app.errorhandler(backend.KilinkNotFoundError)
def handle_not_found_error(error):
    """Return 404 on kilink not found"""
    logger.debug(error.message)
    return jsonify({'message': error.message}), 404


@app.errorhandler(backend.KilinkDataTooBigError)
def handle_content_data_too_big_error(error):
    """Return 413 on content data too big"""
    logger.debug(error.message)
    return jsonify({'message': error.message}), 413


@babel.localeselector
def get_locale():
    """Return the best matched language supported."""
    return request.accept_languages.best_match(LANGUAGES.keys())


# accesory pages
@app.route('/about')
@measure("about", metrics)
def about():
    """Show the about page."""
    return render_template('_about.html')


@app.route('/tools')
@measure("tools", metrics)
def tools():
    """Show the tools page."""
    return render_template('_tools.html')


@app.route('/version')
@measure("version", metrics)
def version():
    """Show the project version, very simple, just for developers/admin help."""
    return kilinkbackend.get_version()


# views
@app.route('/')
@app.route('/<linkode_id>')
@app.route('/<linkode_id>/<revno>')
@app.route('/l/<linkode_id>')
@app.route('/l/<linkode_id>/<revno>')
@measure("index", metrics)
def index(linkode_id=None, revno=None):
    """The base page."""
    return render_template('_new.html')


# API
@app.route('/api/1/linkodes/', methods=['POST'])
@measure("api.create", metrics)
def api_create():
    """Create a kilink."""
    content = request.form['content']
    text_type = request.form.get('text_type', "")
    logger.debug("API create start; type=%r size=%d", text_type, len(content))
    try:
        klnk = kilinkbackend.create_kilink(content, text_type)
    except backend.KilinkDataTooBigError:
        logger.debug("Content data too big; on creation")
        response = make_response()
        return response, 413
    ret_json = jsonify(linkode_id=klnk.linkode_id, revno=klnk.linkode_id)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s' % (config["server_host"], klnk.linkode_id)
    logger.debug("API create done; linkode_id=%s", klnk.linkode_id)
    return response, 201


@app.route('/api/1/linkodes/<linkode_id>', methods=['POST'])
@measure("api.update", metrics)
def api_update(linkode_id):
    """Update a kilink."""
    content = request.form['content']
    parent = request.form['parent']
    text_type = request.form['text_type']
    logger.debug("API update start; linkode_id=%r parent=%r type=%r size=%d",
                 linkode_id, parent, text_type, len(content))
    try:
        klnk = kilinkbackend.update_kilink(parent, content, text_type)
    except backend.KilinkNotFoundError:
        logger.debug("API update done; linkode_id %r not found", linkode_id)
        response = make_response()
        return response, 404
    except backend.KilinkDataTooBigError:
        logger.debug("Content data too big.; linkode_id %r", linkode_id)
        response = make_response()
        return response, 413

    logger.debug("API update done; linkode_id=%r", klnk.linkode_id)
    ret_json = jsonify(revno=klnk.linkode_id)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s' % (config["server_host"], klnk.linkode_id)
    return response, 201


@app.route('/api/1/linkodes/<linkode_id>/<revno>', methods=['GET'])
@app.route('/api/1/linkodes/<linkode_id>', methods=['GET'])
@measure("api.get", metrics)
def api_get(linkode_id, revno=None):
    """Get the kilink and revno content"""
    logger.debug("API get; linkode_id=%r revno=%r", linkode_id, revno)
    if revno is not None:
        # the linkode_id to get the info from is the second token
        linkode_id = revno

    klnk = kilinkbackend.get_kilink(linkode_id)

    # get the tree
    tree, nodeq = kilinkbackend.build_tree(linkode_id)

    logger.debug("API get done; type=%r size=%d len_tree=%d",
                 klnk.text_type, len(klnk.content), nodeq)
    ret_json = jsonify(content=klnk.content, text_type=klnk.text_type,
                       tree=tree, timestamp=klnk.timestamp)
    return ret_json


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
    kilinkbackend = backend.KilinkBackend(engine)
    app.run(debug=True, host='0.0.0.0')
