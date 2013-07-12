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

from decorators import crossdomain

# set up flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'


# views
@app.route('/')
def index():
    """The base page."""
    render_dict = {
        'value': '',
        'button_text': 'Create kilink',
        'user_action': 'create',
        'tree_info': [],
    }
    return render_template('_new.html', **render_dict)

@app.route('/about')
def about():
    return render_template('_about.html')


@app.route('/action/create', methods=['POST'])
def create():
    """Create a kilink."""
    content = request.form['content']
    klnk = kilinkbackend.create_kilink(content)
    url = "/k/%s?revno=%s" % (klnk.kid, klnk.revno)
    return redirect(url, code=303)


@app.route('/action/edit', methods=['POST'])
def edit():
    """Edit a kilink."""
    content = request.form['content']
    kid = request.args['kid']
    parent = request.args['parent']
    klnk = kilinkbackend.update_kilink(kid, parent, content)
    new_url = "/k/%s?revno=%s" % (kid, klnk.revno)
    return redirect(new_url, code=303)


@app.route('/k/<path:path>')
def show(path):
    """Show the kilink content"""
    kid = path
    current_revno = request.args['revno']

    # content
    action_url = 'edit?kid=%s&parent=%s' % (kid, current_revno)
    content = kilinkbackend.get_content(kid, current_revno)
    # tree info
    tree_info = []
    for treenode in kilinkbackend.get_kilink_tree(kid):
        url = "/k/%s?revno=%s" % (kid, treenode.revno)
        parent = treenode.parent
        if parent is None:
            parent = -1
        tree_info.append((treenode.order, parent, treenode.revno,
                         url, str(treenode.timestamp)))

    render_dict = {
        'value': content,
        'button_text': 'Save new version',
        'user_action': action_url,
        'tree_info': json.dumps(tree_info) if tree_info else [],
        'current_revno': current_revno,
    }
    return render_template('_new.html', **render_dict)


#API
# Estamos usando crossdomain porque si no, desde JS no podemos
# postear.Deberiamos pedir ayuda a un JS Ninja
@app.route('/api/1/kilinks', methods=['POST'])
@crossdomain(origin='*')
def api_create():
    """Create a kilink."""
    content = request.form['content']
    klnk = kilinkbackend.create_kilink(content)
    ret_json = jsonify(kilink_id=klnk.kid, revno=klnk.revno)
    response = make_response(ret_json)
    # FIXME: Esto va en un archivo de configuracion
    response.headers['Location'] = 'http://kilink.com.ar/%s/%s' % (
        klnk.kid, klnk.revno)
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
    # FIXME: Esto va en un archivo de configuracion
    response.headers['Location'] = 'http://kilink.com.ar/%s/%s' % (
        klnk.kid, klnk.revno)
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
    # set up the backend
    engine = create_engine('sqlite:////tmp/kilink.db')
    kilinkbackend = backend.KilinkBackend(engine)
    app.run(debug=True, host='0.0.0.0')
