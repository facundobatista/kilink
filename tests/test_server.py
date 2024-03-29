# Copyright 2011-2021 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

import json
from unittest import TestCase
from unittest.mock import patch

from sqlalchemy import create_engine

from kilink import main, backend
from kilink.config import config


class ServingTestCase(TestCase):
    """Tests for server."""

    def setUp(self):
        """Set up."""
        super(ServingTestCase, self).setUp()
        engine = create_engine("sqlite://")
        self.backend = backend.KilinkBackend(engine)
        main.kilinkbackend = self.backend
        self.app = main.app.test_client()

        _ctx = patch("kilink.main.render_template")
        self.mocked_render = _ctx.start()
        self.addCleanup(_ctx.stop)

        config.load_file("configs/development.yaml")

    def test_root_page(self):
        """Root page."""
        main.index()

        self.mocked_render.assert_called_once_with("_new.html")

    def test_deliver_plain(self):
        # create a linkode
        resp = self.app.post("/api/1/linkodes/", data={'content': u'ÑOÑO', 'text_type': 'type'})
        assert resp.status_code == 201
        linkode_id = json.loads(resp.data)['linkode_id']

        url = "/#{}".format(linkode_id)
        resp = self.app.get(url, headers={'Accept': 'text/plain'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode("utf8"), u"ÑOÑO")
        self.assertEqual(resp.headers['Content-Type'], 'text/type')

    def test_deliver_plain_with_revno(self):
        # create a linkode, and update it
        resp = self.app.post("/api/1/linkodes/", data={'content': u'ÑOÑO', 'text_type': 'type'})
        assert resp.status_code == 201
        content = json.loads(resp.data)
        linkode_id = content['linkode_id']
        root_revno = content['revno']
        resp = self.app.post(
            "/api/1/linkodes/%s" % (linkode_id,),
            data={'content': u'other', 'text_type': 'type2', 'parent': root_revno})
        assert resp.status_code == 201
        content = json.loads(resp.data)
        child_revno = content['revno']

        url = "/{}/{}".format(linkode_id, child_revno)
        resp = self.app.get(url, headers={'Accept': 'text/plain'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode("utf8"), u"other")
        self.assertEqual(resp.headers['Content-Type'], 'text/type2')
