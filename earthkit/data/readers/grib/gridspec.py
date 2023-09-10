# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.gridspec import GridSpec
from earthkit.data.core.metadata import RawMetadata


def make_gridspec(metadata):
    maker = GridSpecMaker(metadata)
    return GridSpec(maker.make())


class GridSpecMaker(RawMetadata):
    POSITIVE_SCAN_DIR = 1
    NEGATIVE_SCAN_DIR = -1
    CONF = None
    GRID_TYPES = None

    def __init__(self, metadata):
        self._load()

        # remap metadata keys and extract values
        d = {}
        for k, v in self.CONF["grib_mapping"].items():
            act_val = d.get(v, None)
            if act_val is None:
                d[v] = metadata.get(k, None)

        # determine grid type
        grid_type = d["grid_type"]
        self.grid_type = self.GRID_TYPES.get(grid_type, None)
        if self.grid_type is None:
            raise ValueError(f"Unsupported grib grid type={grid_type}")
        self.grid_conf = dict(self.CONF["types"][self.grid_type])
        d["type"] = self.grid_type

        self.getters = {
            "N": self.N,
            "area": self.area,
        }

        super().__init__(d)

    @staticmethod
    def _load():
        if GridSpecMaker.CONF is None:
            import yaml

            from earthkit.data.paths import earthkit_conf_file

            with open(earthkit_conf_file("data", "gridspec.yaml"), "r") as f:
                GridSpecMaker.CONF = yaml.safe_load(f)

            GridSpecMaker.GRID_TYPES = {}
            for k, v in GridSpecMaker.CONF["types"].items():
                for g in v["grid_types"]:
                    GridSpecMaker.GRID_TYPES[g] = k

    def make(self):
        d = {}

        for v in self.CONF["shared_keys"] + self.grid_conf["keys"]:
            self._add_key_to_spec(v, d)

        if "rotated" not in self["grid_type"]:
            for k in self.CONF["rotation_keys"]:
                d.pop(k, None)

        return d

    def _add_key_to_spec(self, item, d):
        if isinstance(item, str):
            key = item
            method = self.getters.get(key, self.get)
            d[key] = method(key)
        elif isinstance(item, dict):
            for k, v in item.items():
                method = self.getters.get(k, self.get_list)
                r = method(v)
                d[k] = r[0] if len(r) == 1 else r
        else:
            raise TypeError(f"Unsupported item type={type(item)}")

    def get_list(self, item):
        r = []
        for k in item:
            method = self.getters.get(k, None)
            if method is not None:
                v = method()
            else:
                v = self.get(k)
            r.append(v)
        return r

    def area(self, item):
        a = {}
        a["north"] = max(self["first_lat"], self["last_lat"])
        a["south"] = min(self["first_lat"], self["last_lat"])
        a["west"] = self.west()
        a["east"] = self.east()
        return [a[k] for k in item]

    def west(self):
        if self.x_scan_dir() == self.POSITIVE_SCAN_DIR:
            return self["first_lon"]
        else:
            return self["last_lon"]

    def east(self):
        if self.x_scan_dir() == self.POSITIVE_SCAN_DIR:
            return self["last_lon"]
        else:
            return self["first_lon"]

    def x_scan_dir(self):
        v = self.get("i_scans_negatively", None)
        if v is not None:
            return self.POSITIVE_SCAN_DIR if v == 0 else self.NEGATIVE_SCAN_DIR
        else:
            raise ValueError("Could not determine i-direction scanning mode")

    def N(self):
        label = ""
        if self["type"] == "regular_gg":
            label = "F"
        elif self["type"] == "reduced_gg":
            octahedral = self.get("octahedral", 0) == 1
            label = "O" if octahedral else "N"
        else:
            raise Exception("Cannot define N for type=" + self["type"])
        return label + str(self["N"])
