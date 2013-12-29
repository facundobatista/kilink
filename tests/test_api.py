# encoding: utf8

# Copyright 2011-2013 Facundo Batista, Nicolás César
# All Rigths Reserved

"""API tests."""

import json

from unittest import TestCase

from mock import patch
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
        self.backend = kilink.kilinkbackend = backend.KilinkBackend(engine)
        self.app = kilink.app.test_client()

    def api_create(self, data, code=201):
        """Helper to hit the api to create."""
        r = self.app.post("/api/1/linkodes/", data=data)
        self.assertEqual(r.status_code, code)
        if code == 201:
            return json.loads(r.data)

    def api_update(self, kid, data, code=201):
        """Helper to hit the api to edit."""
        r = self.app.post("/api/1/linkodes/%s" % (kid,), data=data)
        self.assertEqual(r.status_code, code)
        return json.loads(r.data)

    def api_get(self, kid, revno, code=200):
        """Helper to hit the api to get."""
        url = "/api/1/linkodes/%s/%s" % (kid, revno)
        r = self.app.get(url)
        self.assertEqual(r.status_code, code)
        return json.loads(r.data)


class ApiTestCase(BaseTestCase):
    """Tests for API kilink creation and updating."""

    def test_create_simple(self):
        """Simple create."""
        content = u'Moñooo()?¿'
        text_type = "type1"
        datos = {'content': content, 'text_type': text_type}

        with patch.object(kilink, "metrics"):
            resp = self.api_create(data=datos)
            kilink.metrics.count.assert_called_with("api.create.ok", 1)

        klnk = self.backend.get_kilink(resp["linkode_id"], resp["revno"])
        self.assertEqual(klnk.content, content)
        self.assertEqual(klnk.text_type, text_type)

    def test_create_error(self):
        """Simple create."""
        content = u'Moñooo()?¿'
        text_type = "type1"
        datos = {'content': content, 'text_type': text_type}

        # make it fail!

        with patch.object(self.backend, 'create_kilink') as mock:
            mock.side_effect = ValueError("foo")
            with patch.object(kilink, "metrics"):
                self.api_create(data=datos, code=500)
                kilink.metrics.count.assert_called_with(
                    "api.create.error.ValueError", 1)

    def test_create_no_text_type(self):
        """Simple create."""
        content = u'Moñooo()?¿'
        datos = {'content': content}
        resp = self.api_create(data=datos)

        klnk = self.backend.get_kilink(resp["linkode_id"], resp["revno"])
        self.assertEqual(klnk.content, content)
        self.assertEqual(klnk.text_type, "")

    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = {'content': u'ÑOÑO', 'text_type': 'type1'}
        resp = self.api_create(data=parent_content)
        kid = resp['linkode_id']
        revno0 = resp["revno"]

        child_content = {
            'content': u'Moñito',
            'parent': revno0,
            'text_type': 'type2',
        }
        with patch.object(kilink, "metrics"):
            resp = self.api_update(kid, data=child_content)
            kilink.metrics.count.assert_called_with("api.update.ok", 1)
        revno1 = resp["revno"]

        klnk = self.backend.get_kilink(kid, revno1)
        self.assertEqual(klnk.content, u"Moñito")
        self.assertEqual(klnk.text_type, u"type2")

        child_content2 = {
            'content': u'Moñito2',
            'parent': revno0,
            'text_type': 'type3',
        }
        resp = self.api_update(kid, data=child_content2)
        revno2 = resp["revno"]

        klnk = self.backend.get_kilink(kid, revno2)
        self.assertEqual(klnk.content, u"Moñito2")
        self.assertEqual(klnk.text_type, u"type3")

        # all three are different
        self.assertEqual(len(set([revno0, revno1, revno2])), 3)

    def test_get_simple(self):
        """Get a kilink and revno content."""
        content = {'content': u'ÑOÑO', 'text_type': 'type'}
        resp = self.api_create(data=content)

        with patch.object(kilink, "metrics"):
            resp = self.api_get(resp['linkode_id'], resp['revno'])
            kilink.metrics.count.assert_called_with("api.get.ok", 1)

        self.assertEqual(resp["content"], u"ÑOÑO")
        self.assertEqual(resp["text_type"], u"type")
