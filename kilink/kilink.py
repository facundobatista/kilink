"""The server and main app for kilink."""

import json

from flask import (
    Flask,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
)
from sqlalchemy import create_engine

import backend

from config import config
from decorators import crossdomain

# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'


# accesory pages
@app.route('/about')
def about():
    """Show the about page."""
    return render_template('_about.html')


# views
@app.route('/')
def index():
    """The base page."""
    render_dict = {
        'value': '',
        'button_text': 'Create kilink',
        'kid_info': 'k/',
        'tree_info': [],
    }
    return render_template('_new.html', **render_dict)


@app.route('/k/', methods=['POST'])
def create():
    """Create a kilink."""
    content = request.form['content']
    klnk = kilinkbackend.create_kilink(content)
    url = "/k/%s" % (klnk.kid,)
    return redirect(url, code=303)


@app.route('/k/<kid>', methods=['POST'])
@app.route('/k/<kid>/<parent>', methods=['POST'])
def update(kid, parent=None):
    """Update a kilink."""
    if parent is None:
        root = kilinkbackend.get_root_node(kid)
        parent = root.revno

    content = request.form['content']
    klnk = kilinkbackend.update_kilink(kid, parent, content)
    new_url = "/k/%s/%s" % (kid, klnk.revno)
    return redirect(new_url, code=303)


@app.route('/k/<kid>')
@app.route('/k/<kid>/<revno>')
def show(kid, revno=None):
    """Show the kilink content"""
    # get the content
    if revno is None:
        root = kilinkbackend.get_root_node(kid)
        revno = root.revno
        content = root.content
    else:
        content = kilinkbackend.get_content(kid, revno)

    # tree info
    tree_info = []
    for treenode in kilinkbackend.get_kilink_tree(kid):
        url = "/k/%s/%s" % (kid, treenode.revno)
        parent = treenode.parent
        if parent is None:
            parent = -1
        tree_info.append((treenode.order, parent, treenode.revno,
                         url, str(treenode.timestamp)))

    render_dict = {
        'value': content,
        'button_text': 'Save new version',
        'kid_info': "k/%s/%s" % (kid, revno),
        'tree_info': json.dumps(tree_info) if tree_info else [],
        'current_revno': revno,
    }
    return render_template('_new.html', **render_dict)


#API
@app.route('/api/1/kilinks', methods=['POST'])
@crossdomain(origin='*')
def api_create():
    """Create a kilink."""
    content = request.form['content']
    klnk = kilinkbackend.create_kilink(content)
    ret_json = jsonify(kilink_id=klnk.kid, revno=klnk.revno)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s/%s' % (
        config["server_host"], klnk.kid, klnk.revno)
    return response, 201


@app.route('/api/1/kilinks/<kid>', methods=['POST'])
@crossdomain(origin='*')
def api_update(kid):
    """Update a kilink."""
    content = request.form['content']
    parent = request.form['parent']
    try:
        klnk = kilinkbackend.update_kilink(kid, parent, content)
    except backend.KilinkNotFoundError:
        response = make_response()
        return response, 404

    ret_json = jsonify(revno=klnk.revno)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s/%s' % (
        config["server_host"], klnk.kid, klnk.revno)
    return response, 201


@app.route('/api/1/kilinks/<kid>/<revno>', methods=['GET'])
@crossdomain(origin='*')
def api_get(kid, revno):
    """Get the kilink and revno content"""
    try:
        content = kilinkbackend.get_content(kid, revno)
        ret_json = jsonify(content=content)
        return ret_json
    except backend.KilinkNotFoundError:
        response = make_response()
        return response, 404

if __name__ == "__main__":
    # load config
    config.load_file("configs/development.yaml")

    # set up the backend
    engine = create_engine(config["db_engine"])
    kilinkbackend = backend.KilinkBackend(engine)
    app.run(debug=True, host='0.0.0.0')
