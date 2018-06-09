# encoding: utf8

# Copyright 2011-2017 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

import json
from unittest import TestCase

from mock import patch
from sqlalchemy import create_engine

from kilink import kilink, backend
from kilink.config import config


class ServingTestCase(TestCase):
    """Tests for server."""

    def setUp(self):
        """Set up."""
        super(ServingTestCase, self).setUp()
        engine = create_engine("sqlite://")
        self.backend = backend.KilinkBackend(engine)
        kilink.kilinkbackend = self.backend
        self.app = kilink.app.test_client()

        _ctx = patch("kilink.kilink.render_template")
        self.mocked_render = _ctx.start()
        self.addCleanup(_ctx.stop)

        config.load_file("configs/development.yaml")

        # _ctx = patch("kilink.kilink.redirect")
        # self.mocked_redirect = _ctx.start()
        # self.addCleanup(_ctx.stop)

    def test_root_page(self):
        """Root page."""
        kilink.index()

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
