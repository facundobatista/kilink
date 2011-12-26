# -*- coding: utf-8 -*-

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Pages server"""


import cgi

from mako.template import Template

import backend
import tools


class KilinkServer(object):
    """The pages server."""

    _servers = {
        '/': '_srv_root',
        '/action/create': '_srv_create',
        '/action/edit': '_srv_edit',
    }

    def __init__(self, template=None, klnkbkend=None):
        if template is None:
            template = Template(file('templates/index.html').read())
        self.template = template

        if klnkbkend is None:
            klnkbkend = backend.KilinkBackend()
        self.klnkbkend = klnkbkend

        # these are overwritten on every __call__
        self.start_response = None
        self.environ = {}

    def parse_qs(self, qs):
        """Parse the query string, simplifying it."""
        d = cgi.parse_qs(qs)
        for k, v in d.iteritems():
            d[k] = v[0]
        return d

    def __call__(self, environ, start_response, extra_data={}):
        path_info = environ['PATH_INFO']
        self.start_response = start_response
        self.environ = environ
        return self._dispatcher(path_info)

    def _dispatcher(self, path_info):
        """Generic dispatcher."""
        srv_name = self._servers.get(path_info)
        if srv_name is None:
            response = self._srv_default(path_info)
        else:
            srvr = getattr(self, srv_name)
            response = srvr()
        return response

    def _srv_root(self):
        """Serve the root page."""
        self.start_response('200 OK', [('Content-Type', 'text/html')])
        render_dict = {
            'value': '',
            'button_text': 'Create kilink',
            'user_action': 'create',
        }
        return [str(self.template.render(**render_dict))]

    def _srv_create(self):
        """Create a kilink."""
        post_data = self.environ['wsgi.input'].read()
        content = tools.magic_quote(post_data[8:]) # starts with 'content='
        kid = self.klnkbkend.create_kilink(content)
        self.start_response('303 see other', [('Location', "/" + kid)])
        return ''

    def _srv_edit(self):
        """Edit a kilink."""
        post_data = self.environ['wsgi.input'].read()
        content = tools.magic_quote(post_data[8:])
        qs = self.parse_qs(self.environ['QUERY_STRING'])
        kid = qs['kid']
        parent = int(qs['parent'])
        new_revno = self.klnkbkend.update_kilink(kid, parent, content)
        new_url = "/%s?revno=%s" % (kid, new_revno)
        self.start_response('303 see other', [('Location', new_url)])
        return ''

    def _srv_default(self, path_info):
        """Serve a kilink by default."""
        kid = path_info[1:]  # without the initial '/'
        qs = self.parse_qs(self.environ['QUERY_STRING'])
        revno = int(qs.get('revno', 1))

        action_url = 'edit?kid=%s&parent=%s' % (kid, revno)
        content = self.klnkbkend.get_content(kid, revno)

        self.start_response('200 OK', [('Content-Type', 'text/html')])
        render_dict = {
            'value': content,
            'button_text': 'Save new version',
            'user_action': action_url,
        }
        return [str(self.template.render(**render_dict))]
