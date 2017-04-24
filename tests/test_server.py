# encoding: utf8

# Copyright 2011-2017 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

import json

from unittest import TestCase

from mock import patch
from sqlalchemy import create_engine

from kilink import kilink, backend


class FakeRequest(object):
    """A fake request to patch Flask."""

    def __init__(self, **k):
        self.__dict__.update(k)


class UnmockedServingTestCase(TestCase):
    """Tests for server not mocking anything."""

    def setUp(self):
        """Set up."""
        super(UnmockedServingTestCase, self).setUp()
        engine = create_engine("sqlite://")
        self.backend = backend.KilinkBackend(engine)
        kilink.kilinkbackend = self.backend
        self.app = kilink.app.test_client()

    def test_serving_base(self):
        """Serving a kilink, base."""
        klnk = self.backend.create_kilink("content", "type1")
        resp = self.app.get("/l/%s" % (klnk.linkode_id,))
        self.assertEqual(resp.headers['Cache-Control'], "public, max-age=0")


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

        _ctx = patch("kilink.kilink.redirect")
        self.mocked_redirect = _ctx.start()
        self.addCleanup(_ctx.stop)

    def test_root_page(self):
        """Root page."""
        kilink.index()

        k = {}
        k['content'] = ''
        k['button_text'] = 'Create linkode'
        k['linkode_info'] = ''
        k['tree_info'] = json.dumps(False)
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_serving_base(self):
        """Serving a kilink, base."""
        klnk = self.backend.create_kilink("content", "type1")
        with patch.object(kilink, "metrics"):
            self.app.get("/%s" % (klnk.linkode_id,))
            kilink.metrics.count.assert_called_with("server.show.ok", 1)

        tree = dict(
            contents=[],
            order=1,
            revno=klnk.linkode_id,
            linkode_id=klnk.linkode_id,
            parent=None,
            url="/%s" % (klnk.linkode_id,),
            timestamp=str(klnk.timestamp),
            selected=True,
        )

        k = {}
        k['content'] = 'content'
        k['button_text'] = 'Save new version'
        k['text_type'] = 'type1'
        k['linkode_info'] = str(klnk.linkode_id)
        k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.linkode_id
        k['timestamp'] = klnk.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.mocked_render.assert_called_once_with("_new.html", **k)

        self.mocked_render.reset_mock()
        self.app.get("/l/%s" % (klnk.linkode_id,))
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_serving_revno(self):
        """Serving a kilink with a revno."""
        klnk = self.backend.create_kilink("content", "type2")
        self.app.get("/%s" % (klnk.linkode_id,))

        tree = dict(
            contents=[],
            order=1,
            revno=klnk.linkode_id,
            linkode_id=klnk.linkode_id,
            parent=None,
            url="/%s" % (klnk.linkode_id,),
            timestamp=str(klnk.timestamp),
            selected=True,
        )

        k = {}
        k['content'] = 'content'
        k['button_text'] = 'Save new version'
        k['text_type'] = 'type2'
        k['linkode_info'] = str(klnk.linkode_id)
        k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.linkode_id
        k['timestamp'] = klnk.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.mocked_render.assert_called_once_with("_new.html", **k)

        self.mocked_render.reset_mock()
        self.app.get("/l/%s" % (klnk.linkode_id,))
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_create(self):
        """Create a kilink."""
        with patch.object(kilink, "metrics"):
            self.app.post("/", data=dict(content="content", text_type="type1"))
            kilink.metrics.count.assert_called_with("server.create.ok", 1)

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).one()

        # compare
        self.assertEqual(created.content, "content")
        self.assertEqual(created.text_type, "type1")
        url = "/%s" % (created.linkode_id,)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_create_auto_text(self):
        """Create a kilink, sending data from autodetection."""
        data = dict(content="content", text_type="auto: type1")
        self.app.post("/", data=data)

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).one()

        # compare
        self.assertEqual(created.content, "content")
        self.assertEqual(created.text_type, "type1")
        url = "/%s" % (created.linkode_id,)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_update_base(self):
        """Update a kilink from it's id."""
        klnk = self.backend.create_kilink("content", "")

        url = "/%s" % (klnk.linkode_id,)
        with patch.object(kilink, "metrics"):
            self.app.post(url, data=dict(content=u"moño", text_type="type1"))
            kilink.metrics.count.assert_called_with("server.update.ok", 1)

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).filter_by(
            parent=klnk.linkode_id).one()

        # compare
        self.assertEqual(created.content, u"moño")
        self.assertEqual(created.text_type, "type1")
        url = "/%s" % (created.linkode_id,)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_update_double_id(self):
        """Update a kilink from the double id (the old way)."""
        klnk = self.backend.create_kilink("content", "")
        klnk = self.backend.update_kilink(klnk.linkode_id, "c2", "t2")

        url = "/dontcare/%s" % (klnk.linkode_id,)
        self.app.post(url, data=dict(content=u"moño", text_type="type2"))

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).filter_by(
            parent=klnk.linkode_id).one()

        # compare
        self.assertEqual(created.content, u"moño")
        self.assertEqual(created.text_type, "type2")
        url = "/%s" % (created.linkode_id,)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_invalid_base(self):
        self.app.get('/invalid')
        self.mocked_render.assert_called_once_with("_404.html")

    def test_invalid_klnk(self):
        self.app.get('/invalid/123')
        self.mocked_render.assert_called_once_with("_404.html")
