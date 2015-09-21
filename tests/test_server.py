# encoding: utf8

# Copyright 2011-2013 Facundo Batista, Nicolás César
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
        resp = self.app.get("/l/%s" % (klnk.kid,))
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
        k['value'] = ''
        k['button_text'] = 'Create linkode'
        k['kid_info'] = ''
        k['tree_info'] = json.dumps(False)
        k['max_chars'] = 5000
        k['max_lines'] = 2000
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_serving_base(self):
        """Serving a kilink, base."""
        klnk = self.backend.create_kilink("content", "type1")
        with patch.object(kilink, "metrics"):
            self.app.get("/%s" % (klnk.kid,))
            kilink.metrics.count.assert_called_with("server.show.ok", 1)

        tree = dict(
            contents=[],
            order=1,
            revno=klnk.revno,
            parent=None,
            url="/%s/%s" % (klnk.kid, klnk.revno),
            timestamp=str(klnk.timestamp),
            selected=True,
        )

        k = {}
        k['value'] = 'content'
        k['button_text'] = 'Save new version'
        k['text_type'] = 'type1'
        k['kid_info'] = "%s/%s" % (klnk.kid, klnk.revno)
        # k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.revno
        k['timestamp'] = klnk.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        k['max_chars'] = 5000
        k['max_lines'] = 2000
        self.mocked_render.assert_called_once_with("_new.html", **k)

        self.mocked_render.reset_mock()
        self.app.get("/l/%s" % (klnk.kid,))
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_serving_revno(self):
        """Serving a kilink with a revno."""
        klnk = self.backend.create_kilink("content", "type2")
        self.app.get("/%s/%s" % (klnk.kid, klnk.revno))

        tree = dict(
            contents=[],
            order=1,
            revno=klnk.revno,
            parent=None,
            url="/%s/%s" % (klnk.kid, klnk.revno),
            timestamp=str(klnk.timestamp),
            selected=True,
        )

        k = {}
        k['value'] = 'content'
        k['button_text'] = 'Save new version'
        k['text_type'] = 'type2'
        k['kid_info'] = "%s/%s" % (klnk.kid, klnk.revno)
        #k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.revno
        k['timestamp'] = klnk.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        k['max_chars'] = 5000
        k['max_lines'] = 2000
        self.mocked_render.assert_called_once_with("_new.html", **k)

        self.mocked_render.reset_mock()
        self.app.get("/l/%s/%s" % (klnk.kid, klnk.revno))
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
        url = "/%s" % (created.kid,)
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
        url = "/%s" % (created.kid,)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_update_base(self):
        """Update a kilink from it's base node."""
        klnk = self.backend.create_kilink("content", "")

        url = "/%s" % (klnk.kid,)
        with patch.object(kilink, "metrics"):
            self.app.post(url, data=dict(content=u"moño", text_type="type1"))
            kilink.metrics.count.assert_called_with("server.update.ok", 1)

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).filter_by(
            kid=klnk.kid, parent=klnk.revno).one()

        # compare
        self.assertEqual(created.content, u"moño")
        self.assertEqual(created.text_type, "type1")
        url = "/%s/%s" % (created.kid, created.revno)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_update_revno(self):
        """Update a kilink from it's base node."""
        klnk = self.backend.create_kilink("content", "")
        klnk = self.backend.update_kilink(klnk.kid, klnk.revno, "c2", "t2")

        url = "/%s/%s" % (klnk.kid, klnk.revno)
        self.app.post(url, data=dict(content=u"moño", text_type="type2"))

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).filter_by(
            kid=klnk.kid, parent=klnk.revno).one()

        # compare
        self.assertEqual(created.content, u"moño")
        self.assertEqual(created.text_type, "type2")
        url = "/%s/%s" % (created.kid, created.revno)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_invalid_base(self):
        self.app.get('/invalid')
        self.mocked_render.assert_called_once_with("_404.html")

    def test_invalid_klnk(self):
        self.app.get('/invalid/123')
        self.mocked_render.assert_called_once_with("_404.html")
