# encoding: utf8

# Copyright 2011-2018 Facundo Batista, Nicolás César
# All Rights Reserved

"""Some tests for the serving part."""

from unittest import TestCase, mock

from sqlalchemy import create_engine

from kilink.kilink import kilink, backend


class ServingTestCase(TestCase):
    """Tests for server."""

    def setUp(self):
        """Set up."""
        super(ServingTestCase, self).setUp()
        engine = create_engine("sqlite://")
        self.backend = backend.KilinkBackend(engine)
        kilink.kilinkbackend = self.backend
        self.app = kilink.app.test_client()

        _ctx = mock.patch("kilink.kilink.kilink.render_template")
        self.mocked_render = _ctx.start()
        self.addCleanup(_ctx.stop)

    def test_root_page(self):
        """Root page."""
        kilink.index()

        self.mocked_render.assert_called_once_with("_new.html")
