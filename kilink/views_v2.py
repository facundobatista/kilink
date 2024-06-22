# API
import logging

from flask import Blueprint
from flask import Flask, jsonify, render_template, request, make_response, url_for

from kilink.backend import kilinkbackend, KilinkDataTooBigError, KilinkNotFoundError, LinkodeNotRootNodeError
from kilink.config import config

logger = logging.getLogger(__name__)

linkode_v2 = Blueprint("linkode_v2", __name__)


@linkode_v2.route('/linkode/', methods=['POST'])
@linkode_v2.route('/linkode/<linkode_id>/', methods=['POST'])
def create_linkode(linkode_id=None):
    """Create a linkode."""

    if "content" not in request.json:
        return "missing content", 400

    content = request.json['content']
    text_type = request.json.get('text_type', "")

    logger.debug("API create start; type=%r size=%d", text_type, len(content))
    try:
        linkode = kilinkbackend.create_linkode(content, text_type, linkode_id)

    except KilinkDataTooBigError:
        msg = "Content data too big; on creation"
        logger.debug(msg)
        return msg, 413

    except KilinkNotFoundError:
        msg = f"Linkode_id {linkode_id} not found"
        logger.debug(msg)
        return msg, 404

    ret_json = jsonify(
        linkode_id=linkode.linkode_id,
        linkode_url=url_for("linkode_v2.get_linkode", linkode_id=linkode.linkode_id),
        root_id=linkode.root,
        root_url=url_for("linkode_v2.get_linkode", linkode_id=linkode.root),
    )
    logger.debug("API create done; linkode_id=%s", linkode.linkode_id)
    return ret_json, 201


@linkode_v2.route('/linkode/<linkode_id>', methods=['GET'])
def get_linkode(linkode_id):
    """Get a linkode"""
    try:
        linkode = kilinkbackend.get_kilink(linkode_id)

    except KilinkNotFoundError:
        msg = f"Linkode_id {linkode_id} not found"
        logger.debug(msg)
        return msg, 404

    ret_json = jsonify(
        content=linkode.content,
        text_type=linkode.text_type,
        timestamp=linkode.timestamp,
        linkode_id=linkode.linkode_id,
        linkode_url=url_for("linkode_v2.get_linkode", linkode_id=linkode.linkode_id),
        root_id=linkode.root,
        root_url=url_for("linkode_v2.get_linkode", linkode_id=linkode.root),
    )

    return ret_json, 200


@linkode_v2.route('/tree/<linkode_id>', methods=['GET'])
def get_tree(linkode_id, revno=None):
    """Get the Tree of the given linkode.

    The linkode_id must be the root of the tree."""

    try:
        tree = kilinkbackend.build_tree_from_root_id(linkode_id)

    except LinkodeNotRootNodeError:
        msg = f"Linkode id '{linkode_id}' is not a tree root."
        logger.debug(msg)
        return msg, 404

    except KilinkNotFoundError:
        msg = f"Linkode id '{linkode_id}' not found"
        logger.debug(msg)
        return msg, 404

    ret_json = jsonify(tree)

    return ret_json, 200
