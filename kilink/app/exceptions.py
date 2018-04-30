class KilinkNotFoundError(Exception):
    """A kilink was specified, we couldn't find it."""


class KilinkDataTooBigError(Exception):
    """Content data too big."""