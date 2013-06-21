# -*- coding: utf-8 -*-

# all the imports
from flask import Flask, request, session, g, redirect, url_for,\
    abort, render_template, flash

import backend
import tools


app = Flask(__name__)
app.config.from_object(__name__)

kilinkbackend = backend.KilinkBackend()


# Vistas
@app.route('/')
def home():

    render_dict = {
        'value': '',
        'button_text': 'Create kilink',
        'user_action': 'create',
        'tree_info': None,
    }

    return render_template('index.html', **render_dict)


@app.route('/action/create', methods=['POST'])
def create():
    """Create a kilink."""
    content = request.form['content']
    kid = kilinkbackend.create_kilink(content)
    return redirect('/k/' + kid, code=303)


@app.route('/action/edit', methods=['POST'])
def edit():
    """Edit a kilink."""
    content = request.form['content']
    kid = request.args['kid']
    parent = int(request.args['parent'])
    new_revno = kilinkbackend.update_kilink(kid, parent, content)
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
    # tree info
    tree_info = []
    for revno, _, parent, tstamp in kilinkbackend.get_kilink_tree(kid):
        url = "/%s?revno=%s" % (kid, revno)
        if parent is None:
            parent = "-1"
            tree_info.append((parent, revno, url, tstamp))

    render_dict = {
        'value': content,
        'button_text': 'Save new version',
        'user_action': action_url,
        'tree_info': tree_info,
        'current_revno': current_revno,
    }
    return render_template('index.html', **render_dict)





if __name__ == "__main__":
    app.run()
