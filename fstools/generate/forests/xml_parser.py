import collections

from fstools.util.i3d import TransformGroup


def cast_to_float(val: str):
    if isinstance(val, str):
        if val.replace('.', '', 1).isdigit():
            if '.' in val or 'e-' in val:
                return float(val)
            else:
                return int(val)
    return val


class XmlMetadata(TransformGroup):
    def __init__(self, data: dict = None):
        super().__init__(i3d=data)
        self.__Record = collections.namedtuple(
            "Record",
            self._field_names
        )

    def __getattr__(self, item):
        return ""

    @property
    def _record_data(self):
        return {k.lstrip(self._prefix): cast_to_float(v) for k, v in self._prefixed.items()}

    @property
    def _prefixed(self) -> dict:
        return {k: cast_to_float(v) for k, v in self.data.items() if self._prefix in k}

    @property
    def _field_names(self):
        return [x.lstrip(self._prefix) for x in self._prefixed.keys()]

    @property
    def record(self):
        return self.__Record(**self._record_data)

    @property
    def shape(self):
        return {}


class XmlForests(TransformGroup):
    def __init__(self, xml_data: dict = None, xml_file: str = None):
        super().__init__(xml_data, xml_file)
        self.default_label = "forest"

    def forests(self, target='forest'):
        forests = self.get_transform_group(data=self.data, target=target)
        assert len(forests) > 0, "no forest entries found in xml file, see example document"
        for forest in forests[0]:
            yield XmlMetadata(data=forest)

    def get_records(self):
        return self.forests()

    @property
    def shape(self):
        return {}
