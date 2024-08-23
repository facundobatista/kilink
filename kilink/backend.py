# Copyright 2011-2021 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend functionality for Kilink."""

import collections
import datetime
import logging
import operator
import uuid
import zlib

from sqlalchemy import Column, DateTime, String, LargeBinary
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from kilink.config import config, DB_ENGINE_INSTANCE_KEY

# what we use for plain text
PLAIN_TEXT = 'plain text'

# DB stuff
Base = declarative_base()

# logger
logger = logging.getLogger('kilink.backend')


class KilinkNotFoundError(Exception):
    """A kilink was specified, we couldn't find it."""


class KilinkDataTooBigError(Exception):
    """Content data too big."""


class LinkodeNotRootNodeError(Exception):
    """Linkode is not a root node."""


TreeNode = collections.namedtuple(
    "TreeNode", "content parent order linkode_id timestamp text_type")


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _get_unique_id():
    """Return a unique ID everytime it's called."""
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
    timestamp = Column(DateTime, default=datetime.datetime.now)
    _text_type = Column('text_type', String)

    def _get_content(self):
        """Return the content, uncompressed."""
        data = zlib.decompress(self.compressed)
        return data.decode("utf8")

    def _set_content(self, data):
        """Compress the content and set it."""
        data = data.encode("utf8")
        self.compressed = zlib.compress(data)

    content = property(_get_content, _set_content)

    def _get_text_type(self):
        """Get the text type; if empty or non existant, return plain text."""
        return self._text_type or PLAIN_TEXT

    def _set_text_type(self, value):
        """Directly set the text type."""
        self._text_type = value

    text_type = property(_get_text_type, _set_text_type)

    def __repr__(self):
        return "<Kilink id={} root={}>".format(self.linkode_id, self.root)

    __str__ = __repr__


def session_manager(orig_func):
    """Wrap function with the session."""

    def new_func(self, *a, **k):
        """Wrappend function to manage DB session."""
        if not self.session.in_transaction():
            self.session.begin()
        try:
            resp = orig_func(self, *a, **k)
            self.session.commit()
            return resp
        except Exception:
            self.session.rollback()
            raise
    return new_func


class KilinkBackend(object):
    """Backend for Kilink."""

    def __init__(self):
        self._cached_version = None
        self._session = None

    @property
    def session(self):
        """Return the cached or just built session."""
        if self._session is None:
            db_engine = config[DB_ENGINE_INSTANCE_KEY]
            Base.metadata.create_all(db_engine)
            Session = scoped_session(sessionmaker())
            self._session = Session(bind=db_engine)

        return self._session

    def get_version(self):
        """Return the version, reading it from a file (cached)."""
        if self._cached_version is None:
            try:
                with open(config['version_file'], 'rt') as fh:
                    self._cached_version = fh.read()
            except Exception:
                self._cached_version = '?'
        return self._cached_version

    @session_manager
    def create_kilink(self, content, text_type):
        """Create a new kilink with given content."""
        self._check_kilink(content)
        new_id = _get_unique_id()
        klnk = Kilink(linkode_id=new_id, root=new_id, content=content, text_type=text_type)
        self.session.add(klnk)
        return klnk

    @session_manager
    def update_kilink(self, parent_id, new_content, text_type):
        """Add a new child to a kilink."""
        self._check_kilink(new_content)
        parent_klnk = self.session.get(Kilink, parent_id)
        if parent_klnk is None:
            raise KilinkNotFoundError("Parent kilink not found")

        new_id = _get_unique_id()
        klnk = Kilink(linkode_id=new_id, parent=parent_id, root=parent_klnk.root,
                      content=new_content, text_type=text_type)
        self.session.add(klnk)
        return klnk

    def create_linkode(self, content, text_type, linkode_parent_id=None):
        """Create a new linkode as root node or as a child of another linkode."""
        if linkode_parent_id:
            linkode = self.update_kilink(
                parent_id=linkode_parent_id,
                text_type=text_type,
                new_content=content,
            )
        else:
            linkode = self.create_kilink(
                text_type=text_type,
                content=content,
            )

        return linkode

    def _check_kilink(self, content):
        if len(content) > config["max_payload"]:
            raise KilinkDataTooBigError("Content data too large, limit exceeded")

    @session_manager
    def get_kilink(self, linkode_id):
        """Get a specific kilink."""
        klnk = self.session.get(Kilink, linkode_id)
        if klnk is None:
            raise KilinkNotFoundError("Data not found for kilink=%r" % (linkode_id,))
        return klnk

    @session_manager
    def _get_kilink_tree(self, root):
        """Return all the information about the kilink."""
        klnk_tree = self.session.query(Kilink).filter_by(root=root).order_by("timestamp").all()
        if len(klnk_tree) == 0:
            raise KilinkNotFoundError("Kilink id not found: %r" % (root,))
        klnk_tree.sort(key=operator.attrgetter("timestamp"))
        result = []
        for i, klnk in enumerate(klnk_tree, 1):
            tn = TreeNode(order=i, linkode_id=klnk.linkode_id, content=klnk.content,
                          parent=klnk.parent, timestamp=klnk.timestamp, text_type=klnk.text_type)
            result.append(tn)
        return result

    @session_manager
    def _get_root_node(self, linkode_id):
        """Return the root node of the kilink."""
        klnk = self.session.get(Kilink, linkode_id)
        if klnk is None:
            raise KilinkNotFoundError("Kilink id not found: %r" % (linkode_id,))
        return klnk

    def build_tree(self, linkode_id):
        """Build the tree for a given kilink id.

        Needed for api v1.
        """
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

    def build_tree_from_root_id(self, linkode_id):
        """Build the tree of the given linkode root."""
        linkode = self.get_kilink(linkode_id)

        if linkode.root != linkode_id:
            raise LinkodeNotRootNodeError()

        # get and process all nodes for that root
        nodes = []
        root_node = None

        for treenode in self._get_kilink_tree(linkode_id):
            node_dict = {
                'timestamp': treenode.timestamp.isoformat(),
                'linkode_id': treenode.linkode_id,
                'parent': treenode.parent,
            }
            if treenode.parent is None:
                root_node = node_dict
            nodes.append(node_dict)

        # at this point 'nodes' is a flat list of linkodes represented as dicts.
        # in the following loop we will nest the children linkodes inside their parents.
        fringe = [root_node]
        while fringe:
            current_node = fringe.pop()
            children = [n for n in nodes if n.get('parent') == current_node['linkode_id']]

            # we don't want to expose the concept of 'parent' in the api
            current_node.pop('parent')
            current_node['children'] = children
            fringe.extend(children)

        tree = root_node
        return tree


kilinkbackend = KilinkBackend()
