# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend tests."""

import datetime
import uuid

from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kilink.backend import (
    Kilink,
    KilinkBackend,
    KilinkNotFoundError,
    _get_unique_id,
)


class BaseTestCase(TestCase):
    """Base for all test using a backend."""

    def setUp(self):
        """Set up."""
        super(BaseTestCase, self).setUp()
        self.db_engine = create_engine("sqlite://")
        self.bkend = KilinkBackend(self.db_engine)


class ContentTestCase(BaseTestCase):
    """Tests for kilink creation and updating."""

    def setUp(self):
        """Set up."""
        super(ContentTestCase, self).setUp()
        Session = sessionmaker()
        conn = self.db_engine.connect()
        self.session = Session(bind=conn)

    def test_create_simple(self):
        """Simple create."""
        content = "some content"
        text_type = "type"
        klnk = self.bkend.create_kilink(content, text_type)
        klnk = self.session.query(Kilink).filter_by(
            kid=klnk.kid, revno=klnk.revno).one()
        self.assertEqual(klnk.content, content)
        self.assertTrue(isinstance(klnk.revno.encode("ascii"), str))
        self.assertEqual(klnk.parent, None)
        self.assertEqual(klnk.text_type, text_type)

    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = "some content"
        child_content = u"moño camión"
        klnk = self.bkend.create_kilink(parent_content, "type1")
        new_klnk = self.bkend.update_kilink(klnk.kid, klnk.revno,
                                            child_content, "type2")
        self.assertEqual(new_klnk.kid, klnk.kid)
        self.assertNotEqual(new_klnk.revno, klnk.revno)
        self.assertGreater(new_klnk.timestamp, klnk.timestamp)
        self.assertEqual(new_klnk.text_type, "type2")

        parent = self.session.query(Kilink).filter_by(
            kid=klnk.kid, revno=klnk.revno).one()
        self.assertEqual(parent.content, parent_content)
        child = self.session.query(Kilink).filter_by(
            kid=klnk.kid, revno=new_klnk.revno).one()
        self.assertEqual(child.content, child_content)

    def test_update_bad_kilink(self):
        """No kilink to update."""
        self.assertRaises(KilinkNotFoundError, self.bkend.update_kilink,
                          "unexistant", 1, "content", "")

    def test_update_bad_revno(self):
        """No revno to create a child."""
        klnk = self.bkend.create_kilink("content", "")
        assert klnk.revno != 37
        self.assertRaises(KilinkNotFoundError, self.bkend.update_kilink,
                          klnk.kid, 37, "content", "")


class DataRetrievalTestCase(BaseTestCase):
    """Tests that cover the retrieval of data."""

    def test_getkilink_revno_ok(self):
        """Get content for a kilink, indicating a good revno."""
        # create a kilink, two contents
        klnk = self.bkend.create_kilink("content 1", "type1")
        new_klnk = self.bkend.update_kilink(klnk.kid, klnk.revno, "c2", "t2")

        # get content for both revisions
        klnk = self.bkend.get_kilink(klnk.kid, klnk.revno)
        self.assertEqual(klnk.content, "content 1")
        self.assertEqual(klnk.text_type, "type1")
        klnk = self.bkend.get_kilink(klnk.kid, new_klnk.revno)
        self.assertEqual(klnk.content, "c2")
        self.assertEqual(klnk.text_type, "t2")

    def test_getkilink_revno_bad(self):
        """Get content for a kilink, indicating a bad revno."""
        klnk = self.bkend.create_kilink("content 1", "")
        self.assertRaises(KilinkNotFoundError,
                          self.bkend.get_kilink, klnk.kid, "bad revno")

    def test_getkilink_kid_bad(self):
        """Get content for a kilink, indicating a bad id."""
        self.assertRaises(KilinkNotFoundError,
                          self.bkend.get_kilink, "kid", "revno")

    def test_getkilink_tree_ok(self):
        """Get all the info for a kilink."""
        # create a tree
        klnk = self.bkend.create_kilink("content 1", "t1")
        klnk2 = self.bkend.update_kilink(klnk.kid, klnk.revno, "content 2", "")
        self.bkend.update_kilink(klnk2.kid, klnk2.revno, "content 3", "t3")
        self.bkend.update_kilink(klnk.kid, klnk.revno, "content 4", "")

        # get it and check structure: revno, content, parent, timestamp
        tree = self.bkend.get_kilink_tree(klnk.kid)
        self.assertEqual(tree[0].content, "content 1")
        self.assertEqual(tree[1].content, "content 2")
        self.assertEqual(tree[2].content, "content 3")
        self.assertEqual(tree[3].content, "content 4")
        self.assertEqual(tree[0].text_type, "t1")
        self.assertEqual(tree[1].text_type, "")
        self.assertEqual(tree[2].text_type, "t3")
        self.assertEqual(tree[3].text_type, "")
        for i, item in enumerate(tree, 1):
            self.assertTrue(isinstance(item.revno.encode("ascii"), str))
            if item.parent is not None:
                self.assertTrue(isinstance(item.parent.encode("ascii"), str))
            self.assertTrue(isinstance(item.timestamp, datetime.datetime))
            self.assertEqual(item.order, i)
        self.assertEqual(tree[0].parent, None)  # root node
        self.assertEqual(tree[1].parent, tree[0].revno)  # 2nd is child of root
        self.assertEqual(tree[2].parent, tree[1].revno)  # 3rd is child of 2nd
        self.assertEqual(tree[3].parent, tree[0].revno)  # 4th is child of root

    def test_getkilink_tree_bad(self):
        """Get all the info for a kilink that does not exist"""
        self.assertRaises(KilinkNotFoundError,
                          self.bkend.get_kilink_tree, 'kid')

    def test_findroot_ok_one_node(self):
        """Get the root node for a kilink when there's only one."""
        # create a node
        orig_klnk = self.bkend.create_kilink("content", "type")

        # get it and check
        klnk = self.bkend.get_root_node(orig_klnk.kid)
        self.assertEqual(klnk.kid, orig_klnk.kid)
        self.assertEqual(klnk.revno, orig_klnk.revno)
        self.assertEqual(klnk.content, "content")
        self.assertEqual(klnk.text_type, "type")

    def test_findroot_ok_two_nodes(self):
        """Get the root node for a kilink when there are several."""
        # create a couple of nodes
        orig_klnk = self.bkend.create_kilink("content", "type")
        self.bkend.update_kilink(orig_klnk.kid, orig_klnk.revno, "c2", "")
        self.bkend.update_kilink(orig_klnk.kid, orig_klnk.revno, "c3", "")

        # get it and check
        klnk = self.bkend.get_root_node(orig_klnk.kid)
        self.assertEqual(klnk.kid, orig_klnk.kid)
        self.assertEqual(klnk.revno, orig_klnk.revno)
        self.assertEqual(klnk.content, orig_klnk.content)

    def test_findroot_tree_bad(self):
        """Get the root node for a kilink that does not exist."""
        self.assertRaises(KilinkNotFoundError, self.bkend.get_root_node, 'kid')


class IDGenTestCase(TestCase):
    """Test case for the id generator."""

    def test_type(self):
        """It must be a string."""
        newid = _get_unique_id()
        self.assertTrue(isinstance(newid, str))

    def test_sanity(self):
        """Stupid sanity check."""
        ids = [_get_unique_id() for _ in xrange(100)]
        self.assertEqual(len(set(ids)), 100)
