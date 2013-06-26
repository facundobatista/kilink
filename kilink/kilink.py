"""The server and main app for kilink."""

import json

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    jsonify,
)

from pygments import highlight
from pygments.lexers import (
    get_lexer_by_name,
    get_all_lexers,
    )
from pygments.formatters import HtmlFormatter

from decorators import *

from backend import Kilink, KilinkBackend


app = Flask(__name__)
app.config.from_object(__name__)
app.config["STATIC_URL"] = 'static'
app.config["STATIC_ROOT"] = 'static'
kilinkbackend = KilinkBackend()


# Vistas
@app.route('/')
def index():
    """The base page."""
    render_dict = {
        'value': '',
        'button_text': 'Create kilink',
        'user_action': 'create',
        'tree_info': [],
        'languages': get_all_lexers(),
        'latest': kilinkbackend.get_latest_kilinks(5),
    }
    return render_template('index.html', **render_dict)


@app.route('/action/create', methods=['POST'])
def create():
    """Create a kilink."""
    content = request.form['content']
    lang = request.form['lang']
    kid = kilinkbackend.create_kilink(content, lang)
    return redirect('/k/' + kid, code=303)


@app.route('/action/edit', methods=['POST'])
def edit():
    """Edit a kilink."""
    content = request.form['content']
    kid = request.args['kid']
    parent = int(request.args['parent'])
    lang = Kilink.selectBy(kid=kid, revno=parent).getOne()
    lang = lang.lang
    new_revno = kilinkbackend.update_kilink(kid, lang, parent, content)
    new_url = "/k/%s?revno=%s" % (kid, new_revno)
    return redirect(new_url, code=303)


@app.route('/k/<path:path>')
def show(path):
    """Show the kilink content"""
    kid = path
    current_revno = int(request.args.get('revno', 1))

    # content
    action_url = 'edit?kid=%s&parent=%s' % (kid, current_revno)
    content = kilinkbackend.get_content(kid, current_revno)
    lang = Kilink.selectBy(kid=kid, revno=current_revno).getOne()
    lang = get_lexer_by_name(lang.lang)
     # tree info
    tree_info = []
    for revno, _, parent, tstamp in kilinkbackend.get_kilink_tree(kid):
        url = "/k/%s?revno=%s" % (kid, revno)
        if parent is None:
            parent = -1
        tree_info.append((parent, revno, url, str(tstamp)))

    render_dict = {
        'code': content,
        'rendered_code': highlight(content,
                                      get_lexer_by_name('python'),
                                      HtmlFormatter()),
        'button_text': 'Save new version',
        'user_action': action_url,
        'tree_info': json.dumps(tree_info) if tree_info else [],
        'current_revno': current_revno,
        'language': lang,
    }
    return render_template('index.html', **render_dict)


#API
# Estamos usando crossdomain porque si no, desde JS no podemos
# postear.Deberiamos pedir ayuda a un JS Ninja
@app.route('/api/1/action/create', methods=['POST'])
@crossdomain(origin='*')
def api_create():
    """Create a kilink."""
    content = request.form['content']
    kid = kilinkbackend.create_kilink(content)
    ret_json = jsonify(kilink_id=kid)
    return ret_json


@app.route('/api/1/action/edit', methods=['POST'])
@crossdomain(origin='*')
def api_edit():
    """Edit a kilink."""
    content = request.form['content']
    kid = request.form['kid']
    parent = int(request.form['parent'])
    new_revno = kilinkbackend.update_kilink(kid, parent, content)
    ret_json = jsonify(kilink_id=kid, revno=new_revno)
    return ret_json


@app.route('/api/1/action/get/<kid>/<int:revno>', methods=['GET'])
@app.route('/api/1/action/get', methods=['GET'])
@crossdomain(origin='*')
def api_get(kid=None, revno=None):
    """Get the kilink and revno content"""
    if not kid:
        kid = request.args.get('kid')
        revno = int(request.args.get('revno', 1))

    try:
        content = kilinkbackend.get_content(kid, revno)
        ret_json = jsonify(kilink_id=kid, revno=revno, content=content)
        return ret_json
    except ValueError:
        return "This kilink does not exists"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
