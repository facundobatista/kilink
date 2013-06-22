# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend tests."""

import datetime
import zlib

from unittest import TestCase

from kilink.backend import KilinkBackend, Kilink


class BaseTestCase(TestCase):
    """Base for all test using a backend."""
    def setUp(self):
        """Set up."""
        super(BaseTestCase, self).setUp()
        self.bkend = KilinkBackend('sqlite:/:memory:?debug=0')
        Kilink.createTable()

    def tearDown(self):
        """Tear down."""
        Kilink.dropTable()


class ContentTestCase(BaseTestCase):
    """Tests for kilink creation and updating."""

    def test_create_simple(self):
        """Simple create."""
        content = "some content"
        zipped = zlib.compress(content)
        kid = self.bkend.create_kilink(content)
        klnk = Kilink.selectBy(kid=kid).getOne()
        self.assertEqual(klnk.content, zipped)
        self.assertEqual(klnk.revno, 1)
        self.assertEqual(klnk.parent_revno, None)

    def test_create_kid_ok(self):
        """Create indicating a new kid."""
        self.bkend.create_kilink("some content", kid="kid")
        self.assertEqual(Kilink.selectBy(kid="kid").count(), 1)

    def test_create_kid_repeated(self):
        """Create indicating an existing kid."""
        self.bkend.create_kilink("some content", kid="kid")
        self.assertRaises(ValueError, self.bkend.create_kilink,
                          "other content", kid="kid")

    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = "some content"
        child_content = "some content"
        kid = self.bkend.create_kilink(parent_content)
        new_revno = self.bkend.update_kilink(kid, 1, child_content)
        self.assertEqual(new_revno, 2)
        parent = Kilink.selectBy(kid=kid, revno=1).getOne()
        self.assertEqual(parent.content, zlib.compress(parent_content))
        child = Kilink.selectBy(kid=kid, revno=2).getOne()
        self.assertEqual(child.content, zlib.compress(child_content))

    def test_update_bad_kilink(self):
        """No kilink to update."""
        self.assertRaises(ValueError, self.bkend.update_kilink,
                          "unexistant", 1, "content")

    def test_update_bad_revno(self):
        """No revno to create a child."""
        kid = self.bkend.create_kilink("content")
        klnk = Kilink.selectBy(kid=kid).getOne()
        assert klnk.revno != 37
        self.assertRaises(ValueError, self.bkend.update_kilink,
                          kid, 37, "content")


class DataRetrievalTestCase(BaseTestCase):
    """Tests that cover the retrieval of data."""

    def test_getcontent_simple(self):
        """Get content for a kilink, no revno indicated."""
        # create a kilink, two contents
        kid = self.bkend.create_kilink("content 1")
        self.bkend.update_kilink(kid, 1, "content 2")

        # get the content
        content = self.bkend.get_content(kid)
        self.assertEqual(content, "content 1")

    def test_getcontent_revno_ok(self):
        """Get content for a kilink, indicating a good revno."""
        # create a kilink, two contents
        kid = self.bkend.create_kilink("content 1")
        self.bkend.update_kilink(kid, 1, "content 2")

        # get content for both revisions
        content = self.bkend.get_content(kid, revno=1)
        self.assertEqual(content, "content 1")
        content = self.bkend.get_content(kid, revno=2)
        self.assertEqual(content, "content 2")

    def test_getcontent_revno_bad(self):
        """Get content for a kilink, indicating a bad revno."""
        kid = self.bkend.create_kilink("content 1")
        self.assertRaises(ValueError, self.bkend.get_content, kid, revno=7)

    def test_getcontent_kid_bad(self):
        """Get content for a kilink, indicating a bad id."""
        self.assertRaises(ValueError, self.bkend.get_content, "kid")

    def test_getkilink_ok(self):
        """Get all the info for a kilink."""
        # create a tree
        kid = self.bkend.create_kilink("content 1")
        revno2 = self.bkend.update_kilink(kid, 1, "content 2")
        self.bkend.update_kilink(kid, revno2, "content 3")
        self.bkend.update_kilink(kid, 1, "content 4")

        # get it and check structure: revno, content, parent, timestamp
        tree = self.bkend.get_kilink_tree(kid)
        tree = sorted(tree)
        self.assertEqual(tree[0][:3], (1, "content 1", None))
        self.assertEqual(tree[1][:3], (2, "content 2", 1))
        self.assertEqual(tree[2][:3], (3, "content 3", 2))
        self.assertEqual(tree[3][:3], (4, "content 4", 1))
        for item in tree:
            self.assertTrue(isinstance(item[3], datetime.datetime))

    def test_getkilink_bad(self):
        """Get all the info for a kilink that does not exist"""
        self.assertRaises(ValueError, self.bkend.get_kilink_tree, 'kid')
