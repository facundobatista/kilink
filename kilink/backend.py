# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend functionality for Kilink."""

import collections
import datetime
import logging
import operator
import uuid
import zlib
from config import config

from sqlalchemy import Column, DateTime, LargeBinary, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

# DB stuff
Base = declarative_base()

# logger
logger = logging.getLogger('kilink.backend')


class KilinkNotFoundError(Exception):
    """A kilink was specified, we couldn't find it."""


class KilinkMaxLenExcededError(Exception):
    """Try to create or update a kilink with lot of lines."""


TreeNode = collections.namedtuple(
    "TreeNode", "content parent order revno timestamp text_type")


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
MAX_LINES = 10000
MAX_CHARS = 100000


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


def session_manager(orig_func):
    """Decorator to wrap function with the session."""
    def new_func(self, *a, **k):
        """Wrappend function to manage DB session."""
        self.session.begin()
        try:
            resp = orig_func(self, *a, **k)
            self.session.commit()
            return resp
        except:
            self.session.rollback()
            raise
    return new_func


class KilinkBackend(object):
    """Backend for Kilink."""

    def __init__(self, db_engine):
        Base.metadata.create_all(db_engine)
        Session = scoped_session(sessionmaker(autocommit=True))
        self.session = Session(bind=db_engine)

    def check_content_len(self, content, max_lines=False, max_chars=False):
        """Check content length."""
        max_chars = max_chars or config.get("max_chars", False) or MAX_CHARS
        max_lines = max_lines or config.get("max_lines", False) or MAX_LINES
        dbg_msg = "Content: {}, max chars: {}, max lines: {}".format(content,
                                                                     max_chars,
                                                                     max_lines)
        logger.debug(dbg_msg)
        err_msgs = []
        if len(content) > max_chars:
            err = "Content len exeded chars maximun: {}".format(len(content))
            err_msgs.append(err)
        lines = content.split("\n")
        if len(lines) <= max_lines:
            err = "Content len exeded lines maximun: {}".format(len(lines))
            err_msgs.append(err)

        if err_msgs:
            err = " and ".join(err_msgs)
            raise KilinkMaxLenExcededError(err)

        return True

    @session_manager
    def create_kilink(self, content, text_type):
        """Create a new kilink with given content."""
        if not self.check_content_len(content, 100):
            raise KilinkMaxLenExcededError("Content len exeded: %s" % 10)

        self.check_content_len(content)
        klnk = Kilink(content=content, text_type=text_type)
        self.session.add(klnk)
        return klnk

    @session_manager
    def update_kilink(self, kid, parent, new_content, text_type):
        """Add a new revision to a kilink."""
        search = self.session.query(Kilink).filter_by(kid=kid, revno=parent)
        if not search.all():
            raise KilinkNotFoundError("Parent kilink not found")

        self.check_content_len(new_content)
        klnk = Kilink(kid=kid, parent=parent,
                      content=new_content, text_type=text_type)
        self.session.add(klnk)
        return klnk

    @session_manager
    def get_kilink(self, kid, revno):
        """Get a specific kilink and revision number."""
        try:
            klnk = self.session.query(Kilink).filter_by(
                kid=kid, revno=revno).one()
        except NoResultFound:
            msg = "Data not found for kilink=%r revno=%r" % (kid, revno)
            raise KilinkNotFoundError(msg)

        return klnk

    @session_manager
    def get_kilink_tree(self, kid):
        """Return all the information about the kilink."""
        klnk_tree = self.session.query(Kilink).filter_by(kid=kid).all()
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

    @session_manager
    def get_root_node(self, kid):
        """Return the root node of the kilink."""
        try:
            klnk = self.session.query(Kilink).filter_by(kid=kid).order_by(
                Kilink.timestamp).limit(1).one()
        except NoResultFound:
            raise KilinkNotFoundError("Kilink id not found: %r" % (kid,))
        return klnk
