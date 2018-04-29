# encoding: utf8

# Copyright 2011-2018 Facundo Batista, Nicolás César
# All Rights Reserved

"""Backend tests."""

import datetime
import os
import tempfile

from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kilink.kilink.backend import (
    Kilink,
    KilinkBackend,
    KilinkNotFoundError,
    get_unique_id,
)
from kilink.kilink.config import config


class BaseTestCase(TestCase):
    """Base for all test using a backend."""
    def setUp(self):
        """Set up."""
        super(BaseTestCase, self).setUp()
        self.db_engine = create_engine("sqlite://")
        self.bkend = KilinkBackend(self.db_engine)
        config.load_file("configs/development.yaml")


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
            linkode_id=klnk.linkode_id).one()
        self.assertEqual(klnk.content, content)
        self.assertTrue(isinstance(klnk.linkode_id.encode("ascii"), bytes))
        self.assertEqual(klnk.parent, None)
        self.assertEqual(klnk.text_type, text_type)
    
    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = "some content"
        child_content = u"moño camión"
        klnk = self.bkend.create_kilink(parent_content, "type1")
        new_klnk = self.bkend.update_kilink(klnk.linkode_id, child_content,
                                            "type2")
        self.assertEqual(new_klnk.parent, klnk.linkode_id)
        self.assertGreater(new_klnk.timestamp, klnk.timestamp)
        self.assertEqual(new_klnk.text_type, "type2")
        
        parent = self.session.query(Kilink).filter_by(
            linkode_id=klnk.linkode_id).one()
        self.assertEqual(parent.content, parent_content)
        child = self.session.query(Kilink).filter_by(
            linkode_id=new_klnk.linkode_id).one()
        self.assertEqual(child.content, child_content)
    
    def test_update_bad_kilink(self):
        """No kilink to update."""
        self.assertRaises(KilinkNotFoundError, self.bkend.update_kilink,
                          "unexistant", "content", "")


class DataRetrievalTestCase(BaseTestCase):
    """Tests that cover the retrieval of data."""
    def test_getkilink_id_ok(self):
        """Get content for a kilink, indicating a good id."""
        # create a kilink, two contents
        klnk = self.bkend.create_kilink("content 1", "type1")
        new_klnk = self.bkend.update_kilink(klnk.linkode_id, "c2", "t2")
        
        # get content for both revisions
        klnk = self.bkend.get_kilink(klnk.linkode_id)
        self.assertEqual(klnk.content, "content 1")
        self.assertEqual(klnk.text_type, "type1")
        klnk = self.bkend.get_kilink(new_klnk.linkode_id)
        self.assertEqual(klnk.content, "c2")
        self.assertEqual(klnk.text_type, "t2")
    
    def test_getkilink_id_bad(self):
        """Get content for a kilink, indicating a bad id."""
        self.assertRaises(KilinkNotFoundError, self.bkend.get_kilink,
                          "bad linkode_id")
    
    def test_getkilink_tree_ok(self):
        # create a tree
        klnk = self.bkend.create_kilink("content 1", "t1")
        klnk2 = self.bkend.update_kilink(klnk.linkode_id, "content 2", "")
        self.bkend.update_kilink(klnk2.linkode_id, "content 3", "t3")
        self.bkend.update_kilink(klnk.linkode_id, "content 4", "")
        
        # get it and check structure: id, content, parent, timestamp
        tree = self.bkend._get_kilink_tree(klnk.root)
        self.assertEqual(tree[0].content, "content 1")
        self.assertEqual(tree[1].content, "content 2")
        self.assertEqual(tree[2].content, "content 3")
        self.assertEqual(tree[3].content, "content 4")
        self.assertEqual(tree[0].text_type, "t1")
        self.assertEqual(tree[1].text_type, "")
        self.assertEqual(tree[2].text_type, "t3")
        self.assertEqual(tree[3].text_type, "")
        for i, item in enumerate(tree, 1):
            self.assertTrue(isinstance(item.linkode_id, str))
            if item.parent is not None:
                self.assertTrue(isinstance(item.parent, str))
            self.assertTrue(isinstance(item.timestamp, datetime.datetime))
            self.assertEqual(item.order, i)
        self.assertEqual(tree[0].parent, None)  # root node
        
        # 2nd is child of root
        self.assertEqual(tree[1].parent, tree[0].linkode_id)
        # 3rd is child of 2nd
        self.assertEqual(tree[2].parent, tree[1].linkode_id)
        # 4th is child of root
        self.assertEqual(tree[3].parent, tree[0].linkode_id)
    
    def test_getkilink_tree_bad(self):
        """Get all the info for a kilink that does not exist"""
        self.assertRaises(
            KilinkNotFoundError, self.bkend._get_kilink_tree, 'linkode_id')
    
    def test_findroot_ok_one_node(self):
        """Get the root node for a kilink when there's only one."""
        # create a node
        orig_klnk = self.bkend.create_kilink("content", "type")
        
        # get it and check
        klnk = self.bkend._get_root_node(orig_klnk.linkode_id)
        self.assertEqual(klnk.linkode_id, orig_klnk.linkode_id)
        self.assertEqual(klnk.parent, None)
        self.assertEqual(klnk.content, "content")
        self.assertEqual(klnk.text_type, "type")
    
    def test_findroot_ok_two_nodes(self):
        """Get the root node for a kilink when there are several."""
        # create a couple of nodes
        orig_klnk = self.bkend.create_kilink("content", "type")
        self.bkend.update_kilink(orig_klnk.linkode_id, "c2", "")
        self.bkend.update_kilink(orig_klnk.linkode_id, "c3", "")
        
        # get it and check
        klnk = self.bkend._get_root_node(orig_klnk.linkode_id)
        self.assertEqual(klnk.linkode_id, orig_klnk.linkode_id)
        self.assertEqual(klnk.content, orig_klnk.content)
    
    def test_findroot_tree_bad(self):
        """Get the root node for a kilink that does not exist."""
        self.assertRaises(KilinkNotFoundError, self.bkend._get_root_node,
                          'linkode_id')


class IDGenTestCase(TestCase):
    """Test case for the id generator."""
    def test_type(self):
        """It must be a string."""
        newid = get_unique_id()
        self.assertTrue(isinstance(newid, str))
    
    def test_sanity(self):
        """Stupid sanity check."""
        ids = [get_unique_id() for _ in range(100)]
        self.assertEqual(len(set(ids)), 100)


class HelpersTestCase(BaseTestCase):
    """Tests for some random helpers."""
    def setUp(self):
        super(HelpersTestCase, self).setUp()
        _, self.tempfile = tempfile.mkstemp(prefix="test-temp-file")
        self.addCleanup(
            lambda: os.path.exists(self.tempfile) and os.remove(self.tempfile))
        config['version_file'] = self.tempfile
    
    def test_version_there(self):
        """TGet version"""
        with open(self.tempfile, "wt") as fh:
            fh.write("test version")
        resp = self.bkend.get_version()
        self.assertEqual(resp, "test version")
    
    def test_version_missing(self):
        """When version is missing"""
        os.remove(self.tempfile)
        resp = self.bkend.get_version()
        self.assertEqual(resp, "?")
    
    def test_version_assure_cached(self):
        """Version is cached"""
        with open(self.tempfile, "wt") as fh:
            fh.write("test version")
        resp = self.bkend.get_version()
        self.assertEqual(resp, "test version")
        
        # now remove the file, and response shouldn't change (it's cached!)
        os.remove(self.tempfile)
        resp = self.bkend.get_version()
        self.assertEqual(resp, "test version")
