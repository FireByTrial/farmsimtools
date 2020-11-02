import collections
import os

from xmltodict import parse, unparse


def applyKeyName(obj: dict, key: str, callback: callable, parents: list = None) -> dict:
    if key in obj:
        if parents is not None:
            callback((obj, parents))
        else:
            callback(obj[key])
    new_parents = parents
    for sub, val in obj.items():
        if parents is not None:
            new_parents = parents.copy()
            new_parents.append(sub)
        if isinstance(val, dict):
            applyKeyName(val, key, callback, parents=new_parents)
        elif isinstance(val, list):
            for record in val:
                applyKeyName(record, key, callback, parents=new_parents)


def read(path: str, *args, **kwargs) -> dict:
    with open(path, "r") as fi:
        contents = fi.read()
    source_i3d = parse(contents, *args, **kwargs)
    return source_i3d


def write(i3d_contents: dict, path: str, *args, **kwargs) -> str:
    with open(path, "w") as fo:
        unparse(i3d_contents, output=fo, pretty=True, indent=' ', *args, **kwargs)


def get_for_type(type: str, i3d: dict) -> list:
    found = []
    applyKeyName(obj=i3d, key=type, callback=found.append)
    return found


def get_for_key(key: str, value: str, i3d: dict) -> list:
    found = []

    def check_key(tup: tuple):
        obj = tup[0]
        parents = tup[1]
        if isinstance(obj, dict) and key in obj and obj[key] == value:
            found.append((obj, parents))

    applyKeyName(obj=i3d, key=key, callback=check_key, parents=[])
    return found


def get_for_id():
    found = []

    def check_key(tup: tuple):
        obj = tup[0]
        parents = tup[1]
        if isinstance(obj, dict) and key in obj and obj[key] == value:
            found.append((obj, parents))

    applyKeyName(obj=i3d, key=key, callback=check_key, parents=[])
    return found


class TransformGroup:
    def __init__(self, i3d: dict = None, file: str = None):
        self._prefix = "@"
        self.file = file
        self.data = i3d
        self.default_label = 'TransformGroup'
        if not self.data and self.file:
            self.data = read(file)

    def prefix(self, term: str) -> str:
        return f"{self._prefix}{term}"

    @property
    def name(self) -> str:
        return str(self.prefix("name"))

    @property
    def id(self) -> str:
        return str(self.prefix('nodeId'))

    @property
    def rotation(self) -> str:
        return str(self.prefix('rotation'))

    @property
    def translation(self) -> str:
        return str(self.prefix('translation'))

    def new_transform_group(self, name: str, identifier: int, translation: str = None, rotation: str = None,
                            children: list = None, label: str = None):
        transform_group = collections.OrderedDict()
        transform_group[self.name] = str(name)
        transform_group[self.id] = str(identifier)
        identifier += 1
        if translation:
            transform_group[self.translation] = str(translation)
        if rotation:
            transform_group[self.rotation] = str(rotation)
        transform_group[label or self.default_label] = children
        return transform_group

    def get_transform_group(self, data, target) -> tuple:
        ttg = get_for_type(target, data)
        return ttg

    def get_by_name(self, name: str, i3d: dict = None):
        return get_for_key(key=self.name, value=name, i3d=i3d or self.data)


class Terrain(TransformGroup):
    target = 'TerrainTransformGroup'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_transform_group(self, data: dict = None):
        return super().get_transform_group(data=data or self.data, target=self.target)

    def get_dem_files(self):
        tg = self.get_transform_group()
        files = []
        for item in tg:
            height_map = item[self.prefix('heightMapId')]
            files.extend(get_for_key(self.prefix("fileId"), height_map, self.data))
        return files


if __name__ == "__main__":
    fn = r"D:\Games\MyMods\Sussex\maps\mapNB.i3d"
    tree_root = "baseTrees"
    contents = read(fn)
    terrain = Terrain(contents)
    terrain.get_transform_group(contents)
    root_trans = TransformGroup(contents)
    trees = root_trans.get_by_name(tree_root)
    print(trees)
    target_fn = os.path.join(os.path.dirname(fn), "generated_" + os.path.basename(fn))
    # write(i3d_contents=contents, path=target_fn)
