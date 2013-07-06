# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend tests."""

import datetime
import uuid
import zlib

from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kilink.backend import KilinkBackend, Kilink, KilinkNotFoundError


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
        zipped = zlib.compress(content)
        klnk = self.bkend.create_kilink(content)
        klnk = self.session.query(Kilink).filter_by(
            kid=klnk.kid, revno=klnk.revno).one()
        self.assertEqual(klnk.content, zipped)
        self.assertTrue(uuid.UUID(klnk.revno))
        self.assertEqual(klnk.parent, None)

    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = "some content"
        child_content = "some content"
        klnk = self.bkend.create_kilink(parent_content)
        new_klnk = self.bkend.update_kilink(klnk.kid, klnk.revno,
                                            child_content)
        self.assertEqual(new_klnk.kid, klnk.kid)
        self.assertNotEqual(new_klnk.revno, klnk.revno)
        self.assertGreater(new_klnk.timestamp, klnk.timestamp)
        parent = self.session.query(Kilink).filter_by(
            kid=klnk.kid, revno=klnk.revno).one()
        self.assertEqual(parent.content, zlib.compress(parent_content))
        child = self.session.query(Kilink).filter_by(
            kid=klnk.kid, revno=new_klnk.revno).one()
        self.assertEqual(child.content, zlib.compress(child_content))

    def test_update_bad_kilink(self):
        """No kilink to update."""
        self.assertRaises(KilinkNotFoundError, self.bkend.update_kilink,
                          "unexistant", 1, "content")

    def test_update_bad_revno(self):
        """No revno to create a child."""
        klnk = self.bkend.create_kilink("content")
        assert klnk.revno != 37
        self.assertRaises(KilinkNotFoundError, self.bkend.update_kilink,
                          klnk.kid, 37, "content")


class DataRetrievalTestCase(BaseTestCase):
    """Tests that cover the retrieval of data."""

    def test_getcontent_simple(self):
        """Get content for a kilink, no revno indicated."""
        # create a kilink, two contents
        klnk = self.bkend.create_kilink("content 1")
        self.bkend.update_kilink(klnk.kid, klnk.revno, "content 2")

        # get the content
        content = self.bkend.get_content(klnk.kid, klnk.revno)
        self.assertEqual(content, "content 1")

    def test_getcontent_revno_ok(self):
        """Get content for a kilink, indicating a good revno."""
        # create a kilink, two contents
        klnk = self.bkend.create_kilink("content 1")
        new_klnk = self.bkend.update_kilink(klnk.kid, klnk.revno, "content 2")

        # get content for both revisions
        content = self.bkend.get_content(klnk.kid, klnk.revno)
        self.assertEqual(content, "content 1")
        content = self.bkend.get_content(klnk.kid, new_klnk.revno)
        self.assertEqual(content, "content 2")

    def test_getcontent_revno_bad(self):
        """Get content for a kilink, indicating a bad revno."""
        klnk = self.bkend.create_kilink("content 1")
        self.assertRaises(KilinkNotFoundError,
                          self.bkend.get_content, klnk.kid, "bad revno")

    def test_getcontent_kid_bad(self):
        """Get content for a kilink, indicating a bad id."""
        self.assertRaises(KilinkNotFoundError,
                          self.bkend.get_content, "kid", "revno")

    def test_getkilink_ok(self):
        """Get all the info for a kilink."""
        # create a tree
        klnk = self.bkend.create_kilink("content 1")
        klnk2 = self.bkend.update_kilink(klnk.kid, klnk.revno, "content 2")
        self.bkend.update_kilink(klnk2.kid, klnk2.revno, "content 3")
        self.bkend.update_kilink(klnk.kid, klnk.revno, "content 4")

        # get it and check structure: revno, content, parent, timestamp
        tree = self.bkend.get_kilink_tree(klnk.kid)
        self.assertEqual(tree[0].content, "content 1")
        self.assertEqual(tree[1].content, "content 2")
        self.assertEqual(tree[2].content, "content 3")
        self.assertEqual(tree[3].content, "content 4")
        for i, item in enumerate(tree, 1):
            self.assertTrue(uuid.UUID(item.revno))
            if item.parent is not None:
                self.assertTrue(uuid.UUID(item.parent))
            self.assertTrue(isinstance(item.timestamp, datetime.datetime))
            self.assertEqual(item.order, i)
        self.assertEqual(tree[0].parent, None)  # root node
        self.assertEqual(tree[1].parent, tree[0].revno)  # 2nd is child of root
        self.assertEqual(tree[2].parent, tree[1].revno)  # 3rd is child of 2nd
        self.assertEqual(tree[3].parent, tree[0].revno)  # 4th is child of root

    def test_getkilink_bad(self):
        """Get all the info for a kilink that does not exist"""
        self.assertRaises(ValueError, self.bkend.get_kilink_tree, 'kid')
