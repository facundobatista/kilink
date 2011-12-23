#!/bin/env python
# -*- coding: utf-8 -*-

"""Kilink FTW!"""

import os
import re
import sys

from flup.server.fcgi import WSGIServer
from mako.template import Template

import backend

FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

MAIN_PAGE = Template(file('templates/index.html').read())

klnkbkend = backend.KilinkBackend()


def magic_quote(text):
    """Magic! FIXME: need explanation, and tests!!"""
    response = []
    text = iter(text)
    while True:
        try:
            char = text.next()
        except StopIteration:
            break

        if char != '%':
            response.append(char)
            continue

        head = int(text.next() + text.next(), 16)
        if head <= 127:
            response.append("&#%d;" % head)
            continue

        if 192 <= head <= 223:
            assert text.next() == '%'
            c2 = int(text.next() + text.next(), 16)
            u = chr(head) + chr(c2)
            response.append("&#%d;" % ord(u.decode("utf8")))
            continue

        if 224 <= head <= 239:
            assert text.next() == '%'
            c2 = int(text.next() + text.next(), 16)
            assert text.next() == '%'
            c3 = int(text.next() + text.next(), 16)
            u = chr(head) + chr(c2) + chr(c3)
            response.append("&#%d;" % ord(u.decode("utf8")))
            continue

        if 240 <= head <= 247:
            assert text.next() == '%'
            c2 = int(text.next() + text.next(), 16)
            assert text.next() == '%'
            c3 = int(text.next() + text.next(), 16)
            assert text.next() == '%'
            c4 = int(text.next() + text.next(), 16)
            u = chr(head) + chr(c2) + chr(c3) + chr(c4)
            response.append("&#%d;" % ord(u.decode("utf8")))
            continue

        raise ValueError("Not recognized text format: %r" % ("".join(text),))
    return "".join(response)



def kilink(environ, start_response, extra_data={}):
    """Kilink, :)"""
    path_info = environ['PATH_INFO']
    query_string = environ['QUERY_STRING']
    render_dict={'value':''}
    render_dict.update(extra_data)

    if path_info == '/':
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [str(MAIN_PAGE.render(**render_dict))]

    if path_info == '/action/create':
        response = str(environ)
        post_data = environ['wsgi.input'].read()
        assert post_data[:8] == 'content='
        content = magic_quote(post_data[8:])
        kid = klnkbkend.create_kilink(content)
        start_response('303 see other', [('Location', "/" + kid)])
        return ''

    # serving a kilink
    start_response('200 OK', [('Content-Type', 'text/html')])
    kid = path_info[1:]
    response = klnkbkend.get_content(kid, 1)
    render_dict.update({'value': response})
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
