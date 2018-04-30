# encoding: utf8

# Copyright 2011-2018 Facundo Batista, Nicolás César
# All Rights Reserved

"""Some tests for the serving part."""

from unittest import TestCase, mock

from sqlalchemy import create_engine

from kilink.app import backend, linkode


class ServingTestCase(TestCase):
    """Tests for server."""

    def setUp(self):
        """Set up."""
        super(ServingTestCase, self).setUp()
        engine = create_engine("sqlite://")
        self.backend = backend.KilinkBackend(engine)
        linkode.kilinkbackend = self.backend
        self.app = linkode.app.test_client()

        _ctx = mock.patch("kilink.app.linkode.render_template")
        self.mocked_render = _ctx.start()
        self.addCleanup(_ctx.stop)

    def test_root_page(self):
        """Root page."""
        linkode.index()

        self.mocked_render.assert_called_once_with("_new.html")
