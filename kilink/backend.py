# encoding: utf8

# Copyright 2011-2016 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend functionality for Kilink."""

import collections
import datetime
import logging
import operator
import uuid
import zlib

from sqlalchemy import Column, DateTime, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

from config import config

# DB stuff
Base = declarative_base()

# logger
logger = logging.getLogger('kilink.backend')


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
        self._cached_version = None

    def get_version(self):
        """Return the version, reading it from a file (cached)."""
        if self._cached_version is None:
            try:
                with open(config['version_file'], 'rt') as fh:
                    self._cached_version = fh.read()
            except:
                self._cached_version = '?'
        return self._cached_version

    @session_manager
    def create_kilink(self, content, text_type):
        """Create a new kilink with given content."""
        klnk = Kilink(content=content, text_type=text_type)
        self.session.add(klnk)
        return klnk

    @session_manager
    def update_kilink(self, kid, parent, new_content, text_type):
        """Add a new revision to a kilink."""
        search = self.session.query(Kilink).filter_by(kid=kid, revno=parent)
        if not search.all():
            raise KilinkNotFoundError("Parent kilink not found")

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

    def build_tree(self, kid, revno):
        """Build the tree for a given kilink id."""
        nodes = []
        for treenode in self.get_kilink_tree(kid):
            url = "/%s/%s" % (kid, treenode.revno)
            parent = treenode.parent
            nodes.append({
                'order': treenode.order,
                'parent': parent,
                'revno': treenode.revno,
                'url': url,
                'timestamp': str(treenode.timestamp),
                'selected': treenode.revno == revno,
            })
        root = [n for n in nodes if n['parent'] is None][0]
        fringe = [root, ]

        while fringe:
            node = fringe.pop()
            children = [n for n in nodes if n['parent'] == node['revno']]

            node['contents'] = children
            fringe.extend(children)

        return root, len(nodes)
