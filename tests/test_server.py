# encoding: utf8

# Copyright 2011-2017 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

from unittest import TestCase

from mock import patch
from sqlalchemy import create_engine

from kilink import kilink, backend


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

        # _ctx = patch("kilink.kilink.redirect")
        # self.mocked_redirect = _ctx.start()
        # self.addCleanup(_ctx.stop)

    def test_root_page(self):
        """Root page."""
        kilink.index()

        self.mocked_render.assert_called_once_with("_new.html")
