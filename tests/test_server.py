# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

from StringIO import StringIO

from twisted.trial.unittest import TestCase

from kilink import kilink


class FakeRequest(object):
    """A fake request to patch Flask."""
    def __init__(self, **k):
        self.__dict__.update(k)


class FakeTemplate(object):
    """Store what was given to replace."""

    def __init__(self):
        self.called = {}
        self.rendered = object()

    def render(self, **k):
        """Fake render."""
        self.called.update(k)
        return self.rendered


class FakeBackend(object):
    """Test controllable backend."""

    kid = None
    def __init__(self):
        self.kid = None
        self.actions = []

    def create_kilink(self, content):
        return self.kid


class ServingTestCase(TestCase):
    """Tests for server."""

    def setUp(self):
        """Set up."""
        self.template = FakeTemplate()
        self.backend = FakeBackend()
        self.patch(kilink, "kilinkbackend", self.backend)

        # to check
        self.rendered = None
        self.patch(kilink, "render_template",
                   lambda *a, **k: setattr(self, "rendered", (a, k)))
        self.redirected = None
        self.patch(kilink, "redirect",
                   lambda *a, **k: setattr(self, "redirected", (a, k)))

    def test_root_page(self):
        """Root page."""
        kilink.index()
        a, k = self.rendered
        self.assertEqual(a, ("index.html",))
        self.assertEqual(k['value'], '')
        self.assertEqual(k['button_text'], 'Create kilink')
        self.assertEqual(k['user_action'], 'create')
        self.assertEqual(k['tree_info'], None)

    def test_serving_simple(self):
        """Serving a kilink with just its id."""
        self.backend.get_content = lambda *a: "foobar"
        self.backend.get_kilink_tree = lambda *a: []
        self.patch(kilink, "request", FakeRequest(args=dict(revno=1)))

        kilink.show("kid")

        a, k = self.rendered
        should_action = "edit?kid=kid&parent=1"
        self.assertEqual(a, ("index.html",))
        self.assertEqual(k['value'], 'foobar')
        self.assertEqual(k['button_text'], 'Save new version')
        self.assertEqual(k['user_action'], should_action)
        self.assertEqual(k['tree_info'], [])

    def test_serving_revno(self):
        """Serving a kilink with a revno."""
        self.backend.get_content = lambda *a: "foobar"
        self.backend.get_kilink_tree = lambda *a: []
        self.patch(kilink, "request", FakeRequest(args=dict(revno=87)))
        kilink.show("kid")

        a, k = self.rendered
        should_action = "edit?kid=kid&parent=87"
        self.assertEqual(a, ("index.html",))
        self.assertEqual(k['value'], 'foobar')
        self.assertEqual(k['button_text'], 'Save new version')
        self.assertEqual(k['user_action'], should_action)
        self.assertEqual(k['tree_info'], [])

    def test_create(self):
        """Create a kilink."""
        self.patch(kilink, "request", FakeRequest(form=dict(content=u"moño")))
        called = []
        self.backend.create_kilink = lambda c: called.append(c) or 'kilink_id'

        kilink.create()
        self.assertEqual(called[0], u"moño")
        a, k = self.redirected
        self.assertEqual(a, ("/k/kilink_id",))
        self.assertEqual(k, dict(code=303))

    def test_edit(self):
        """Edit a kilink."""
        form = dict(content=u"moño")
        args = dict(kid='kid', parent=23)
        self.patch(kilink, "request", FakeRequest(form=form, args=args))
        called = []
        self.backend.update_kilink = lambda *a: called.append(a) or 'newrev'

        kilink.edit()
        self.assertEqual(called[0], ("kid", 23, u"moño"))
        a, k = self.redirected
        self.assertEqual(a, ("/k/kid?revno=newrev",))
        self.assertEqual(k, dict(code=303))
