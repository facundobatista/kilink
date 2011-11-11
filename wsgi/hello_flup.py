#!/bin/env python

"""Kilink FTW!"""

import cgi
import os
import sys

import backend

from flup.server.fcgi import WSGIServer

FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

MAIN_PAGE = """
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <title>Kilink</title>
</head>
<body>

<h1 id="title">Kilink</h1>

<form action="/create" method="POST" id="pasteform" name="pasteform">
<textarea id="id_content" rows="20" cols="80" name="content"></textarea>
<br/>
<input type="submit" value="Create kilink" />
</form>

</body> </html>
"""


def myapp(environ, start_response):
    """Generic handler."""
    start_response('200 OK', [('Content-Type', 'text/plain')])
    path_info = environ['PATH_INFO']
    query_string = environ['QUERY_STRING']

    # convert to something usable
    method_name = path_info[1:]
    kwargs = dict((k, v[0]) for k, v in cgi.parse_qs(query_string).iteritems())
    meth = getattr(backend, method_name)
    result = meth(**kwargs)
    return [str(result)]


def kilink(environ, start_response):
    """Kilink, :)"""
    start_response('200 OK', [('Content-Type', 'text/html')])
    path_info = environ['PATH_INFO']
    query_string = environ['QUERY_STRING']

    if path_info == '/':
        response = MAIN_PAGE
    elif path_info == '/create':
        response = str(environ)
    else:
        response = "Oops"
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
