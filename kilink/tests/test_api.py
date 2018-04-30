# encoding: utf8

# Copyright 2011-2018 Facundo Batista, Nicolás César
# All Rights Reserved

"""API tests."""

import json
import datetime
from unittest import TestCase, mock

from sqlalchemy import create_engine

from kilink import app as kilink
from kilink.app.config import config
from kilink.app import backend
from kilink.app.metrics import metrics


class _ANY(object):
    """A helper object that compares equal to everything."""
    def __eq__(self, other):
        return True
    
    def __ne__(self, other):
        return False
    
    def __repr__(self):
        return '<ANY>'


anything = _ANY()


class BaseTestCase(TestCase):
    """Base for all test using a API."""
    def setUp(self):
        """Set up."""
        super(BaseTestCase, self).setUp()
        config.load_file("configs/development.yaml")
        engine = create_engine("sqlite://")
        self.app = kilink.app.test_client()
        test_engine = backend.KilinkBackend(engine)
        self.app.kilinkbackend = kilink.linkode.kilinkbackend = test_engine
    
    def api_create(self, data, code=201):
        """Helper to hit the api to create."""
        response = self.app.post("/api/1/linkodes/", data=data)

        self.assertEqual(response.status_code, code)
        if code == 201:
            return response.get_json()
    
    def api_update(self, linkode_id, data, code=201):
        """Helper to hit the api to edit."""
        url = "/api/1/linkodes/%s" % (linkode_id,)
        response = self.app.post(url, data=data)
        self.assertEqual(response.status_code, code)
        return response.get_json()
    
    def api_get(self, linkode_id, revno=None, code=200):
        """Helper to hit the api to get."""
        if revno is None:
            url = "/api/1/linkodes/%s" % (linkode_id,)
        else:
            url = "/api/1/linkodes/%s/%s" % (linkode_id, revno)
        response = self.app.get(url)
        
        self.assertEqual(response.status_code, code)
        return response.get_json()


class ApiTestCase(BaseTestCase):
    """Tests for API kilink creation and updating."""
    maxDiff = None
    
    def test_create_simple(self):
        """Simple create."""
        content = u'Moñooo()?¿'
        text_type = "type1"
        datos = {'content': content, 'text_type': text_type}
        
        with mock.patch.object(metrics, "count"):
            resp = self.api_create(data=datos)
            metrics.count.assert_called_with("api.create.ok", 1)
        klnk = self.app.kilinkbackend.get_kilink(resp["linkode_id"])
        
        self.assertEqual(klnk.content, content)
        self.assertEqual(klnk.text_type, text_type)
        self.assertLess(klnk.timestamp, datetime.datetime.utcnow())
        
    def test_create_error(self):
        """Simple create with error"""
        content = u'Moñooo()?¿'
        text_type = "type1"
        datos = {'content': content, 'text_type': text_type}
        
        # make it fail!
        
        with mock.patch.object(self.app.kilinkbackend, 'create_kilink') as mocked:
            mocked.side_effect = ValueError("foo")
            with mock.patch.object(metrics, "count"):
                self.api_create(data=datos, code=500)
                metrics.count.assert_called_with(
                    "api.create.error.ValueError", 1)
    
    def test_create_no_text_type(self):
        """Simple createwith not text type"""
        content = u'Moñooo()?¿'
        datos = {'content': content}
        resp = self.api_create(data=datos)
        
        klnk = self.app.kilinkbackend.get_kilink(resp["linkode_id"])
        self.assertEqual(klnk.content, content)
        self.assertEqual(klnk.text_type, "")
        self.assertLess(klnk.timestamp, datetime.datetime.utcnow())
    
    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = {'content': u'ÑOÑO', 'text_type': 'type1'}
        resp = self.api_create(data=parent_content)
        linkode_id = resp['linkode_id']
        revno0 = resp["revno"]
        
        child_content = {
            'content': u'Moñito',
            'parent': revno0,
            'text_type': 'type2',
        }
        with mock.patch.object(metrics, "count"):
            resp = self.api_update(linkode_id, data=child_content)
            metrics.count.assert_called_with("api.update.ok", 1)
        revno1 = resp["revno"]
        
        klnk = self.app.kilinkbackend.get_kilink(revno1)
        self.assertEqual(klnk.content, u"Moñito")
        self.assertEqual(klnk.text_type, u"type2")
        self.assertLess(klnk.timestamp, datetime.datetime.utcnow())
        
        child_content2 = {
            'content': u'Moñito2',
            'parent': revno0,
            'text_type': 'type3',
        }
        resp = self.api_update(linkode_id, data=child_content2)
        revno2 = resp["revno"]
        
        klnk = self.app.kilinkbackend.get_kilink(revno2)
        self.assertEqual(klnk.content, u"Moñito2")
        self.assertEqual(klnk.text_type, u"type3")
        self.assertLess(klnk.timestamp, datetime.datetime.utcnow())
        
        # all three are different
        self.assertEqual(len({revno0, revno1, revno2}), 3)
    
    def test_get_simple(self):
        """Get a kilink and revno content."""
        content = {'content': u'ÑOÑO', 'text_type': 'type'}
        resp = self.api_create(data=content)
        
        linkode_id = resp['linkode_id']
        revno = resp['revno']
        with mock.patch.object(metrics, "count"):
            resp = self.api_get(linkode_id, revno)
            metrics.count.assert_called_with("api.get.ok", 1)
        
        self.assertEqual(resp["content"], u"ÑOÑO")
        self.assertEqual(resp["text_type"], u"type")
        self.assertEqual(resp["timestamp"], anything)
        self.assertEqual(resp['tree'], {
            u'revno': revno,
            u'linkode_id': linkode_id,
            u'timestamp': anything,
            u'parent': None,
            u'url': "/{}".format(linkode_id),
            u'selected': True,
            u'order': 1,
            u'contents': [],
        })
    
    def test_get_norevno(self):
        """Get a kilink and revno content."""
        content = {'content': u'ÑOÑO', 'text_type': 'type'}
        resp = self.api_create(data=content)
        linkode_id = resp['linkode_id']
        revno = resp['revno']
        
        with mock.patch.object(metrics, "count"):
            resp = self.api_get(linkode_id)
            metrics.count.assert_called_with("api.get.ok", 1)
        
        self.assertEqual(resp["content"], u"ÑOÑO")
        self.assertEqual(resp["text_type"], u"type")
        self.assertEqual(resp["timestamp"], anything)
        self.assertEqual(resp['tree'], {
            u'linkode_id': linkode_id,
            u'revno': revno,
            u'timestamp': anything,
            u'parent': None,
            u'url': "/{}".format(linkode_id),
            u'selected': True,
            u'order': 1,
            u'contents': [],
        })
    
    def test_tree(self):
        """Get a good tree when getting a node."""
        
        resp = self.api_create(data={'content': "content 0", 'text_type': ''})
        linkode_id = resp['linkode_id']
        root_revno = resp['revno']
        
        resp = self.api_update(
            linkode_id=linkode_id,
            data={
                'content': "content 1", 'text_type': '', 'parent': root_revno}
        )
        child1_revno = resp['revno']
        
        resp = self.api_update(
            linkode_id=linkode_id,
            data={
                'content': "content 11", 'text_type': '',
                'parent': child1_revno}
        )
        child11_revno = resp['revno']
        
        resp = self.api_update(
            linkode_id=linkode_id,
            data={
                'content': "content 2", 'text_type': '', 'parent': root_revno}
        )
        child2_revno = resp['revno']
        
        # get the info
        resp = self.api_get(linkode_id)
        self.assertEqual(resp['tree'], {
            u'revno': root_revno,
            u'linkode_id': linkode_id,
            u'parent': None,
            u'url': "/{}".format(linkode_id),
            u'timestamp': anything,
            u'selected': True,
            u'order': 1,
            u'contents': [{
                u'revno': child1_revno,
                u'linkode_id': child1_revno,
                u'parent': root_revno,
                u'url': "/{}".format(child1_revno),
                u'timestamp': anything,
                u'selected': False,
                u'order': 2,
                u'contents': [{
                    u'revno': child11_revno,
                    u'linkode_id': child11_revno,
                    u'parent': child1_revno,
                    u'url': "/{}".format(child11_revno),
                    u'timestamp': anything,
                    u'selected': False,
                    u'order': 3,
                    u'contents': []
                }],
            }, {
                u'revno': child2_revno,
                u'linkode_id': child2_revno,
                u'parent': root_revno,
                u'url': "/{}".format(child2_revno),
                u'timestamp': anything,
                u'selected': False,
                u'order': 4,
                u'contents': [],
            }]
        })
    
    def test_invalid_kilink(self):
        resp_klnk = self.api_get('invalid', revno=1, code=404)
        resp_base = self.api_get('invalid', code=404)
        
        self.assertIn('message', resp_base)
        self.assertIn('message', resp_klnk)
    
    def test_too_large_content(self):
        """Content data too large."""
        content = u'Moñooo()?¿' + '.' * config["max_payload"]
        text_type = "type1"
        datos = {'content': content, 'text_type': text_type}
        resp = self.api_create(data=datos, code=413)
