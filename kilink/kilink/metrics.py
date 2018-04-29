# Copyright 2013 Facundo Batista
# All Rights Reserved

"""Adapter to send metrics to statsd."""
import time
from socket import socket, AF_INET, SOCK_DGRAM

MT_TIMING = "ms"
MT_COUNT = "c"
MT_GAUGE = "g"


class StatsdClient(object):
    """Send data to stats daemon over UDP, formatting accordingly."""

    def __init__(self, namespace, host='localhost', port=8125):
        self.namespace = namespace.encode("utf8")
        self.addr = host, port

    def timing(self, bucket, value):
        """Send timing stats."""
        self.send(bucket, value, MT_TIMING)

    def gauge(self, bucket, value):
        """Send gauge stats."""
        self.send(bucket, value, MT_GAUGE)

    def count(self, bucket, value):
        """Send counter stat."""
        self.send(bucket, value, MT_COUNT)

    def send(self, bucket, value, metric_type):
        """Send the record to stats daemon via UDP."""
        record = self._build_record(bucket, metric_type, value).encode("utf8")
        udp_sock = socket(AF_INET, SOCK_DGRAM)
        udp_sock.sendto(record, self.addr)

    def _build_record(self, bucket, metric_type, value):
        """Build the record"""
        record = "{}.{}:{}|{}".format(
            self.namespace, bucket.encode("utf8"), value, metric_type)
        return record


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

        # # need to fix the name because it's used by flask
        newf.__name__ = oldf.__name__
        return newf
    return _decorator
