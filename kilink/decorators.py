"""Decorators to use in Flask."""
import time

from flask import jsonify


def json_return(f):
    """Parse response to json and keep original"""
    def wrapped_function(*args, **kwargs):
        """The wrapped function."""
        resp = f(*args, **kwargs)
        response = jsonify(**resp)
        response.original = resp
        return response
    return wrapped_function


def measure(metric_name, metric):
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
                metric.count(name, 1)
                raise
            else:
                tdelta = time.time() - tini

                metric.count(metric_name + '.ok', 1)
                metric.timing(metric_name, tdelta)
                return result

        # # need to fix the name because it's used by flask
        newf.__name__ = oldf.__name__
        return newf
    return _decorator