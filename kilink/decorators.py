"""Decorators to use in Flask."""

from datetime import timedelta
import time
from functools import update_wrapper

from flask import make_response, request, current_app, jsonify

from metrics import StatsdClient

metrics = StatsdClient("linkode")


def nocache(f):
    """Decorator to make a page un-cacheable."""
    def new_func(*args, **kwargs):
        """The new function."""
        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = 'public, max-age=0'
        return resp
    return update_wrapper(new_func, f)


def measure(metric_name):
    """Decorator generator to send metrics counting and with timing."""

    def _decorator(oldf):
        """The decorator itself."""

        def newf(*args, **kwargs):
            """The function to replace."""
            tini = time.time()
            try:
                result = oldf(*args, **kwargs)
            except Exception as exc:
                name = "%s.error.%s" % (metric_name, exc.__class__.__name__)
                metrics.count(name, 1)
                raise
            else:
                tdelta = time.time() - tini

                metrics.count(metric_name + '.ok', 1)
                metrics.timing(metric_name, tdelta)
                return result

        # need to fix the name because it's used by flask
        newf.func_name = oldf.func_name
        return newf
    return _decorator


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """Allow to be hit from other domain."""
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """Get methods."""
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        """The decorator."""
        def wrapped_function(*args, **kwargs):
            """The wrapped function."""
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def json_return(f):
    """Parse response to json and keep original"""
    def response(*args, **kwargs):
        """The wrapped function."""
        resp = f(*args, **kwargs)
        response = jsonify(**resp)
        response.original = resp
        return response
    return response
