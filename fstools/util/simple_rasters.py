import imageio
import numpy

from fstools.util import generic_io


def read(path: str) -> numpy.ndarray:
    return generic_io.read(imageio.read, path)


def write(array: numpy.ndarray, path: str, overwrite: bool = False) -> None:
    def _write(_path, _array):
        return imageio.imwrite(_array, _path)

    return generic_io.write(_write, overwrite=overwrite, path=path, _array=array)

def read_img(path: str):
    return generic_io.read(imageio.imread, path)