#!/bin/env python
# -*- coding: utf-8 -*-

"""Kilink FTW!"""

import cgi
import os
import sys

import backend

from flup.server.fcgi import WSGIServer

FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

MAIN_PAGE = file('templates/index.html').read()

klnkbkend = backend.KilinkBackend()

def kilink(environ, start_response):
    """Kilink, :)"""
    path_info = environ['PATH_INFO']
    query_string = environ['QUERY_STRING']

    if path_info == '/':
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [MAIN_PAGE]

    if path_info == '/action/create':
        response = str(environ)
        post_data = environ['wsgi.input'].read()
        assert post_data[:8] == 'content='
        content = post_data[8:]
        kid = klnkbkend.create_kilink(content)
        start_response('303 see other', [('Location', "/" + kid)])
        return ''

    # serving a kilink
    start_response('200 OK', [('Content-Type', 'text/plain')])
    kid = path_info[1:]
    response = klnkbkend.get_content(kid, 1)
    return [response]


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
