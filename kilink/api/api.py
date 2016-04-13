# Copyright 2011-2016 Facundo Batista
# All Rigths Reserved

"""The API for kilink."""

import logging

from flask import (
    jsonify,
    make_response,
    request,
    Blueprint,
    current_app
)

from decorators import crossdomain, measure

api = Blueprint('api', __name__)
logger = logging.getLogger('kilink.kilink')


@api.route('/api/1/linkodes/', methods=['POST'])
@crossdomain(origin='*')
@measure("api.create")
def api_create():
    """Create a kilink."""
    content = request.form['content']
    text_type = request.form.get('text_type', "")
    logger.debug("API create start; type=%r size=%d", text_type, len(content))
    klnk = current_app.kilinkbackend.create_kilink(content, text_type)
    ret_json = jsonify(linkode_id=klnk.kid, revno=klnk.revno)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s/%s' % (
        current_app.config["server_host"], klnk.kid, klnk.revno)
    logger.debug("API create done; kid=%s", klnk.kid)
    return response, 201


@api.route('/api/1/linkodes/<kid>', methods=['POST'])
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
        klnk = current_app.kilinkbackend.update_kilink(kid,
                                                       parent, content,
                                                       text_type)
    except current_app.kilinkNotFoundError:
        logger.debug("API update done; kid %r not found", kid)
        response = make_response()
        return response, 404

    logger.debug("API update done; kid=%r revno=%r", klnk.kid, klnk.revno)
    ret_json = jsonify(revno=klnk.revno)
    response = make_response(ret_json)
    response.headers['Location'] = 'http://%s/%s/%s' % (
        current_app.config["server_host"], klnk.kid, klnk.revno)
    return response, 201


@api.route('/api/1/linkodes/<kid>/<revno>', methods=['GET'])
@api.route('/api/1/linkodes/<kid>', methods=['GET'])
@crossdomain(origin='*')
@measure("api.get")
def api_get(kid, revno=None):
    """Get the kilink and revno content"""
    logger.debug("API get; kid=%r revno=%r", kid, revno)
    if revno is None:
        klnk = current_app.kilinkbackend.get_root_node(kid)
        revno = klnk.revno
    else:
        klnk = current_app.kilinkbackend.get_kilink(kid, revno)

    # get the tree
    tree, nodeq = current_app.kilinkbackend.build_tree(kid, revno)

    logger.debug("API get done; type=%r size=%d len_tree=%d",
                 klnk.text_type, len(klnk.content), nodeq)
    ret_json = jsonify(content=klnk.content, text_type=klnk.text_type,
                       tree=tree)
    return ret_json

