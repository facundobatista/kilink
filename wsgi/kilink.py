#!/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Kilink FTW!"""

import os
import sys

from flup.server.fcgi import WSGIServer

import server

FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111


def main(args_in, app_name="hello"):
    """Go girl."""
    socketfile = os.path.join(FCGI_SOCKET_DIR, 'kilink.socket' )

    try:
        srvr = WSGIServer(server.KilinkServer(), bindAddress=socketfile,
                          umask=FCGI_SOCKET_UMASK, multiplexed=True)
        srvr.run()
    finally:
        # clean up server socket file
        os.unlink(socketfile)

if __name__ == '__main__':
    main(sys.argv[1:])
