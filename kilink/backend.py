# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend functionality for Kilink."""

import collections
import datetime
import operator
import threading
import uuid
import zlib

from sqlalchemy import Column, DateTime, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class KilinkNotFoundError(Exception):
    """A kilink was specified, we couldn't find it."""

TreeNode = collections.namedtuple(
    "TreeNode", "content parent order revno timestamp text_type")


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


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


class SessionManager(object):
    """Handles the sessions in a multi-threaded environment."""

    def __init__(self, engine):
        self.engine = engine
        self._sessions = {}

    def get_session(self):
        """Return a session for this thread."""
        thread_id = threading.current_thread().ident
        try:
            return self._sessions[thread_id]
        except KeyError:
            pass

        conn = self.engine.connect()
        Session = sessionmaker()
        session = Session(bind=conn)
        self._sessions[thread_id] = session
        return session


class KilinkBackend(object):
    """Backend for Kilink."""

    def __init__(self, db_engine):
        Base.metadata.create_all(db_engine)
        self.sm = SessionManager(db_engine)

    def create_kilink(self, content, text_type):
        """Create a new kilink with given content."""
        session = self.sm.get_session()
        klnk = Kilink(content=content, text_type=text_type)
        session.add(klnk)
        session.commit()
        return klnk

    def update_kilink(self, kid, parent, new_content, text_type):
        """Add a new revision to a kilink."""
        session = self.sm.get_session()
        search = session.query(Kilink).filter_by(kid=kid, revno=parent)
        if not search.all():
            raise KilinkNotFoundError("Parent kilink not found")

        klnk = Kilink(kid=kid, parent=parent,
                      content=new_content, text_type=text_type)
        session.add(klnk)
        session.commit()
        return klnk

    def get_kilink(self, kid, revno):
        """Get a specific kilink and revision number."""
        session = self.sm.get_session()
        try:
            klnk = session.query(Kilink).filter_by(
                kid=kid, revno=revno).one()
        except NoResultFound:
            msg = "Data not found for kilink=%r revno=%r" % (kid, revno)
            raise KilinkNotFoundError(msg)

        return klnk

    def get_kilink_tree(self, kid):
        """Return all the information about the kilink."""
        session = self.sm.get_session()
        klnk_tree = session.query(Kilink).filter_by(kid=kid).all()
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
        session = self.sm.get_session()
        try:
            klnk = session.query(Kilink).filter_by(kid=kid).order_by(
                Kilink.timestamp).limit(1).one()
        except NoResultFound:
            raise KilinkNotFoundError("Kilink id not found: %r" % (kid,))
        return klnk
