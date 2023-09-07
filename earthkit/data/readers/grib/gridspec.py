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


def missing_is_none(x):
    return None if x == 2147483647 else x


def make_gridspec(metadata):
    grid_type = metadata.get("gridType", None)
    if grid_type in grid_specs:
        maker = grid_specs[grid_type]
        d = maker(metadata).make()
        return GridSpec(d)
    else:
        raise TypeError(f"Cannot make GridSpec, unsupported grid_type={grid_type}")


class GridSpecMaker(metaclass=ABCMeta):
    POSITIVE_SCAN_DIR = 1
    NEGATIVE_SCAN_DIR = -1
    GRID_TYPE = None

    def __init__(self, md):
        if isinstance(md, dict):
            md = RawMetadata(md)
        self.md = md
        assert md.get("gridType", None) == self.GRID_TYPE

    def _get_first_valid(self, keys, desc=""):
        for k in keys:
            v = self.md.get(k, None)
            if v is not None:
                return v
        if desc:
            raise ValueError(f"Could not determine {desc}")
        else:
            raise ValueError(f"None of the keys have valid value: {keys}")

    def first_lon(self):
        return self.md.get("longitudeOfFirstGridPointInDegrees")

    def last_lon(self):
        return self.md.get("longitudeOfLastGridPointInDegrees", None)

    def first_lat(self):
        return self.md.get("latitudeOfFirstGridPointInDegrees", None)

    def last_lat(self):
        return self.md.get("latitudeOfLastGridPointInDegrees", None)

    def north(self):
        return max(self.first_lat(), self.last_lat())

    def south(self):
        return min(self.first_lat(), self.last_lat())

    def x_scan_dir(self):
        v = self.md.get("iScansNegatively", None)
        if v is not None:
            return self.POSITIVE_SCAN_DIR if v == 0 else self.NEGATIVE_SCAN_DIR
        else:
            v = self.md.get("iScansPositively", None)
            if v is not None:
                return self.POSITIVE_SCAN_DIR if v == 1 else self.NEGATIVE_SCAN_DIR
            else:
                raise ValueError("Could not determine i-direction scanning mode")

    @abstractmethod
    def make(self):
        pass


class LatLonGridSpecMaker(GridSpecMaker):
    GRID_TYPE = "regular_ll"

    def __init__(self, md):
        super().__init__(md)

    def make(self):
        d = dict()
        d["type"] = self.GRID_TYPE
        dx, dy = self._get_grid()
        d["grid"] = [abs(dx), abs(dy)]
        d["area"] = [self.north(), self.west(), self.south(), self.east()]

        for key in [
            "jPointsAreConsecutive",
            "iScansNegatively",
            "jScansPositively",
        ]:
            v = self.md.get(key, None)
            if v is not None:
                d[key] = v

        return d

    def _get_grid(self):
        dx = self.md.get("iDirectionIncrementInDegrees", None)
        dy = self.md.get("jDirectionIncrementInDegrees", None)

        if dx is None:
            nx = self._get_first_valid(
                ["numberOfPointsAlongAParallel", "Ni"],
                desc="number of points in longitude",
            )
            lon_range = self.last_lon() - self.first_lon()
            if nx == 1:
                dx = 1.0
            else:
                dx = lon_range / (nx - 1.0)

        if dy is None:
            ny = self._get_first_valid(
                ["numberOfPointsAlongAMeridian", "Nj"],
                desc="number of points in latitude",
            )
            lat_range = self.last_lat() - self.first_lat()
            if ny == 1:
                dy = 1.0
            else:
                dy = lat_range / (ny - 1.0)

        return dx, dy

    def west(self):
        if self.x_scan_dir() == self.POSITIVE_SCAN_DIR:
            return self.first_lon()
        else:
            return self.last_lon()

    def east(self):
        if self.x_scan_dir() == self.POSITIVE_SCAN_DIR:
            return self.last_lon()
        else:
            return self.first_lon()


class GaussianGridSpecMaker(GridSpecMaker):
    def __init__(self, *args, label=None):
        if label not in ["F", "N", "O"]:
            raise ValueError("Invalid Gaussian grid label={label}")
        self.label = label
        super().__init__(*args)

    def make(self):
        d = dict()
        d["type"] = self.GRID_TYPE
        N = self.md.get("N")
        global_grid = self.md.get("global", 0) == 1
        d["grid"] = f"{self.label}{N}"

        if not global_grid:
            d["area"] = [self.north(), self.west(), self.south(), self.east()]

        for key in [
            "jPointsAreConsecutive",
            "iScansNegatively",
            "jScansPositively",
        ]:
            v = self.md.get(key, None)
            if v is not None:
                d[key] = v

        return d

    def west(self):
        return self.first_lon()

    def east(self):
        return self.last_lon()


class RegularGaussianGridSpecMaker(GaussianGridSpecMaker):
    GRID_TYPE = "regular_gg"

    def __init__(self, md):
        super().__init__(md, label="F")


class ReducedGaussianGridSpecMaker(GaussianGridSpecMaker):
    GRID_TYPE = "reduced_gg"

    def __init__(self, md):
        octahedral = md.get("isOctahedral", 0) == 1
        label = "O" if octahedral else "N"
        super().__init__(md, label=label)


class ReducedLatLonGridSpecMaker(LatLonGridSpecMaker):
    GRID_TYPE = "reduced_ll"

    def __init__(self, md):
        super().__init__(md)

    def make(self):
        d = dict()
        d["type"] = self.GRID_TYPE
        _, dy = self._get_grid()
        d["grid"] = abs(dy)
        d["area"] = [self.north(), self.west(), self.south(), self.east()]

        for key in [
            "jPointsAreConsecutive",
            "iScansNegatively",
            "jScansPositively",
        ]:
            v = self.md.get(key, None)
            if v is not None:
                d[key] = v

        return d

    def _get_grid(self):
        dy = self.md.get("jDirectionIncrementInDegrees", None)

        if dy is None:
            ny = self._get_first_valid(
                ["numberOfPointsAlongAMeridian", "Nj"],
                desc="number of points in latitude",
            )
            lat_range = self.last_lat() - self.first_lat()
            if ny == 1:
                dy = 1.0
            else:
                dy = lat_range / (ny - 1.0)

        return None, dy


class RotatedLatLonGridSpecMaker(LatLonGridSpecMaker):
    GRID_TYPE = "rotated_ll"

    def __init__(self, md):
        super().__init__(md)

    def make(self):
        d = dict()
        d["type"] = self.GRID_TYPE
        dx, dy = self._get_grid()
        d["grid"] = [abs(dx), abs(dy)]
        d["area"] = [self.north(), self.west(), self.south(), self.east()]
        d["rotation"] = [self.south_pole_lat(), self.south_pole_lon()]
        for key in [
            "angleOfRotationInDegrees",
            "jPointsAreConsecutive",
            "iScansNegatively",
            "jScansPositively",
        ]:
            v = self.md.get(key, None)
            if v is not None:
                d[key] = v

        return d

    def south_pole_lat(self):
        return self.md.get("latitudeOfSouthernPoleInDegrees", None)

    def south_pole_lon(self):
        return self.md.get("longitudeOfSouthernPoleInDegrees", None)


grid_specs = {
    "regular_ll": LatLonGridSpecMaker,
    "regular_gg": RegularGaussianGridSpecMaker,
    "reduced_gg": ReducedGaussianGridSpecMaker,
    "reduced_ll": ReducedLatLonGridSpecMaker,
    "rotated_ll": RotatedLatLonGridSpecMaker,
}
