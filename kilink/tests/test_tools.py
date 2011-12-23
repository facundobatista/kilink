# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some kilink tests."""

from unittest import TestCase

from kilink.tools import magic_quote


class MagicQuoteTestCase(TestCase):
    """Tests for the magic_quote function."""

    def test_unencoded(self):
        """Unencoded stuff."""
        inp = "some content"
        out = magic_quote(inp)
        self.assertEqual(inp, out)

    def test_plus(self):
        """Specially encoded +."""
        res = magic_quote("+") # space
        self.assertEqual(res, " ")

    def test_singlechar(self):
        """One encoded char."""
        res = magic_quote("%3E") # <
        self.assertEqual(res, "&#62;")

    def test_doublechar(self):
        """Two chars, because of UTF8."""
        res = magic_quote("%C3%B1") # ñ
        self.assertEqual(res, "&#241;")

    def test_triplechar(self):
        """Three chars, because of UTF8."""
        res = magic_quote("%EC%8F%94") # 쏔
        self.assertEqual(res, "&#50132;")

    def test_mixed(self):
        """All mixed up."""
        # <a b c> cañón +쏔
        res = magic_quote('%3Ca+b+c%3E+ca%C3%B1%C3%B3n+%2B%EC%8F%94')
        self.assertEqual(res, "&#60;a b c&#62; ca&#241;&#243;n &#43;&#50132;")
