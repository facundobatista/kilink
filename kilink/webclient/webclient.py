# Copyright 2011-2016 Facundo Batista
# All Rigths Reserved

"""The Web Client for kilink."""

import json
import logging

from flask import (
    redirect,
    render_template,
    request,
    Blueprint,
    current_app
)

from decorators import measure, nocache

import api

webclient = Blueprint('webclient', __name__,
                      template_folder="templates")
logger = logging.getLogger('kilink.kilink')


@webclient.route('/about')
@measure("about")
def about():
    """Show the about page."""
    return render_template('_about.html')


@webclient.route('/tools')
@measure("tools")
def tools():
    """Show the tools page."""
    return render_template('_tools.html')


@webclient.route('/version')
@measure("version")
def version():
    """Show the project version, very very simple,
     just for developers/admin help."""
    return current_app.kilinkbackend.get_version()


# views
@webclient.route('/')
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


@webclient.route('/', methods=['POST'])
@measure("server.create")
def create():
    """Create a kilink."""
    content = request.form['content']
    text_type = request.form['text_type']
    logger.debug("Create start; type=%r size=%d", text_type, len(content))
    if text_type[:6] == "auto: ":
        text_type = text_type[6:]
    klnk = current_app.kilinkbackend.create_kilink(content, text_type)
    url = "/%s" % (klnk.kid,)
    logger.debug("Create done; kid=%s", klnk.kid)
    return redirect(url, code=303)


@webclient.route('/<kid>', methods=['POST'])
@webclient.route('/<kid>/<parent>', methods=['POST'])
@measure("server.update")
def update(kid, parent=None):
    """Update a kilink."""
    content = request.form['content']
    text_type = request.form['text_type']
    logger.debug("Update start; kid=%r parent=%r type=%r size=%d",
                 kid, parent, text_type, len(content))
    if parent is None:
        root = current_app.kilinkbackend.get_root_node(kid)
        parent = root.revno

    klnk = current_app.kilinkbackend.update_kilink(kid,
                                                   parent, content,
                                                   text_type)
    new_url = "/%s/%s" % (kid, klnk.revno)
    logger.debug("Update done; kid=%r revno=%r", klnk.kid, klnk.revno)
    return redirect(new_url, code=303)


@webclient.route('/<kid>')
@webclient.route('/<kid>/<revno>')
@webclient.route('/l/<kid>')
@webclient.route('/l/<kid>/<revno>')
@nocache
@measure("server.show")
def show(kid, revno=None):
    """Show the kilink content"""
    # get the content
    logger.debug("Show start; kid=%r revno=%r", kid, revno)
    # if revno is None:
    #     klnk = current_app.kilinkbackend.get_root_node(kid)
    #     revno = klnk.revno
    # else:
    #     klnk = current_app.kilinkbackend.get_kilink(kid, revno)
    # content = klnk.content
    # text_type = klnk.text_type
    # timestamp = klnk.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    # # get the tree
    # tree, nodeq = current_app.kilinkbackend.build_tree(kid, revno)

    render_dict = api.api.api_get(kid, revno).original

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
