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
        'button_text': 'Create linkode',
        'kid_info': 'l/',
        'tree_info': json.dumps(False),
    }
    return render_template('_new.html', **render_dict)


@app.route('/l/', methods=['POST'])
def create():
    """Create a kilink."""
    content = request.form['content']
    klnk = kilinkbackend.create_kilink(content)
    url = "/l/%s" % (klnk.kid,)
    return redirect(url, code=303)


@app.route('/l/<kid>', methods=['POST'])
@app.route('/l/<kid>/<parent>', methods=['POST'])
def update(kid, parent=None):
    """Update a kilink."""
    if parent is None:
        root = kilinkbackend.get_root_node(kid)
        parent = root.revno

    content = request.form['content']
    klnk = kilinkbackend.update_kilink(kid, parent, content)
    new_url = "/l/%s/%s" % (kid, klnk.revno)
    return redirect(new_url, code=303)


@app.route('/l/<kid>')
@app.route('/l/<kid>/<revno>')
def show(kid, revno=None):
    """Show the kilink content"""
    # get the content
    if revno is None:
        root = kilinkbackend.get_root_node(kid)
        revno = root.revno
        content = root.content
    else:
        content = kilinkbackend.get_content(kid, revno)

    # node list
    node_list = []
    for treenode in kilinkbackend.get_kilink_tree(kid):
        url = "/l/%s/%s" % (kid, treenode.revno)
        parent = treenode.parent
        node_list.append({
            'order': treenode.order,
            'parent': parent,
            'revno': treenode.revno,
            'url': url,
            'timestamp': str(treenode.timestamp),
            'selected': treenode.revno == revno,
        })

    tree = {}
    build_tree(tree, {}, node_list)

    render_dict = {
        'value': content,
        'button_text': 'Save new version',
        'kid_info': "l/%s/%s" % (kid, revno),
        'tree_info': json.dumps(tree) if tree != {} else False,
        'current_revno': revno,
    }
    return render_template('_new.html', **render_dict)


def build_tree(tree, parent, nodes):
    """ Build tree for 3djs """

    children = [
        n for n in nodes
        if n.get('parent', None) == parent.get('revno', None)
    ]

    for child in children:
        if tree == {}:
            tree['contents'] = []
            tree['order'] = child['order']
            tree['revno'] = child['revno']
            tree['parent'] = child['parent']
            tree['url'] = child['url']
            tree['timestamp'] = child['timestamp']
            tree['selected'] = child['selected']
            new_child = tree
        else:
            new_child = {
                'contents': [],
                'order': child['order'],
                'revno': child['revno'],
                'parent': child['parent'],
                'url': child['url'],
                'timestamp': child['timestamp'],
                'selected': child['selected'],
            }
            tree['contents'].append(new_child)
        build_tree(new_child, child, nodes)


#API
@app.route('/api/1/linkodes', methods=['POST'])
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


@app.route('/api/1/linkodes/<kid>', methods=['POST'])
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


@app.route('/api/1/linkodes/<kid>/<revno>', methods=['GET'])
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
