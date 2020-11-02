import os
from contextlib import contextmanager


def shape_components(shp: str):
    return {
        ext: os.path.splitext(shp)[0] + f".{ext}" for ext in ['shp', 'shx', 'dbf']
    }


@contextmanager
def shape_readers(shp, shx, dbf):
    with open(shp, "rb") as spi:
        with open(shx, "rb") as sxi:
            with open(dbf, "rb") as dbi:
                yield {'shp': spi, 'shx': sxi, 'dbf': dbi}
