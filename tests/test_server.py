# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
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
        k['button_text'] = 'Create kilink'
        k['user_action'] = 'create'
        k['tree_info'] = []
        self.mocked_render.assert_called_once_with("index.html", **k)

    def test_serving_revno(self):
        """Serving a kilink with a revno."""
        klnk = self.backend.create_kilink("content")
        with patch("kilink.kilink.request") as m:
            m.args = dict(revno=klnk.revno)
            kilink.show(klnk.kid)

        tree = [[1, -1, klnk.revno, "/k/%s?revno=%s" % (klnk.kid, klnk.revno),
                str(klnk.timestamp)]]
        k = {}
        k['value'] = 'content'
        k['button_text'] = 'Save new version'
        k['user_action'] = "edit?kid=%s&parent=%s" % (klnk.kid, klnk.revno)
        k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.revno
        self.mocked_render.assert_called_once_with("index.html", **k)

    def test_create(self):
        """Create a kilink."""
        with patch("kilink.kilink.request") as m:
            m.form = dict(content="content")
            kilink.create()

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).one()

        # compare
        url = "/k/%s?revno=%s" % (created.kid, created.revno)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_edit(self):
        """Edit a kilink."""
        #form = dict(content=u"moño")
        #self.patch(kilink, "request", FakeRequest(form=form, args=args))
        #called = []
        #self.backend.update_kilink = lambda *a: called.append(a) or 'newrev'

        #kilink.edit()
        #self.assertEqual(called[0], ("kid", 23, u"moño"))
        #a, k = self.redirected
        #self.assertEqual(a, ("/k/kid?revno=newrev",))
        #self.assertEqual(k, dict(code=303))


        klnk = self.backend.create_kilink("content")

        with patch("kilink.kilink.request") as m:
            m.form = dict(content=u"moño")
            m.args = dict(kid=klnk.kid, parent=klnk.revno)
            kilink.edit()

        # get what was created, to compare
        created = self.backend.session.query(backend.Kilink).filter_by(
            kid=klnk.kid, parent=klnk.revno).one()

        # compare
        url = "/k/%s?revno=%s" % (created.kid, created.revno)
        self.mocked_redirect.assert_called_once_with(url, code=303)
