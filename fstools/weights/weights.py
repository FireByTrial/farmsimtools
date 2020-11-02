import os
import shutil

import imageio
import numpy

from fstools.i18n import _
from fstools.util import simple_rasters


def create_samples(path: str, layers: int = 4):
    image = simple_rasters.read(path)
    out_layers = []
    rand_array = numpy.random.randint(1, layers + 1, image.shape)
    for x in range(1, layers + 1, 1):
        mask = numpy.ma.equal(rand_array, x)
        masked = image * mask
        out_layers.append((masked, x))
    return out_layers


def generate_weights(output: str, input_file: str, overwrite: bool = True, layers: int = 4):
    samples = create_samples(input_file, layers=layers)
    for sample, index in samples:
        target = f"{output}0{str(index)}_weight.png"
        if os.path.exists(target):
            bak = target + ".bak"
            if os.path.exists(bak) and overwrite is True:
                os.remove(bak)
            shutil.move(target, bak)
        imageio.imwrite(target, sample)


def main(output: str, input_file: str = "blank.png", overwrite: bool = False, layers: int = 4):
    for i in range(1, layers, 1):
        weight_target = f"{output}0{str(i)}_weight.png"
        if not os.path.exists(weight_target) or overwrite is True:
            shutil.copyfile(input_file, weight_target)


if __name__ == "__main__":
    while True:
        try:
            target = input(_("output path (`C:\\exmaple\\animalMud`): ")) \
                     or r"D:\Games\MyMods\Sussex\maps\mapNB1\animalMud"
            source = input(_("sourceImage (blank for blank.png): ")) or "blank.png"
            generate_weights(target, source, overwrite=False, layers=4)
        except KeyboardInterrupt:
            print("Goodbye!")
            raise
