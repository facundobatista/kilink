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

TreeNode = collections.namedtuple("TreeNode",
                                  "content parent order revno timestamp")


class Kilink(Base):
    """Kilink data."""
    __tablename__ = 'kilink'

    kid = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    revno = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent = Column(String, default=None)
    content = Column(LargeBinary)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


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

    def create_kilink(self, content):
        """Create a new kilink with given content."""
        content = content.encode('utf8')
        zipped = zlib.compress(content)
        session = self.sm.get_session()
        klnk = Kilink(content=zipped)
        session.add(klnk)
        session.commit()
        return klnk

    def update_kilink(self, kid, parent, new_content):
        """Add a new revision to a kilink."""
        new_content = new_content.encode('utf8')
        zipped = zlib.compress(new_content)
        session = self.sm.get_session()
        search = session.query(Kilink).filter_by(kid=kid, revno=parent)
        if not search.all():
            raise KilinkNotFoundError("Parent kilink not found")

        klnk = Kilink(kid=kid, parent=parent, content=zipped)
        session.add(klnk)
        session.commit()
        return klnk

    def get_content(self, kid, revno):
        """Get content for a specific kilink and revision number."""
        session = self.sm.get_session()
        try:
            klnk = session.query(Kilink).filter_by(
                kid=kid, revno=revno).one()
        except NoResultFound:
            msg = "Data not found for kilink=%r revno=%r" % (kid, revno)
            raise KilinkNotFoundError(msg)

        expanded = zlib.decompress(klnk.content)
        expanded = expanded.decode('utf8')
        return expanded

    def get_kilink_tree(self, kid):
        """Return all the information about the kilink."""
        session = self.sm.get_session()
        klnk_tree = session.query(Kilink).filter_by(kid=kid).all()
        if len(klnk_tree) == 0:
            raise ValueError("Kilink id not found: %r" % (kid,))
        decomp = zlib.decompress
        klnk_tree.sort(key=operator.attrgetter("timestamp", "revno"))
        result = []
        for i, klnk in enumerate(klnk_tree, 1):
            tn = TreeNode(order=i, content=decomp(klnk.content),
                          revno=klnk.revno, parent=klnk.parent,
                          timestamp=klnk.timestamp)
            result.append(tn)
        return result
