# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

from StringIO import StringIO

from twisted.trial.unittest import TestCase

from kilink.server import KilinkServer


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
        self.klnk = KilinkServer(template=self.template,
                                 klnkbkend=self.backend)
        self.klnk.start_response = self._start_resp

    def _start_resp(self, code, headers):
        """Store response."""
        self._resp_code = code
        self._resp_headers = headers

    def test_parse_qs(self):
        """Check the query string parser."""
        r = self.klnk.parse_qs("a=b&c=3")
        self.assertEqual(r, dict(a='b', c='3'))

    def test_root_page(self):
        """Root page."""
        response = self.klnk._dispatcher('/')
        self.assertEqual(self.template.called['value'], '')
        self.assertEqual(self.template.called['button_text'], 'Create kilink')
        self.assertEqual(self.template.called['user_action'], 'create')
        self.assertEqual(self._resp_code, '200 OK')
        self.assertIn(('Content-Type', 'text/html'), self._resp_headers)
        self.assertEqual(response, [str(self.template.rendered)])

    def test_serving_simple(self):
        """Serving a kilink with just its id."""
        called = []
        self.backend.get_content = lambda *a: called.extend(a) or "foobar"
        self.klnk.environ['QUERY_STRING'] = ''
        response = self.klnk._dispatcher('/kilink_id')
        self.assertEqual(self.template.called['value'], 'foobar')
        self.assertEqual(self.template.called['button_text'],
                         'Save new version')
        self.assertEqual(self.template.called['user_action'],
                         'edit?kid=kilink_id&parent=1')
        self.assertEqual(self._resp_code, '200 OK')
        self.assertIn(('Content-Type', 'text/html'), self._resp_headers)
        self.assertEqual(response, [str(self.template.rendered)])
        self.assertEqual(called, ['kilink_id', 1])

    def test_serving_revno(self):
        """Serving a kilink with a revno."""
        called = []
        self.backend.get_content = lambda *a: called.extend(a) or "foobar"
        self.klnk.environ['QUERY_STRING'] = 'revno=87'
        response = self.klnk._dispatcher('/kilink_id')
        self.assertEqual(self.template.called['value'], 'foobar')
        self.assertEqual(self.template.called['button_text'],
                         'Save new version')
        self.assertEqual(self.template.called['user_action'],
                         'edit?kid=kilink_id&parent=87')
        self.assertEqual(self._resp_code, '200 OK')
        self.assertIn(('Content-Type', 'text/html'), self._resp_headers)
        self.assertEqual(response, [str(self.template.rendered)])
        self.assertEqual(called, ['kilink_id', 87])

    def test_create(self):
        """Create a kilink."""
        self.klnk.environ['wsgi.input'] = StringIO("content=foobar")
        called = []
        self.backend.create_kilink = lambda c: called.append(c) or 'kilink_id'
        response = self.klnk._dispatcher('/action/create')
        self.assertEqual(self._resp_code, '303 see other')
        self.assertIn(('Location', '/kilink_id'), self._resp_headers)
        self.assertEqual(response, '')
        self.assertEqual(called, ['foobar'])

    def test_edit(self):
        """Edit a kilink."""
        self.klnk.environ['wsgi.input'] = StringIO("content=newcontent")
        self.klnk.environ['QUERY_STRING'] = 'kid=klnkid&parent=17'
        called = []
        self.backend.update_kilink = lambda *a: called.extend(a) or 23
        response = self.klnk._dispatcher('/action/edit')
        self.assertEqual(self._resp_code, '303 see other')
        self.assertIn(('Location', '/klnkid?revno=23'), self._resp_headers)
        self.assertEqual(response, '')
        self.assertEqual(called, ['klnkid', 17, 'newcontent'])
