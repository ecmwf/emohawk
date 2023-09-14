# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.metadata import RawMetadata


def make_levelspec(metadata):
    maker = LevelSpecMaker(metadata)
    return maker.make()


class LevelSpecConf:
    _CONFIG = None
    _LEVEL_TYPES = None

    @staticmethod
    def config():
        LevelSpecConf._load()
        return LevelSpecConf._CONFIG

    @staticmethod
    def level_types():
        LevelSpecConf._load()
        return LevelSpecConf._LEVEL_TYPES

    @staticmethod
    def _load():
        if LevelSpecConf._CONFIG is None:
            import yaml

            # from earthkit.data.paths import earthkit_conf_file

            path = "/Users/cgr/git/earthkit-data/_dev/level/level_spec.yaml"
            # with open(earthkit_conf_file("data", "level_spec.yaml"), "r") as f:
            with open(path, "r") as f:
                LevelSpecConf._CONFIG = yaml.safe_load(f)

            # add gridspec key to grib key mapping to conf
            d = {}
            for k, v in LevelSpecConf._CONFIG["grib_key_map"].items():
                if v in d:
                    k_act = d[v]
                    if isinstance(k_act, tuple):
                        k = tuple([*k_act, k])
                    else:
                        k = tuple([k_act, k])
                d[v] = k
            LevelSpecConf._CONFIG["to_grib_map"] = d

            # assign conf to GRIB typeOfLevel
            LevelSpecConf._LEVEL_TYPES = {}
            for k, v in LevelSpecConf._CONFIG["types"].items():
                g = v["type"]
                if isinstance(g, str):
                    LevelSpecConf._LEVEL_TYPES[g] = k
                elif isinstance(g, list):
                    for x in g:
                        LevelSpecConf._LEVEL_TYPES[x] = k

    @staticmethod
    def remap_ls_keys_to_grib(gs):
        gs_to_grib = LevelSpecConf._CONFIG["to_grib_map"]
        r = {}
        for k, v in gs.items():
            grib_key = gs_to_grib[k]
            if isinstance(grib_key, tuple):
                for x in grib_key:
                    r[x] = v
            else:
                r[grib_key] = v
        return r


class LevelSpecMaker(RawMetadata):
    POSITIVE_SCAN_DIR = 1
    NEGATIVE_SCAN_DIR = -1

    def __init__(self, metadata):
        self.conf = LevelSpecConf.config()

        # remap metadata keys and get values
        d = {}
        for k, v in self.conf["grib_key_map"].items():
            act_val = d.get(v, None)
            if act_val is None:
                d[v] = metadata.get(k, None)

        # determine grid type
        level_type = d["level_type"]
        self.level_type = LevelSpecConf.level_types().get(level_type, None)
        if self.level_type is None:
            raise ValueError(f"Unsupported grib level type={level_type}")
        self.level_conf = dict(self.conf["types"][self.level_type])
        d["type"] = self.level_type

        self.getters = {}

        super().__init__(d)

    def make(self):
        d = {}

        for v in self.level_conf["spec"]:
            self._add_key_to_spec(v, d)

        self.scale(d)
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

    def scale(self, d):
        s = self.level_conf.get("scale", None)
        if s is not None:
            for k, v in s.items():
                if k in d:
                    level_type = v[0]
                    factor = v[1]
                if self["level_type"] == level_type:
                    d[k] *= factor


class LevelSpecConverter:
    LS_LEVEL_TYPE = None

    def __init__(self, ls, ls_type, edition):
        self.ls = ls
        self.ls_type = ls_type
        self.conf = LevelSpecConf.config()["types"][ls_type]
        self.edition = edition
        # self.grid_size = 0
        # TODO: add gridspec validation

    def run(self):
        d = self.add_level_type()
        for k in self.conf["grib"]:
            if k not in d:
                d[k] = self.get(k)
        self.descale(d)
        d = LevelSpecConf.remap_ls_keys_to_grib(d)

        return d

    @staticmethod
    def to_metadata(ls, edition=2):
        ls_type = ls["type"]
        maker = lsspec_converters.get(ls_type, LevelSpecConverter)
        converter = maker(ls, ls_type, edition)
        return converter.run()

    def add_level_type(self):
        d = {}
        d["level_type"] = self.conf["type"]
        return d

    def get(self, key, default=None, transform=None):
        v = self.ls.get(key, default)
        if v is not None and callable(transform):
            return transform(v)
        return v

    def descale(self, d):
        s = self.conf.get("scale", None)
        if s is not None:
            for k, v in s.items():
                if k in d:
                    level_type = v[0]
                    factor = v[1]
                if d["level_type"] == level_type:
                    d[k] = int(d[k] / factor)


class PressureLevelSpecConverter(LevelSpecConverter):
    LS_LEVEL_TYPE = "pl"

    def add_level_type(self):
        d = {}
        level = self.ls.get("level")
        if level < 1:
            d["level_type"] = "isobaricInPa"
        else:
            d["level_type"] = "isobaricInhPa"
        return d


lsspec_converters = {}
for x in [PressureLevelSpecConverter]:
    lsspec_converters[x.LS_LEVEL_TYPE] = x
