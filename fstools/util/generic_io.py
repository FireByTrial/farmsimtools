import os
import shutil

from fstools import _


def read(func, path, *args, **kwargs):
    assert os.path.exists(path), path + _("file not found")
    return func(path, *args, **kwargs)


def write(func: callable, path: str, overwrite: bool = False, *args, **kwargs):
    _exists = os.path.exists(path)
    _bak = path + ".bak"
    if _exists and not overwrite is True:
        raise AssertionError(f"`{path}`" + _(" exists but not permitted to overwrite"))
    if os.path.exists(_bak):
        os.remove(_bak)
    try:
        shutil.move(path, _bak)
        resp = func(path, *args, **kwargs)
    except Exception as exc:
        if _exists:
            shutil.copy2(_bak, path)
        raise
    finally:
        if _exists:
            os.remove(_bak)
    return resp
