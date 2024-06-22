# API
import logging

from flask import Blueprint
from flask import Flask, jsonify, render_template, request, make_response, url_for

from kilink.backend import kilinkbackend, KilinkDataTooBigError, KilinkNotFoundError
from kilink.config import config

logger = logging.getLogger(__name__)

linkode_v2 = Blueprint("linkode_v2", __name__)

"""
/linkode POST -> crea un nodo raiz
- toma:
    - content
    - text_type [opt]
- devuelve:
    - linkode_metadata
        - linkode_id
        - root_id (self)
        - linkode_url
        - root_url

/linkode/id/
    - POST -> Crea un hijo de ese id
        - toma lo mismo que /linkode/
        - devuelve lo mismo que /linkode/

    - GET -> devuelve details de ese id
        - devuelve lo mismo que lo otro + extra info:
            - content
            - text_type
            - timestamp, etc....

/tree/id/ GET solo funciona con id de root (sino 404)
    - devuelve:
        - estructura de arbol, cada nodo con su metadata:
            - linkode_id
            - timestamp

NO HAY PUT en ningun endpoint. Todas las entidades son inmutables, para cambios crear uno nuevo.
"""
class LinkodeCreateParams:
    def validate_params(self):
        """Tiene que venir esta estructura en la request
        """
        return {
            "content": str,
            "text_type": str, # opcional en key o value=None
        }

class LinkodeReference:
    """
    Respuesta de creación de linkodes
    """
    def response(self):
        {
            "linkode_id": str,
            "root_id": str,
            "likode_url": str,
            "root_url": str,
        }


class LinkodeGetDetails:
    def serialize(self):
        return {}



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
