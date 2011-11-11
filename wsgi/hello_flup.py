#!/bin/env python

"""Kilink FTW!"""

import cgi
import os
import sys

import backend

from flup.server.fcgi import WSGIServer

#FCGI_LISTEN_ADDRESS = ('localhost', 9000)
FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

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


def main(args_in, app_name="hello"):
    """Go girl."""
    socketfile = os.path.join(FCGI_SOCKET_DIR, 'kilink.socket' )

    try:
        srvr = WSGIServer(myapp, bindAddress=socketfile,
                          umask=FCGI_SOCKET_UMASK, multiplexed=True)
        srvr.run()
    finally:
        # clean up server socket file
        os.unlink(socketfile)

if __name__ == '__main__':
    main(sys.argv[1:])
