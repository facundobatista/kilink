# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Backend functionality for Kilink."""

import os
import time
import zlib

import sqlobject


DB_FILENAME = os.path.abspath('data.db')

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _b62_encode(num):
    """Encode using a 62 letters alphabet."""
    arr = []
    base = len(ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)


def get_short_kid():
    """Build a short unique identifier."""
    return _b62_encode(int((time.time() * 1000000)))


class Kilink(sqlobject.SQLObject):
    """Kilink data."""
    kid = sqlobject.StringCol()
    revno = sqlobject.IntCol(default=1)
    parent_revno = sqlobject.IntCol(default=None)
    content = sqlobject.PickleCol()
    timestamp = sqlobject.DateTimeCol(default=sqlobject.DateTimeCol.now)


class KilinkBackend(object):
    """Backend for Kilink."""

    def __init__(self, db_connection=None):
        if db_connection is None:
            #if not os.path.exists(DB_FILENAME):
            #    Kilink.createTable()
            db_connection = 'sqlite:' + DB_FILENAME

        # connect
        connection = sqlobject.connectionForURI(db_connection)
        sqlobject.sqlhub.processConnection = connection

    def create_kilink(self, content, kid=None):
        """Create a new kilink with given content."""
        content = content.encode('utf8')
        zipped = zlib.compress(content)

        # create a kilink id if none is given
        if kid is None:
            kid = get_short_kid()
        else:
            # assure that the given kilink id is unique
            search = Kilink.selectBy(kid=kid)
            if search.count() > 0:
                raise ValueError("The given kilink id is already used: %r" %
                                 (kid,))

        try:
            Kilink(kid=kid, content=zipped)
        except sqlobject.dberrors.OperationalError,e:
            # TODO check that e is "no such table: kilink "
            Kilink.createTable()
            Kilink(kid=kid, content=zipped)
        return kid

    def update_kilink(self, kid, parent, new_content):
        """Add a new revision to a kilink."""
        # assure the parent is there
        search = Kilink.selectBy(kid=kid, revno=parent)
        if not search.count():
            raise ValueError("There's no such kilink for kid=%r revno=%s" % (
                             kid, parent))

        # calculate new revno; note that this is not thread safe
        highest_revno = Kilink.selectBy(kid=kid).max(Kilink.q.revno)
        new_revno = highest_revno + 1

        # create new revision
        new_content = new_content.encode('utf8')
        zipped = zlib.compress(new_content)
        Kilink(kid=kid, revno=new_revno, parent_revno=parent, content=zipped)
        return new_revno

    def get_content(self, kid, revno=1):
        """Get content for a specific kilink and version."""
        try:
            klnk = Kilink.selectBy(kid=kid, revno=revno).getOne()
        except sqlobject.main.SQLObjectNotFound:
            raise ValueError("Data not found for kilink=%r revno=%s" % (
                             kid, revno))
        expanded = zlib.decompress(klnk.content)
        expanded = expanded.decode('utf8')
        return expanded

    def get_kilink_tree(self, kid):
        """Return all the information about the kilink."""
        search = Kilink.selectBy(kid=kid)
        if not search.count():
            raise ValueError("Kilink id not found: %r" % (kid,))
        decomp = zlib.decompress
        data = [(k.revno, decomp(k.content), k.parent_revno, k.timestamp)
                for k in search]
        return data
