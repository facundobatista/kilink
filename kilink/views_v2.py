"""API v2."""

import logging
from http import HTTPStatus

from flask import Blueprint
from flask import jsonify, request, url_for

from kilink.backend import (
    kilinkbackend,
    KilinkDataTooBigError,
    KilinkNotFoundError,
    LinkodeNotRootNodeError,
)


logger = logging.getLogger(__name__)

linkode_v2 = Blueprint("linkode_v2", __name__)


def external_url_for(*args, **kwargs):
    """Provide the full url (including host) for some params.

    Always use this one, not 'url_for' directly.
    """
    return url_for(*args, **kwargs, _external=True)


@linkode_v2.route('/linkode/', methods=['POST'])
@linkode_v2.route('/linkode/<linkode_id>/', methods=['POST'])
def create_linkode(linkode_id=None):
    """Create a linkode.

    If linkode_id is present in the url, create a child of that linkode, otherwise
    create a new linkode root.

    Expected params:
        - content (str): content of the linkode.
        - text_type (optional, str): text_type of the content (ej python, html, etc)

    Expected responses:
        201 - Created:
            - linkode_id (str): id of the created linkode.
            - linkode_url (str): url to get the created linkode by api.
            - root_id (str): id of the linkode root of the created linkode tree.
            - root_url (str): url to get the root of the created linkode tree.

        400 - Bad Request: when the key 'content' is missing in the request.

        413 - Request Entity Too Large: when the content's size exceeds the limit.

        404 - Not Found: when creating a child of a linkode and the parent is not found.
    """
    if "content" not in request.json:
        return "missing content", HTTPStatus.BAD_REQUEST

    content = request.json['content']
    text_type = request.json.get('text_type', "")
    read_only = request.json.get('read_only', "").lower() == 'true'

    logger.debug("API create start; type=%r size=%d", text_type, len(content))
    try:
        linkode = kilinkbackend.create_linkode(content, text_type, linkode_id, read_only=read_only)

    except KilinkDataTooBigError:
        msg = "Content data too big; on creation"
        logger.debug(msg)
        return msg, HTTPStatus.REQUEST_ENTITY_TOO_LARGE

    except KilinkNotFoundError:
        msg = f"Linkode_id {linkode_id} not found"
        logger.debug(msg)
        return msg, HTTPStatus.NOT_FOUND

    ret_json = jsonify(
        linkode_id=linkode.linkode_id,
        linkode_url=external_url_for("linkode_v2.get_linkode", linkode_id=linkode.linkode_id),
        root_id=linkode.root,
        root_url=external_url_for("linkode_v2.get_linkode", linkode_id=linkode.root),
    )
    logger.debug("API create done; linkode_id=%s", linkode.linkode_id)
    return ret_json, HTTPStatus.CREATED


@linkode_v2.route('/linkode/<linkode_id>', methods=['GET'])
def get_linkode(linkode_id):
    """Get a linkode by ID.

    Expected responses:
        200 - OK
            - content (str): content of the linkode.
            - text_type (str): text_type of the content (ej python, html, etc)
            - timestamp (str): linkode creation date and time
            - linkode_id (str): id of the requested linkode.
            - linkode_url (str): url to get the requested linkode by api.
            - root_id (str): id of the linkode root of the requested linkode tree.
            - root_url (str): url to get the root of the requested linkode tree.

        404 - Not Found: when the requested linkode was not found in the database.
    """
    try:
        linkode = kilinkbackend.get_kilink(linkode_id)

    except KilinkNotFoundError:
        msg = f"Linkode_id {linkode_id} not found"
        logger.debug(msg)
        return msg, HTTPStatus.NOT_FOUND

    ret_json = jsonify(
        content=linkode.content,
        text_type=linkode.text_type,
        timestamp=linkode.timestamp.isoformat(),
        linkode_id=linkode.linkode_id,
        linkode_url=external_url_for("linkode_v2.get_linkode", linkode_id=linkode.linkode_id),
        root_id=linkode.root,
        root_url=external_url_for("linkode_v2.get_linkode", linkode_id=linkode.root),
        read_only=linkode.read_only
    )

    return ret_json, HTTPStatus.OK


@linkode_v2.route('/tree/<linkode_id>', methods=['GET'])
def get_tree(linkode_id, revno=None):
    """Get the Tree of the given linkode.

    The linkode_id must be the root of the tree.

    Expected responses:
        200 - OK - The tree is represented by a dict with the following structure:
            {
                linkode_id: <linkode id>,
                timestamp: <linkode creation timestamp>,
                order: 1,
                children: [
                    {
                        linkode_id: <linkode id>,
                        timestamp: <linkode creation timestamp>,
                        order: 2,
                        children: [...]
                    },
                    {
                        linkode_id: <linkode id>,
                        timestamp: <linkode creation timestamp>,
                        order: 3,
                        children: [...]
                    },
                ]
            }

        404 - Not Found:
            - when the requested linkode was not found in the database.
            - or when the requested linkode is not the root of its tree.
    """
    try:
        tree = kilinkbackend.build_tree_from_root_id(linkode_id)

    except LinkodeNotRootNodeError:
        msg = f"Linkode id '{linkode_id}' is not a tree root."
        logger.debug(msg)
        return msg, HTTPStatus.NOT_FOUND

    except KilinkNotFoundError:
        msg = f"Linkode id '{linkode_id}' not found"
        logger.debug(msg)
        return msg, HTTPStatus.NOT_FOUND

    ret_json = jsonify(tree)

    return ret_json, HTTPStatus.OK
