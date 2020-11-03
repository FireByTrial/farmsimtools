import os
from pathlib import Path

from fstools.generate.forests.forestGenerator import ForestGenerator
from fstools.util import i3d

if __name__ == "__main__":
    # change this if you named your base treeset something other than baseTrees (case counts)
    i3d_tree_sources = "baseTrees"

    # path to your i3d file (make sure to backup your project first!)
    i3d_file = Path(r"D:\MyMods\MyModMap\maps\mapNB.i3d")

    # Note: you can use a combination of both tif/png and xml/shp, you just have to have one of each

    ###### if working with geospatial data ######
    shp = Path(r"C:\MyMods\MyModMap\reference\geospatial\forestry.shp")
    rasterized = Path(r"C:\MyMods\MyModMap\reference\geospatial\forestryRaster.tif")
    # if your not using shp, you can set that to None and add a Path to a xml instead here
    xml_fn = None
    # comment everything out with `#` in the PNG/XML section,

    ###### if working with PNG and xml (GE) ######
    # leave the shp as None
    shp = None
    rasterized = Path(r"C:\MyMods\MyModMap\maps\mapDE\forests.png")
    xml_fn = Path(r"C:\MyMods\MyModMap\maps\xml\forests.xml")

    # don't change things below here
    print("loading...")
    fg = ForestGenerator(i3d_file, i3d_tree_sources, rasterized, shp, xml_raster_metadata=xml_fn)
    print("running generation")
    fg.run()
    target_fn = os.path.join(os.path.dirname(i3d_file), os.path.basename(i3d_file))
    i3d.write(i3d_contents=fg.i3d_data.data, path=target_fn)
    print(f"Done! wrote to {target_fn}")
