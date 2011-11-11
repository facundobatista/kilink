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
<style type="text/css">
textarea#id_content{
color:#666;
font-size:14px;
-moz-border-radius: 8px; -webkit-border-radius: 8px;
margin:5px 0px 10px 0px;
padding:10px;
border:#999 1px solid;
font-family:"Lucida Sans Unicode", "Lucida Grande", sans-serif;
transition: all 0.25s ease-in-out;
-webkit-transition: all 0.25s ease-in-out;
-moz-transition: all 0.25s ease-in-out;
box-shadow: 0 0 5px rgba(81, 203, 238, 0);
-webkit-box-shadow: 0 0 5px rgba(81, 203, 238, 0);
-moz-box-shadow: 0 0 5px rgba(81, 203, 238, 0);
}


textarea#id_content:focus{
color:#000;
outline:none;
border:#35a5e5 1px solid;
font-family:"Lucida Sans Unicode", "Lucida Grande", sans-serif;
box-shadow: 0 0 5px rgba(81, 203, 238, 1);
-webkit-box-shadow: 0 0 5px rgba(81, 203, 238, 1);
-moz-box-shadow: 0 0 5px rgba(81, 203, 238, 1);
}
</style>
</head>
<body>

<h1 id="title">Kilink</h1>

<form action="/action/create" method="POST" id="pasteform" name="pasteform">
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
    path_info = environ['PATH_INFO']
    query_string = environ['QUERY_STRING']

    # assure the user is there
    try:
        backend.get_user_kilinks(1)
    except backend.UserError:
        backend.create_user('name', 'mail')

    if path_info == '/':
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [MAIN_PAGE]

    if path_info == '/action/create':
        response = str(environ)
        post_data = environ['wsgi.input'].read()
        assert post_data[:8] == 'content='
        content = post_data[8:]
        kid = backend.create_kilink(1, content)
        start_response('303 see other', [('Location', "/" + kid)])
        return ''

    # serving a kilink
    start_response('200 OK', [('Content-Type', 'text/plain')])
    kid = path_info[1:]
    response = backend.get_content(kid, 1)
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
