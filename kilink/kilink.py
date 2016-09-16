# Copyright 2011-2016 Facundo Batista
# All Rigths Reserved

"""The server for kilink."""

import logging
import json

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
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
from decorators import crossdomain, measure, json_return, nocache

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
        klnk = kilinkbackend.update_kilink(kid,
                                           parent, content,
                                           text_type)
    except kilinkbackend.kilinkNotFoundError:
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
@json_return
def api_get(kid, revno=None):
    """Get the kilink and revno content"""
    logger.debug("API get; kid=%r revno=%r", kid, revno)
    if revno is None:
        klnk = kilinkbackend.get_root_node(kid)
        revno = klnk.revno
    else:
        klnk = kilinkbackend.get_kilink(kid, revno)

    content = klnk.content
    text_type = klnk.text_type
    timestamp = klnk.timestamp

    # get the tree
    tree, nodeq = kilinkbackend.build_tree(kid, revno)

    logger.debug("API get done; type=%r size=%d len_tree=%d",
                 text_type, len(content), nodeq)

    ret_dict = {
        'content': content,
        'text_type': text_type,
        'tree': tree,
        'nodeq': nodeq,
        'timestamp': timestamp,
        'kid_info': "%s/%s" % (kid, revno)
    }

    return ret_dict
    # ret_json = jsonify(content=content,
    #                    text_type=text_type,
    #                    tree=tree,
    #                    timestamp=timestamp,
    #                    kid_info="%s/%s" % (kid, revno))
    # return ret_json


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
    """Show the project version, very very simple,
     just for developers/admin help."""
    return kilinkbackend.get_version()


# views
@app.route('/')
@measure("index")
def index():
    """The base page."""
    render_dict = {
        'value': '',
        'button_text': ('Create linkode'),
        'kid_info': '',
        'tree_info': json.dumps(False),
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

    klnk = kilinkbackend.update_kilink(kid,
                                       parent, content,
                                       text_type)
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
    # if revno is None:
    #     klnk = backend.get_root_node(kid)
    #     revno = klnk.revno
    # else:
    #     klnk = backend.get_kilink(kid, revno)
    # content = klnk.content
    # text_type = klnk.text_type
    # timestamp = klnk.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    # # get the tree
    # tree, nodeq = backend.build_tree(kid, revno)

    render_dict = api_get(kid, revno).original

    render_dict['tree_info'] = json.dumps(
        render_dict['tree']) if render_dict['tree'] != {} else False
    render_dict.pop('tree', None)
    render_dict['button_text'] = ('Save new version')
    render_dict['current_revno'] = revno
    # render_dict = {
    #     'value': content,
    #     'button_text': ('Save new version'),
    #     'kid_info': "%s/%s" % (kid, revno),
    #     'tree_info': json.dumps(tree) if tree != {} else False,
    #     'current_revno': revno,
    #     'text_type': text_type,
    #     'timestamp': timestamp,
    # }
    logger.debug("Show done; quantity=%d", render_dict['nodeq'])
    return render_template('_new.html', **render_dict)


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
    app.kilinkbackend = kilinkbackend
    app.run(debug=True, host='0.0.0.0')
