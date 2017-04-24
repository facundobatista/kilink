# Copyright 2011-2017 Facundo Batista
# All Rigths Reserved

"""The server for kilink."""

import logging
import time

from functools import update_wrapper

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    make_response
)

# from flask.ext.assets import Environment
# from flask_assets import Environment
from flask_babel import Babel
from flask_babel import gettext as _
from sqlalchemy import create_engine

import backend
import loghelper

from config import config, LANGUAGES
from metrics import StatsdClient
from decorators import crossdomain

# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'
app.config["PROPAGATE_EXCEPTIONS"] = False

babel = Babel(app)

# flask-assets
# assets = Environment(app)
# assets.cache = "/tmp/"
# assets.init_app(app)

# logger
logger = logging.getLogger('kilink.kilink')

# metrics
metrics = StatsdClient("linkode")


def nocache(f):
    """Decorator to make a page un-cacheable."""
    def new_func(*args, **kwargs):
        """The new function."""
        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = 'public, max-age=0'
        return resp
    return update_wrapper(new_func, f)


def measure(metric_name):
    """Decorator generator to send metrics counting and with timing."""

    def _decorator(oldf):
        """The decorator itself."""

        def newf(*args, **kwargs):
            """The function to replace."""
            tini = time.time()
            try:
                result = oldf(*args, **kwargs)
            except Exception as exc:
                name = "%s.error.%s" % (metric_name, exc.__class__.__name__)
                metrics.count(name, 1)
                raise
            else:
                tdelta = time.time() - tini

                metrics.count(metric_name + '.ok', 1)
                metrics.timing(metric_name, tdelta)
                return result

        # need to fix the name because it's used by flask
        newf.func_name = oldf.func_name
        return newf
    return _decorator


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


# accesory pages
@app.route('/about')
@measure("about")
def about():
    """Show the about page."""
    return render_template('_about.html')


@app.route('/tools')
@measure("tools")
def tools():
    """Show the tools page."""
    return render_template('_tools.html')


@app.route('/version')
@measure("version")
def version():
    """Show the project version, very very simple, just for developers/admin help."""
    return kilinkbackend.get_version()


# views
@app.route('/')
@measure("index")
def index():
    """The base page."""
    render_dict = {
        'new_button_text': _('Create linkode'),
        'update_button_text': _('Save new version'),
    }
    return render_template('_new.html', **render_dict)


# API
@app.route('/api/1/linkodes/', methods=['POST'])
@crossdomain(origin='*')
@measure("api.create")
def api_create():
    """Create a kilink."""
    content = request.form['content']
    text_type = request.form.get('text_type', "")
    logger.debug("API create start; type=%r size=%d", text_type, len(content))
    klnk = kilinkbackend.create_kilink(content, text_type)
    ret_json = jsonify(linkode_id=klnk.linkode_id, revno=klnk.linkode_id)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s' % (config["server_host"], klnk.linkode_id)
    logger.debug("API create done; linkode_id=%s", klnk.linkode_id)
    return response, 201


@app.route('/api/1/linkodes/<linkode_id>', methods=['POST'])
@crossdomain(origin='*')
@measure("api.update")
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

    logger.debug("API update done; linkode_id=%r", klnk.linkode_id)
    ret_json = jsonify(revno=klnk.linkode_id)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s' % (config["server_host"], klnk.linkode_id)
    return response, 201


@app.route('/api/1/linkodes/<linkode_id>/<revno>', methods=['GET'])
@app.route('/api/1/linkodes/<linkode_id>', methods=['GET'])
@crossdomain(origin='*')
@measure("api.get")
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
