# Copyright 2011-2013 Facundo Batista
# All Rigths Reserved

"""The server and main app for kilink."""

import json
import logging
import time

from functools import update_wrapper

from flask import (
    Flask,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
)

from flask_assets import Environment
from flask_babel import Babel
from flask_babel import gettext as _
from sqlalchemy import create_engine

import backend
import loghelper

from config import config, LANGUAGES
from decorators import crossdomain
from metrics import StatsdClient

# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'
app.config["PROPAGATE_EXCEPTIONS"] = False
babel = Babel(app)

# flask-assets
assets = Environment(app)
assets.init_app(app)

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
            except Exception, exc:
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


# views
@app.route('/')
@measure("index")
def index():
    """The base page."""
    logger.debug(config["max_chars"], config["max_lines"])
    render_dict = {
        'value': '',
        'button_text': _('Create linkode'),
        'kid_info': '',
        'tree_info': json.dumps(False),
        'max_chars': config['max_chars'],
        'max_lines': config['max_lines'],
    }
    return render_template('_new.html', **render_dict)


@app.route('/', methods=['POST'])
@measure("server.create")
def create():
    """Create a kilink."""
    content = request.form['content']
    text_type = request.form['text_type']
    logger.debug("Create start; type=%r size=%d", text_type, len(content))
    if text_type[:6] == "auto: ":
        text_type = text_type[6:]
    klnk = kilinkbackend.create_kilink(content, text_type)
    url = "/%s" % (klnk.kid,)
    logger.debug("Create done; kid=%s", klnk.kid)
    return redirect(url, code=303)


@app.route('/<kid>', methods=['POST'])
@app.route('/<kid>/<parent>', methods=['POST'])
@measure("server.update")
def update(kid, parent=None):
    """Update a kilink."""
    content = request.form['content']
    text_type = request.form['text_type']
    logger.debug("Update start; kid=%r parent=%r type=%r size=%d",
                 kid, parent, text_type, len(content))
    if parent is None:
        root = kilinkbackend.get_root_node(kid)
        parent = root.revno

    klnk = kilinkbackend.update_kilink(kid, parent, content, text_type)
    new_url = "/%s/%s" % (kid, klnk.revno)
    logger.debug("Update done; kid=%r revno=%r", klnk.kid, klnk.revno)
    return redirect(new_url, code=303)


@app.route('/<kid>')
@app.route('/<kid>/<revno>')
@app.route('/l/<kid>')
@app.route('/l/<kid>/<revno>')
@nocache
@measure("server.show")
def show(kid, revno=None):
    """Show the kilink content"""
    # get the content
    logger.debug("Show start; kid=%r revno=%r", kid, revno)
    if revno is None:
        klnk = kilinkbackend.get_root_node(kid)
        revno = klnk.revno
    else:
        klnk = kilinkbackend.get_kilink(kid, revno)
    content = klnk.content
    text_type = klnk.text_type

    # get the tree
    tree, nodeq = build_tree(kid, revno)

    render_dict = {
        'value': content,
        'button_text': _('Save new version'),
        'kid_info': "%s/%s" % (kid, revno),
        'tree_info': json.dumps(tree) if tree != {} else False,
        'current_revno': revno,
        'text_type': text_type,
        'max_chars': config['max_chars'],
        'max_lines': config['max_lines'],
    }
    logger.debug("Show done; quantity=%d", nodeq)
    return render_template('_new.html', **render_dict)


def build_tree(kid, revno):
    """Build the tree for a given kilink id."""
    nodes = []
    for treenode in kilinkbackend.get_kilink_tree(kid):
        url = "/%s/%s" % (kid, treenode.revno)
        parent = treenode.parent
        nodes.append({
            'order': treenode.order,
            'parent': parent,
            'revno': treenode.revno,
            'url': url,
            'timestamp': str(treenode.timestamp),
            'selected': treenode.revno == revno,
        })

    root = [n for n in nodes if n['parent'] is None][0]
    fringe = [root, ]

    while fringe:
        node = fringe.pop()
        children = [n for n in nodes if n['parent'] == node['revno']]

        node['contents'] = children
        fringe.extend(children)

    return root, len(nodes)


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
    ret_json = jsonify(linkode_id=klnk.kid, revno=klnk.revno)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s/%s' % (
        config["server_host"], klnk.kid, klnk.revno)
    logger.debug("API create done; kid=%s", klnk.kid)
    return response, 201


@app.route('/api/1/linkodes/<kid>', methods=['POST'])
@crossdomain(origin='*')
@measure("api.update")
def api_update(kid):
    """Update a kilink."""
    content = request.form['content']
    parent = request.form['parent']
    text_type = request.form['text_type']
    logger.debug("API update start; kid=%r parent=%r type=%r size=%d",
                 kid, parent, text_type, len(content))
    try:
        klnk = kilinkbackend.update_kilink(kid, parent, content, text_type)
    except backend.KilinkNotFoundError:
        logger.debug("API update done; kid %r not found", kid)
        response = make_response()
        return response, 404

    logger.debug("API update done; kid=%r revno=%r", klnk.kid, klnk.revno)
    ret_json = jsonify(revno=klnk.revno)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s/%s' % (
        config["server_host"], klnk.kid, klnk.revno)
    return response, 201


@app.route('/api/1/linkodes/<kid>/<revno>', methods=['GET'])
@app.route('/api/1/linkodes/<kid>', methods=['GET'])
@crossdomain(origin='*')
@measure("api.get")
def api_get(kid, revno=None):
    """Get the kilink and revno content"""
    logger.debug("API get; kid=%r revno=%r", kid, revno)
    if revno is None:
        klnk = kilinkbackend.get_root_node(kid)
        revno = klnk.revno
    else:
        klnk = kilinkbackend.get_kilink(kid, revno)

    # get the tree
    tree, nodeq = build_tree(kid, revno)

    logger.debug("API get done; type=%r size=%d len_tree=%d",
                 klnk.text_type, len(klnk.content), nodeq)
    ret_json = jsonify(content=klnk.content, text_type=klnk.text_type,
                       tree=tree)
    return ret_json


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
    kilinkbackend = backend.KilinkBackend(engine)
    app.run(debug=True, host='0.0.0.0')
