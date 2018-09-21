"""Decorators to use in Flask."""

import time
from metrics import StatsdClient

# metrics
metrics = StatsdClient("linkode")


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
