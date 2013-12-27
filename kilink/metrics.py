# Copyright 2013 Facundo Batista
# All Rigths Reserved

"""Adapter to send metrics to statsd."""

from socket import socket, AF_INET, SOCK_DGRAM

# metric types
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
        record = "{}.{}:{}|{}".format(
            self.namespace, bucket.encode("utf8"), value, metric_type)
        udp_sock = socket(AF_INET, SOCK_DGRAM)
        udp_sock.sendto(record, self.addr)
