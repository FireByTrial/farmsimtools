import collections
import json
import math
import os
import random
from contextlib import suppress
from pathlib import Path

import numpy
import shapefile

from fstools.generate.forests.xml_parser import XmlForests
from fstools.i18n import _
from fstools.util import i3d
from fstools.util import simple_rasters
from fstools.util.i3d import TransformGroup, get_for_key
from fstools.util.shapeutil import shape_components, shape_readers


class ForestGenerator:
    def __init__(self, i3d_fn: str, tree_source: str, raster_source: Path, shape: str = None, xml_raster_metadata: str = None):
        """
        takes a i3d file and creates forests automatically based on a combination of either shp or xml data with a
        raster layer input to specify locations of the forests
        :param i3d_fn: path to an i3d file (not the data itself)
        :param tree_source: the source TransformGroup name to pull the trees from
        :param raster_source: a png or tiff that matches the DEM file in the i3d file
        :param shape: a shapefile that the raster_source that was exported from a GIS app with corresponding metadata
        :param xml_raster_metadata: a xml file that corresponds with the infoLayer png (raster_source)
        """
        super().__init__()
        self.i3d_data = i3d.TransformGroup(file=i3d_fn)
        self.terrain = i3d.Terrain(i3d=self.i3d_data.data)
        self.tree_source = tree_source
        self.shp = shape
        self.xml_raster_metadata = xml_raster_metadata
        self.raster = simple_rasters.read_img(raster_source)
        self.global_density_factor = 0.3  # 0.6 is good for a realistic 'feel' but it's not great for gameplay
        self.dem_files = self.terrain.get_dem_files()
        assert self.dem_files, _("DEM not found in i3d")
        self.__shp_records = None
        self.__shp_fields = None
        self.__dem = None

    def _load_dem(self):
        dem_ref = self.dem_files[0][0][self.terrain.prefix('filename')]
        dem_path = os.path.join(os.path.dirname(self.i3d_data.file), dem_ref)
        self.__dem = simple_rasters.read_img(dem_path)

    @property
    def dem(self):
        if self.__dem is None:
            self._load_dem()
        return self.__dem

    @property
    def trees(self):
        return self.i3d_data.get_by_name(self.tree_source).copy()

    def read_records(self, path: str = None):
        if (path and "xml" in path) or self.xml_raster_metadata:
            return list(self.read_xml(path))
        elif (path and "shp" in path) or self.shp:
            return self.read_shp(path)
        else:
            raise AssertionError("a shp or xml file must be provided")

    def read_xml(self, path: str = None):
        return XmlForests(xml_file=path or self.xml_raster_metadata).get_records()

    def read_shp(self, path: str = None):
        with shape_readers(**shape_components(path or self.shp)) as readers:
            reader = shapefile.Reader(**readers)
            self.__shp_records = [x for x in reader.iterShapeRecords()]
            self.__shp_fields = reader.fields.copy()
        return self.__shp_records

    def run(self, shp_key: str = "id", target_ids: list = None):
        records = self.read_records()
        target_records = target_ids or []
        if not target_records:
            target_records.extend([getattr(x.record, shp_key) for x in records])
        forests = []
        forest_number = 0
        ident = 100000
        transform = TransformGroup()
        tree_species = self.trees[0][0][transform.default_label]
        rand_array = numpy.random.randint(0, len(tree_species)-1, self.raster.shape)
        for record in records:
            if record.record.id not in target_records:
                continue
            forest_number += 1
            density_multiplier = (record.record.densMult or 1.0) * self.global_density_factor
            forest = self.generate(record, forest_number=forest_number, id_start=ident, rand_array=rand_array)
            smaller_forest = self.thin_forest(forest, percent_to_keep=random.randint(45, 75) * density_multiplier)
            forests.append(smaller_forest)
        print(sum([len(x) for x in forests]))
        autoForests = self.i3d_data.get_by_name('autoForests')
        autoForests[0][0]['TransformGroup'] = forests

    def generateMask(self, record: shapefile.ShapeRecord, rand_array: numpy.ndarray, species: list = [],
                     weighting: list = []):
        transform = TransformGroup()
        mask = numpy.ma.equal(self.raster, record.record.id)
        aoi = rand_array * mask
        masked = aoi * self.prune_neighbors(aoi)
        log_choice = numpy.flip(numpy.logspace(0, 1, len(species), base=10))
        _weighting = list(weighting.values()) if isinstance(weighting, dict) else weighting
        if _weighting:
            probabilities = _weighting
        else:
            probabilities = log_choice / log_choice.sum()
        print(_("Probabilities:"))
        for i in range(len(probabilities)):
            print(f"{species[i][transform.name]}: {round(probabilities[i] * 100, 2)}%")
        tree_species = numpy.random.choice(list(range(0, len(species))), mask.count(), p=probabilities)

        y_loc = 0
        locations = []
        print(_("masking grid..."))
        i = 0
        for (x, y), val in numpy.ndenumerate(masked):
            if val > 0:
                locations.append({'x': x, 'y': y, 'z': species[tree_species[i]]})
                i += 1
        return locations

    def generate(self, record: shapefile.ShapeRecord, rand_array: numpy.ndarray, forest_number: int = 1,
                 id_start: int = 1000000, gitter=1.25, z_offset=-0.05):  # , tree_types:list =[]):
        print(_("processing forest #" + str(forest_number)))
        transform = TransformGroup()
        terrain_pixel_scale = float(self.terrain.get_transform_group()[0][transform.prefix('unitsPerPixel')])
        prefix = 'base'
        forest = transform.new_transform_group(name=f"forest{forest_number}", identifier=id_start, children=[])
        id_start += 1
        trees = self.trees[0][0][transform.default_label]
        tree_names = list(map(lambda x: x[transform.name].lstrip(prefix), trees))
        tree_weights = list(map("wgt{}".format, tree_names))
        weights = [0.37, 0.53, 0.07, 0.03]
        shp_weights = {}
        for tree_weight in tree_weights:
            try:
                _weight = getattr(record.record, tree_weight)
            except AttributeError as exc:
                print(_("missing tree weights for shp with name:") + tree_weight)
            else:
                if _weight is not None:
                    shp_weights[tree_weight] = _weight
        if shp_weights:
            if sum(shp_weights.values()) == 1:
                weights = shp_weights
            else:
                print(_("weights do not sum to 1.0 for {}").format(record.record.id))
        tree_count = {}
        for loc in self.generateMask(record=record, rand_array=rand_array, species=trees, weighting=weights):
            clone_tree = loc['z'].copy()
            tree_tg = clone_tree[transform.default_label]
            no_prefix = clone_tree[transform.name].lstrip(prefix).lower()
            tree_count.setdefault(no_prefix, {})
            try:
                available_ages = [int(x[transform.name].lstrip(f"{no_prefix}_stage")) for x in tree_tg]
            except TypeError as exc:
                clone_tree_list = [[tree_tg]]  # a single tree in the group causes this (maple)
                rand_choice = tree_tg[transform.name].lstrip(f"{no_prefix}_stage")
            else:
                available_ages = [x for x in available_ages if record.record.minSize <= x <= record.record.maxSize]
                if not available_ages:
                    print(_("found invalid min/max size for record (or no tree of permitted ages)#") + str(
                        record.record.id))
                    continue
                rand_choice = random.choice(available_ages)
                target_name = f"{no_prefix}_stage{rand_choice}"
                clone_tree_list = get_for_key(transform.name, target_name, dict(root=tree_tg))
            tree_count[no_prefix].setdefault(str(rand_choice), 0)
            tree_count[no_prefix][str(rand_choice)] += 1
            x_gitter = abs(random.random()) % (gitter - gitter * 2)
            y_gitter = abs(random.random()) % (gitter - gitter * 2)
            dem_values = []
            for _x in range(loc['x']-1, loc['x']+2):
                for _y in range(loc['y']-1, loc['y']+2):
                    dem_values.append(self.dem[_x, _y])
            dem_height = sum(sorted(dem_values[:2]))/2
            z_val = dem_height / (pow(2, 16) / pow(2, 8)) + z_offset
            loc_str = "{x} {z} {y}".format(
                **{
                    "x": ((float(loc['y']) - self.raster.shape[0] / 2) * terrain_pixel_scale) + x_gitter,
                    "y": ((float(loc['x']) - self.raster.shape[1] / 2) * terrain_pixel_scale) + y_gitter,
                    'z': z_val
                }
            )
            if clone_tree_list:
                tree = clone_tree_list[0][0].copy()
                tree[transform.translation] = loc_str
                rotate = map(str, [0, round(abs(random.random() % 360), 2) - 180, 0])
                tree[transform.rotation] = "{} {} {}".format(*rotate)
                tree[transform.id] = str(id_start)
                id_start += 1
                forest[transform.default_label].append(tree)
        print(_("forest #{} has {} trees").format(forest_number, len(forest[transform.default_label])))
        print(json.dumps(tree_count, indent=2, sort_keys=True))
        return forest

    def prune_neighbors(self, arr: numpy.ndarray, distance=2):
        comp_arr = numpy.full(arr.shape, True, dtype=int)
        print(_("pruning values..."))
        for (x, y), item in numpy.ndenumerate(arr):
            summed = 0
            if item > 0:
                for xd in range(x-distance, x+distance+1):
                    if summed > 1:
                        continue
                    for yd in range(y-distance, y+distance+1):
                        with suppress(IndexError):
                            summed += (1 if arr[xd][yd] > 0 else 0)
            comp_arr[x][y] = int(summed)
        mask = numpy.ma.greater(comp_arr, 1)
        print(_("pruned {}").format(mask.count()))
        return arr * mask

    def thin_forest(self, forest: collections.OrderedDict, percent_to_keep=75):
        transform = TransformGroup()

        chunks = [
            forest[transform.default_label][i:i + 100] for i in range(0, len(forest[transform.default_label]), 100)
        ]
        thinned_forest = []
        for chunk in chunks:
            to_keep = random.sample(chunk, int(max(1, math.floor(len(chunk) * (percent_to_keep / 100)))))
            thinned_forest.extend(to_keep)
        forest[transform.default_label] = thinned_forest
        return forest


if __name__ == "__main__":
    i3d_file = Path(r"D:\Games\MyMods\Sussex\maps\mapNB.i3d")
    i3d_tree_sources = "baseTrees"
    #shp = Path(r"D:\Games\MyMods\Sussex\reference\geospatial\forestry.shp")
    shp = None
    #rasterized = Path(r"D:\Games\MyMods\Sussex\reference\geospatial\forestryRaster.tif")
    rasterized = Path(r"D:\Games\MyMods\Sussex\maps\mapNB1\forests.png")
    xml_fn = Path(r"D:\Games\MyMods\Sussex\xml\forests.xml")
    fg = ForestGenerator(i3d_file, i3d_tree_sources, rasterized, shp, xml_raster_metadata=xml_fn)
    fg.run()
    # target_fn = os.path.join(os.path.dirname(i3d_file), "forest_" + os.path.basename(i3d_file))
    target_fn = os.path.join(os.path.dirname(i3d_file), os.path.basename(i3d_file))
    i3d.write(i3d_contents=fg.i3d_data.data, path=target_fn)
    print(f"Done! wrote to {target_fn}")
