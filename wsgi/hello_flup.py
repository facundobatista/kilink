#!/bin/env python
"""
Demo standalone Python FastCGI daemon using "flup" FastCGI->WSGI server
behind Nginx.

CentOS prerequisites -- from EPEL repository:
yum install python-flup nginx

1) Start this program and leave it running
2) Copy "nginx.conf" in this directory to /etc/nginx, then: /etc/init.d/nginx start
3) Try hitting any URL on http://localhost:88/

References:
http://trac.saddi.com/flup
http://pypi.python.org/pypi/flup/
http://wiki.codemongers.com/NginxModules
"""
from flup.server.fcgi import WSGIServer
import time, os, sys
import optparse

__usage__ = "%prog -n <num>"
__version__ = "$Id$"
__author__ = "Matt Kangas <matt@daylife.com>"

#FCGI_LISTEN_ADDRESS = ('localhost', 9000)
FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

def myapp(environ, start_response):
    """Dummy response handler"""
    # SLEEP 100 ms to force a demostration of parallel threading performance
    time.sleep(0.1)
    start_response('200 OK', [('Content-Type', 'text/plain')])
    pretty_env = '\n'.join(['%s: %s' % (repr(k),repr(v)) for (k,v) in environ.items()])
    msg = '''\
Hallo Welt!
Die zeit ist: %s
PID %s\n
%s\n''' % (time.ctime(), os.getpid(), pretty_env)
    return [msg]

def get_application():
    return myapp

def get_socketpath(name, server_number):
    #return os.path.join(FCGI_SOCKET_DIR, 'fcgi-%s-%s.socket' % (name, server_number))
    return os.path.join(FCGI_SOCKET_DIR, 'kilink.socket' )

def main(args_in, app_name="hello"):
    p = optparse.OptionParser(description=__doc__, version=__version__)
    p.set_usage(__usage__)
    p.add_option("-v", action="store_true", dest="verbose", help="verbose logging")
    p.add_option("-n", type="int", dest="server_num", help="Server instance number")
    opt, args = p.parse_args(args_in)

    if not opt.server_num:
        print "ERROR: server number not specified"
        p.print_help()
        return

    socketfile = get_socketpath(app_name, opt.server_num)
    app = get_application()

    try:
        WSGIServer(app,
               bindAddress = socketfile,
               umask = FCGI_SOCKET_UMASK,
               multiplexed = True,
               ).run()
    finally:
        # Clean up server socket file
        os.unlink(socketfile)

if __name__ == '__main__':
    main(sys.argv[1:])
