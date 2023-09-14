# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta, abstractmethod

from earthkit.data.core.gridspec import GridSpec
from earthkit.data.core.metadata import RawMetadata

FULL_GLOBE = 360.0
FULL_GLOBE_EPS = 1e-7


def make_gridspec(metadata):
    maker = GridSpecMaker(metadata)
    return GridSpec(maker.make())


class GridSpecConf:
    _CONFIG = None
    _GRID_TYPES = None

    @staticmethod
    def config():
        GridSpecConf._load()
        return GridSpecConf._CONFIG

    @staticmethod
    def grid_types():
        GridSpecConf._load()
        return GridSpecConf._GRID_TYPES

    @staticmethod
    def _load():
        if GridSpecConf._CONFIG is None:
            import yaml

            from earthkit.data.paths import earthkit_conf_file

            with open(earthkit_conf_file("data", "gridspec.yaml"), "r") as f:
                GridSpecConf._CONFIG = yaml.safe_load(f)

            # add gridspec key to grib key mapping to conf
            d = {}
            for k, v in GridSpecConf._CONFIG["grib_key_map"].items():
                if v in d:
                    k_act = d[v]
                    if isinstance(k_act, tuple):
                        k = tuple([*k_act, k])
                    else:
                        k = tuple([k_act, k])
                d[v] = k
            GridSpecConf._CONFIG["conf_key_map"] = d

            # assign conf to GRIB gridType
            GridSpecConf._GRID_TYPES = {}
            for k, v in GridSpecConf._CONFIG["types"].items():
                g = v["grid_type"]
                GridSpecConf._GRID_TYPES[g] = k
                g = v.get("rotated_type", None)
                if g is not None:
                    GridSpecConf._GRID_TYPES[g] = k

    @staticmethod
    def remap_gs_keys_to_grib(gs):
        gs_to_grib = GridSpecConf._CONFIG["conf_key_map"]
        r = {}
        for k, v in gs.items():
            grib_key = gs_to_grib[k]
            if isinstance(grib_key, tuple):
                for x in grib_key:
                    r[x] = v
            else:
                r[grib_key] = v
        return r


class GridSpecMaker(RawMetadata):
    POSITIVE_SCAN_DIR = 1
    NEGATIVE_SCAN_DIR = -1

    def __init__(self, metadata):
        self.conf = GridSpecConf.config()

        # remap metadata keys and get values
        d = {}
        for k, v in self.conf["grib_key_map"].items():
            act_val = d.get(v, None)
            if act_val is None:
                d[v] = metadata.get(k, None)

        # determine grid type
        grid_type = d["grid_type"]
        self.grid_type = GridSpecConf.grid_types().get(grid_type, None)
        if self.grid_type is None:
            raise ValueError(f"Unsupported grib grid type={grid_type}")
        self.grid_conf = dict(self.conf["types"][self.grid_type])
        d["type"] = self.grid_type

        self.getters = {
            "N": self.N,
            "area": self.area,
        }

        super().__init__(d)

    def make(self):
        d = {}

        for v in self.grid_conf["spec"]:
            self._add_key_to_spec(v, d)

        if "rotated" not in self["grid_type"]:
            for k in self.conf["rotation_keys"]:
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
        elif isinstance(item, list):
            for v in item:
                self._add_key_to_spec(v, d)
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
        label = self.grid_conf["N_label"]
        if isinstance(label, dict):
            if "octahedral" not in label:
                raise ValueError(f"octahedral missing from N label description={label}")
            octahedral = 1 if self.get("octahedral", 0) == 1 else 0
            label = label["octahedral"][octahedral]
        elif not isinstance(label, str):
            raise ValueError(f"Invalid N label description={label}")
        return label + str(self["N"])


class GridSpecConverter(metaclass=ABCMeta):
    GS_GRID_TYPE = None

    def __init__(self, gs, gs_type, edition):
        self.gs = gs
        self.gs_type = gs_type
        self.conf = GridSpecConf.config()["types"][gs_type]
        self.edition = edition
        self.grid_size = 0
        # TODO: add gridspec validation

    def run(self):
        # the order might matter
        d = self.add_grid_type()
        d.update(self.add_grid())
        d.update(self.add_rotation())
        d.update(self.add_scanning())
        d = GridSpecConf.remap_gs_keys_to_grib(d)
        return d

    @staticmethod
    def to_metadata(gs, edition=2):
        gs_type = GridSpecConverter.infer_gs_type(gs)

        # create converter and generate metadata
        maker = gridspec_converters.get(gs_type, None)
        if maker is None:
            raise ValueError(f"Unsupported gridspec type={gs_type}")
        else:
            converter = maker(gs, gs_type, edition)
            return converter.run(), converter.grid_size

    @staticmethod
    def infer_gs_type(gs):
        gs_type = gs.get("type", None)
        # when no type specified the grid must be regular_ll or gaussian
        if gs_type is None:
            grid = gs["grid"]
            # regular_ll: the grid is in the form of [dx, dy]
            if isinstance(grid, list) and len(grid) == 2:
                gs_type = "regular_ll"
            # gaussian: the grid=N as a str or int
            elif isinstance(grid, (str, int)):
                gs_type = GridSpecConverter.infer_gaussian_type(grid)

        if gs_type is None:
            raise ValueError("Could not determine type of gridspec={gs}")

        return gs_type

    @staticmethod
    def infer_gaussian_type(v):
        """Determine gridspec type for Gaussian grids"""
        grid_type = ""
        if isinstance(v, str):
            try:
                if v[0] == "F":
                    grid_type = "regular_gg"
                elif v[0] in ["N", "O"]:
                    grid_type = "reduced_gg"
                else:
                    grid_type = "regular_gg"
                    _ = int(v)
            except Exception:
                raise ValueError(f"Invalid Gaussian grid description str={v}")
        elif isinstance(v, int):
            grid_type = "regular_gg"
        else:
            raise ValueError(f"Invalid Gaussian grid description={v}")

        return grid_type

    def add_grid_type(self):
        d = {}
        d["grid_type"] = self.conf["grid_type"]

        rotation = self.add_rotation()
        if rotation:
            rotated_type = self.conf.get("rotated_type", None)
            if rotated_type is None:
                raise ValueError(
                    f"Rotation is not supported for gridspec type={self.gs_type}"
                )
            d["grid_type"] = rotated_type
            d.update(rotation)

        return d

    @abstractmethod
    def add_grid(self):
        pass

    def add_rotation(self):
        d = {}
        rotation = self.gs.get("rotation", None)
        if rotation is not None:
            if not isinstance(rotation, list) or len(rotation) != 2:
                raise ValueError(f"Invalid rotation in grid spec={rotation}")
            d["lat_south_pole"] = rotation[0]
            d["lon_south_pole"] = rotation[1]
            d["angle_of_rotation"] = self.get("angle_of_rotation")
        return d

    def add_scanning(self):
        d = {}
        keys = {
            "j_points_consecutive": 0,
            "i_scans_negatively": 0,
            "j_scans_positively": 0,
        }
        for k, v in keys.items():
            d[k] = self.get(k, default=v, transform=self.to_zero_one)
        return d

    def _parse_scanning(self):
        d = self.add_scanning()
        return (d["i_scans_negatively"], d["j_scans_positively"])

    def to_zero_one(self, v):
        return 1 if (v == 1 or v is True) else 0

    def get(self, key, default=None, transform=None):
        v = self.gs.get(key, default)
        if v is not None and callable(transform):
            return transform(v)
        return v

    @staticmethod
    def normalise_lon(lon, minimum):
        while lon < minimum:
            lon += FULL_GLOBE
        while lon >= minimum + FULL_GLOBE:
            lon -= FULL_GLOBE
        return lon


class LatLonGridSpecConverter(GridSpecConverter):
    GS_GRID_TYPE = "regular_ll"

    def _parse_ew(self, dx, west, east):
        nx = self.gs.get("nx", None)
        west = self.normalise_lon(west, 0)
        east = self.normalise_lon(east, 0)
        global_ew = False
        if east < west:
            east += FULL_GLOBE
        if abs(east - west) < FULL_GLOBE_EPS:
            east = west + FULL_GLOBE
            global_ew = True
        elif abs(east - west - FULL_GLOBE) < FULL_GLOBE_EPS:
            global_ew = True
        assert west >= 0
        assert east > west

        if global_ew:
            east -= abs(dx)

        if nx is None:
            d_lon = east - west
            nx = int(d_lon / dx) + 1
            eps = dx / 3
            if abs(abs((nx - 1) * dx) - abs(d_lon)) > eps:
                if abs((nx - 1) * dx) > abs(d_lon):
                    nx -= 1
                else:
                    nx += 1

        west = self.normalise_lon(west, 0)
        east = self.normalise_lon(east, 0)
        if self.edition == 1:
            if west > east:
                west = self.normalise_lon(west, -180)

        return nx, west, east

    def _parse_ns(self, dy, north, south):
        ny = self.gs.get("ny", None)
        if ny is None:
            d_lat = abs(north - south)
            ny = int(d_lat / dy) + 1
            eps = dy / 3
            if abs(abs((ny - 1) * dy) - abs(d_lat)) > eps:
                if abs((ny - 1) * dy) > abs(d_lat):
                    ny -= 1
                else:
                    ny += 1
        return ny, north, south

    def add_grid(self):
        d = {}
        area = self.gs.get("area", None)
        if isinstance(area, list) and len(area) == 4:
            north, west, south, east = area
        else:
            raise ValueError(f"Invalid area={area}")

        dx, dy = self.gs.get("grid", [1, 1])
        nx, west, east = self._parse_ew(dx, west, east)
        ny, north, south = self._parse_ns(dy, north, south)

        # apply i and j scanning directions
        i_scan_neg, j_scan_pos = self._parse_scanning()
        if j_scan_pos == 1:
            north, south = south, north
        if i_scan_neg == 1:
            west, east = east, west

        d["nx"] = nx
        d["ny"] = ny
        d["dx"] = dx
        d["dy"] = dy
        d["first_lat"] = north
        d["last_lat"] = south
        d["first_lon"] = west
        d["last_lon"] = east

        self.grid_size = nx * ny

        return d


class RegularGaussianGridSpecConverter(GridSpecConverter):
    GS_GRID_TYPE = "regular_gg"

    def add_grid(self):
        N = self.gs.get("grid", None)
        if isinstance(N, str):
            try:
                if N[0] == "F":
                    N = int(N[:1])
                else:
                    N = int(N)
            except Exception:
                raise ValueError("Invalid N={N}")
        elif not isinstance(N, int):
            raise ValueError("Invalid N={N}")
        if N < 1 or N > 1000000:
            raise ValueError("Invalid N={N}")
        d = dict(N=N)
        return d


class ReducedGaussianGridSpecConverter(GridSpecConverter):
    GS_GRID_TYPE = "reduced_gg"

    def add_grid(self):
        N = self.gs.get("grid", None)
        octahedral = self.gs.get("octahedral", 0)
        if isinstance(N, str):
            try:
                if N[0] == "N":
                    N = int(N[:1])
                    octahedral = 0
                elif N[0] == "O":
                    N = int(N[:1])
                    octahedral = 1
                else:
                    N = int(N)
            except Exception:
                raise ValueError("Invalid N={N}")
        elif not isinstance(N, int):
            raise ValueError("Invalid N={N}")
        if N < 1 or N > 1000000:
            raise ValueError("Invalid N={N}")
        d = dict(N=N, octahedral=octahedral)
        return d


gridspec_converters = {}
for x in [LatLonGridSpecConverter, RegularGaussianGridSpecConverter]:
    gridspec_converters[x.GS_GRID_TYPE] = x
