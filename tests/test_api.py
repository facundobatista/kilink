# encoding: utf8

"""API tests."""

from unittest import TestCase

#from kilink.backend import KilinkBackend, Kilink
#from kilink import *
import requests


class BaseTestCase(TestCase):
    """Base for all test using a API."""
    def setUp(self):
        """Set up."""
        super(BaseTestCase, self).setUp()
        self.kilink_create = 'http://localhost:5000/api/1/action/create'
        self.kilink_edit = 'http://localhost:5000/api/1/action/edit'
        self.kilink_get = 'http://localhost:5000/api/1/action/get'


class ApiTestCase(BaseTestCase):
    """Tests for API kilink creation and updating."""

    def test_create_simple(self):
        """Simple create."""
        datos = {'content': u'Moñooo()?¿'}
        r = requests.post(self.kilink_create, data=datos)
        self.assertTrue(r.ok)
        self.assertTrue(u'kilink_id' in r.json())

    def test_update_simple(self):
        """Update a kilink with new content."""
        parent_content = {'content': u'ÑOÑO'}
        p = requests.post(self.kilink_create, data=parent_content)
        kid = p.json()['kilink_id']

        child_content = {'content': u'Moñito', 'kid': kid, 'parent': 1}
        c = requests.post(self.kilink_edit, data=child_content)
        self.assertEqual(c.json().get('revno'), 2)

        child_content2 = {'content': u'Moñito2', 'kid': kid, 'parent': 1}
        c2 = requests.post(self.kilink_edit, data=child_content2)
        self.assertEqual(c2.json().get('revno'), 3)

    def test_get_simple(self):
        """Get a kilink and revno content."""
        content = {'content': u'ÑOÑO'}
        p = requests.post(self.kilink_create, data=content)
        kid = p.json()['kilink_id']
        get = {'kid': kid, 'revno': 1}
        c = requests.post(self.kilink_get, data=get)
        self.assertEqual(c.json().get('revno'), 1)
