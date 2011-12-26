#!/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Kilink FTW!"""

import cgi
import os
import sys

from flup.server.fcgi import WSGIServer
from mako.template import Template

import backend
import tools

FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

MAIN_PAGE = Template(file('templates/index.html').read())

klnkbkend = backend.KilinkBackend()


def kilink(environ, start_response, extra_data={}):
    """Kilink, :)"""
    path_info = environ['PATH_INFO']
    query_string = cgi.parse_qs(environ['QUERY_STRING'])
    render_dict = {'value':''}
    render_dict.update(extra_data)

    if path_info == '/':
        print "======= root"
        start_response('200 OK', [('Content-Type', 'text/html')])
        render_dict['button_text'] = 'Create kilink'
        render_dict['user_action'] = 'create'
        return [str(MAIN_PAGE.render(**render_dict))]

    if path_info == '/action/create':
        print "======= create"
        response = str(environ)
        post_data = environ['wsgi.input'].read()
        assert post_data[:8] == 'content='
        content = tools.magic_quote(post_data[8:])
        kid = klnkbkend.create_kilink(content)
        start_response('303 see other', [('Location', "/" + kid)])
        return ''

    if path_info == '/action/edit':
        response = str(environ)
        post_data = environ['wsgi.input'].read()
        assert post_data[:8] == 'content='
        content = tools.magic_quote(post_data[8:])
        kid = query_string['kid'][0]
        parent = int(query_string['parent'][0])
        print "======= EDIT!", kid, parent
        new_revno = klnkbkend.update_kilink(kid, parent, content)
        start_response('303 see other',
                       [('Location', "/%s?revno=%s" % (kid, new_revno))])
        return ''

    # serving a kilink
    print "======= serving"
    start_response('200 OK', [('Content-Type', 'text/html')])
    kid = path_info[1:]
    revno = int(query_string.get('revno', [1])[0])
    response = klnkbkend.get_content(kid, revno)
    render_dict.update({'value': response})
    render_dict['button_text'] = 'Save new version'
    render_dict['user_action'] = 'edit?kid=%s&parent=%s' % (kid, revno)
    return [MAIN_PAGE.render(**render_dict)]


def main(args_in, app_name="hello"):
    """Go girl."""
    socketfile = os.path.join(FCGI_SOCKET_DIR, 'kilink.socket' )

    try:
        srvr = WSGIServer(kilink, bindAddress=socketfile,
                          umask=FCGI_SOCKET_UMASK, multiplexed=True)
        srvr.run()
    finally:
        # clean up server socket file
        os.unlink(socketfile)

if __name__ == '__main__':
    main(sys.argv[1:])
