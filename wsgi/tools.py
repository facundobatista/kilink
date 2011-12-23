#!/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tools for Kilink."""


def magic_quote(text):
    """Convert wsgi encoding to the one that we can deliver to the entry."""
    response = []
    text = iter(text)
    while True:
        try:
            char = text.next()
        except StopIteration:
            break

        if char == '+':
            response.append(' ')
            continue

        if char != '%':
            response.append(char)
            continue

        head = int(text.next() + text.next(), 16)
        if head <= 127:
            response.append("&#%d;" % head)
            continue

        if 192 <= head <= 223:
            assert text.next() == '%'
            c2 = int(text.next() + text.next(), 16)
            u = chr(head) + chr(c2)
            response.append("&#%d;" % ord(u.decode("utf8")))
            continue

        if 224 <= head <= 239:
            assert text.next() == '%'
            c2 = int(text.next() + text.next(), 16)
            assert text.next() == '%'
            c3 = int(text.next() + text.next(), 16)
            u = chr(head) + chr(c2) + chr(c3)
            response.append("&#%d;" % ord(u.decode("utf8")))
            continue

        if 240 <= head <= 247:
            assert text.next() == '%'
            c2 = int(text.next() + text.next(), 16)
            assert text.next() == '%'
            c3 = int(text.next() + text.next(), 16)
            assert text.next() == '%'
            c4 = int(text.next() + text.next(), 16)
            u = chr(head) + chr(c2) + chr(c3) + chr(c4)
            response.append("&#%d;" % ord(u.decode("utf8")))
            continue

        raise ValueError("Not recognized text format: %r" % ("".join(text),))
    return "".join(response)
