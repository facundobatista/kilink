# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend functionality for Kilink."""

import collections
import datetime
import operator
import uuid
import zlib
import saw

from sqlalchemy import Column, DateTime, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.base import Engine

Base = declarative_base()


class KilinkNotFoundError(Exception):
    """A kilink was specified, we couldn't find it."""

TreeNode = collections.namedtuple(
    "TreeNode", "content parent order revno timestamp text_type")


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
db = None  # a SAW db instance.


def get_backend(engine):
    """Returns a Kilink backend instance."""
    if not isinstance(engine, Engine):
        raise Exception('Argument must be an Engine instance.')
    global db
    db = saw.DB('linkode.db', engine=engine)
    return KilinkBackend(engine)


def _get_unique_id():
    """Returns a unique ID everytime it's called."""
    arr = []
    base = len(ALPHABET)
    num = uuid.uuid4().int
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    return ''.join(arr)


class Kilink(Base, object):
    """Kilink data."""
    __tablename__ = 'kilink'

    kid = Column(String, primary_key=True, default=_get_unique_id)
    revno = Column(String, primary_key=True, default=_get_unique_id)
    parent = Column(String, default=None)
    compressed = Column(LargeBinary)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    text_type = Column(String)

    def _get_content(self):
        """Return the content, uncompressed."""
        data = zlib.decompress(self.compressed)
        return data.decode("utf8")

    def _set_content(self, data):
        """Compress the content and set it."""
        data = data.encode("utf8")
        self.compressed = zlib.compress(data)

    content = property(_get_content, _set_content)


class KilinkBackend(object):
    """Backend for Kilink."""

    def __init__(self, engine):
        self.engine = engine

    def create_kilink(self, content, text_type):
        """Create a new kilink with given content."""
        klnk = Kilink(content=content, text_type=text_type)
        return db.insert(klnk, returning_id='kid')

    def update_kilink(self, kid, parent, new_content, text_type):
        """Add a new revision to a kilink."""
        with db.query as query:
            klnk_exists = query(Kilink).filter_by(kid=kid, revno=parent).scalar()
        if not klnk_exists:
            raise KilinkNotFoundError("Parent kilink not found")
        klnk = Kilink(kid=kid, parent=parent,
                      content=new_content, text_type=text_type)
        kid = db.insert(klnk, returning_id='kid')
        return kid, klnk.revno

    def get_kilink(self, kid, revno):
        """Get a specific kilink and revision number."""
        with db.query as query:
            klnk = query(Kilink).filter_by(kid=kid,
                revno=revno).scalar()
        if not klnk:
            msg = "Data not found for kilink=%r revno=%r" % (kid, revno)
            raise KilinkNotFoundError(msg)
        return klnk

    def get_kilink_tree(self, kid):
        """Return all the information about the kilink."""
        with db.query as query:
            klnk_tree = query(Kilink).filter_by(kid=kid).all()
        if len(klnk_tree) == 0:
            raise KilinkNotFoundError("Kilink id not found: %r" % (kid,))
        klnk_tree.sort(key=operator.attrgetter("timestamp", "revno"))
        result = []
        for i, klnk in enumerate(klnk_tree, 1):
            tn = TreeNode(order=i, content=klnk.content,
                          revno=klnk.revno, parent=klnk.parent,
                          timestamp=klnk.timestamp, text_type=klnk.text_type)
            result.append(tn)
        return result

    def get_root_node(self, kid):
        """Return the root node of the kilink."""
        with db.query as query:
            klnk = query(Kilink).filter_by(kid=kid).order_by(
                Kilink.timestamp).limit(1).scalar()
        if not klnk:
            raise KilinkNotFoundError("Kilink id not found: %r" % (kid,))
        return klnk
