# encoding: utf8

"""API tests."""

import json

from unittest import TestCase

from sqlalchemy import create_engine

from kilink import kilink, backend
from kilink.config import config


class BaseTestCase(TestCase):
    """Base for all test using a API."""
    def setUp(self):
        """Set up."""
        super(BaseTestCase, self).setUp()
        config.load_file("configs/development.yaml")
        engine = create_engine("sqlite://")
        kilink.kilinkbackend = backend.KilinkBackend(engine)
        self.app = kilink.app.test_client()

    def api_create(self, data, code=201):
        """Helper to hit the api to create."""
        r = self.app.post("/api/1/kilinks", data=data)
        self.assertEqual(r.status_code, code)
        return json.loads(r.data)

    def api_update(self, data, code=201):
        """Helper to hit the api to edit."""
        r = self.app.post("/api/1/kilinks", data=data)
        self.assertEqual(r.status_code, code)
        return json.loads(r.data)

    def api_get(self, kid, revno, code=200):
        """Helper to hit the api to get."""
        url = "/api/1/kilinks/%s/%s" % (kid, revno)
        r = self.app.get(url)
        self.assertEqual(r.status_code, code)
        return json.loads(r.data)


class ApiTestCase(BaseTestCase):
    """Tests for API kilink creation and updating."""

    def test_create_simple(self):
        """Simple create."""
        datos = {'content': u'Moñooo()?¿'}
        resp = self.api_create(data=datos)
        self.assertTrue(u'kilink_id' in resp)
        self.assertTrue(u'revno' in resp)

    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = {'content': u'ÑOÑO'}
        resp = self.api_create(data=parent_content)
        kid = resp['kilink_id']
        revno0 = resp["revno"]

        child_content = {
            'content': u'Moñito',
            'kid': kid,
            'parent': revno0,
        }
        resp = self.api_update(data=child_content)
        revno1 = resp["revno"]

        child_content2 = {
            'content': u'Moñito2',
            'kid': kid,
            'parent': revno0,
        }
        resp = self.api_update(data=child_content2)
        revno2 = resp["revno"]

        # all three are different
        self.assertEqual(len(set([revno0, revno1, revno2])), 3)

    def test_get_simple(self):
        """Get a kilink and revno content."""
        content = {'content': u'ÑOÑO'}
        resp = self.api_create(data=content)
        resp = self.api_get(resp['kilink_id'], resp['revno'])
        self.assertEqual(resp["content"], u"ÑOÑO")
