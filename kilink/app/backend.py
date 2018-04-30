# encoding: utf8

# Copyright 2011-2018 Facundo Batista, Nicolás César
# All Rights Reserved

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

from kilink.app.exceptions import KilinkNotFoundError, KilinkDataTooBigError
from kilink.app.config import config

# DB stuff
Base = declarative_base()

# logger
logger = logging.getLogger('kilink.backend')

TreeNode = collections.namedtuple(
    "TreeNode", "content parent order linkode_id timestamp text_type")


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_unique_id():
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

    linkode_id = Column(String, primary_key=True)
    root = Column(String, nullable=False)
    parent = Column(String, default=None)
    compressed = Column(LargeBinary)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    text_type = Column(String)

    @property
    def content(self):
        """Return the content, uncompressed."""
        data = zlib.decompress(self.compressed)
        return data.decode("utf8")

    @content.setter
    def content(self, data):
        """Compress the content and set it."""
        data = data.encode("utf8")
        self.compressed = zlib.compress(data)

    def __str__(self):
        return "<Kilink id={} root={}>".format(self.linkode_id, self.root)

    __repr__ = __str__


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
        self._max_payload = config['max_payload']

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
        self._check_kilink(content)
        new_id = get_unique_id()
        klnk = Kilink(linkode_id=new_id, root=new_id, content=content,
                      text_type=text_type)
        self.session.add(klnk)
        return klnk

    @session_manager
    def update_kilink(self, parent_id, new_content, text_type):
        """Add a new child to a kilink."""
        self._check_kilink(new_content)
        parent_klnk = self.session.query(Kilink).get(parent_id)
        if parent_klnk is None:
            raise KilinkNotFoundError("Parent kilink not found")

        new_id = get_unique_id()
        klnk = Kilink(linkode_id=new_id, parent=parent_id,
                      root=parent_klnk.root, content=new_content,
                      text_type=text_type)
        self.session.add(klnk)
        return klnk

    def _check_kilink(self, content):
        """Check kilink max payload"""
        if len(content) > self._max_payload:
            raise KilinkDataTooBigError(
                "Content data too large, limit exceeded")

    @session_manager
    def get_kilink(self, linkode_id):
        """Get a specific kilink."""
        klnk = self.session.query(Kilink).get(linkode_id)
        if klnk is None:
            raise KilinkNotFoundError(
                "Data not found for kilink=%r" % (linkode_id,))
        return klnk

    @session_manager
    def _get_kilink_tree(self, root):
        """Return all the information about the kilink."""
        klnk_tree = self.session.query(Kilink).filter_by(
            root=root).order_by("timestamp").all()
        if len(klnk_tree) == 0:
            raise KilinkNotFoundError("Kilink id not found: %r" % (root,))
        klnk_tree.sort(key=operator.attrgetter("timestamp"))
        result = []
        for i, klnk in enumerate(klnk_tree, 1):
            tn = TreeNode(order=i, linkode_id=klnk.linkode_id,
                          content=klnk.content, parent=klnk.parent,
                          timestamp=klnk.timestamp, text_type=klnk.text_type)
            result.append(tn)
        return result

    @session_manager
    def _get_root_node(self, linkode_id):
        """Return the root node of the kilink."""
        klnk = self.session.query(Kilink).get(linkode_id)
        if klnk is None:
            raise KilinkNotFoundError(
                "Kilink id not found: %r" % (linkode_id,))
        return klnk

    def build_tree(self, linkode_id):
        """Build the tree for a given kilink id."""
        # get the kilink to find out the root
        klnk = self._get_root_node(linkode_id)

        # get and process all nodes for that root
        nodes = []
        root_node = None
        for treenode in self._get_kilink_tree(klnk.root):
            url = "/%s" % (treenode.linkode_id,)
            node = {
                'order': treenode.order,
                'parent': treenode.parent,
                'revno': treenode.linkode_id,
                'url': url,
                'timestamp': str(treenode.timestamp),
                'selected': treenode.linkode_id == linkode_id,
                'linkode_id': treenode.linkode_id,
            }
            if treenode.parent is None:
                root_node = node
            nodes.append(node)

        fringe = [root_node]
        while fringe:
            node = fringe.pop()
            children = [n for n in nodes if n['parent'] == node['linkode_id']]

            node['contents'] = children
            fringe.extend(children)

        return root_node, len(nodes)
