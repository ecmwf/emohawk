# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.readers.grib.index import GribFieldList
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import step_to_delta
from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)


class VirtualGribGeography(Geography):
    pass


class VirtualGribMetadata(RawMetadata):
    KEY_TYPES = {
        "s": str,
        "l": int,
        "d": float,
        "str": str,
        "int": int,
        "float": float,
        "": None,
    }

    KEY_TYPE_SUFFIX = {str: ":s", int: ":l", float: ":d"}

    KEY_GROUPS = {
        ("dataDate", "date"),
        ("dataTime", "time"),
        ("level", "levelist"),
        ("step", "endStep", "stepRange"),
        ("param", "shortName"),
    }

    def __init__(self, m):
        super().__init__(m)

    def _get(self, key, astype=None, default=None, raise_on_missing=True):
        def _key_name(key):
            if key == "_param_id":
                key = "paramId"
            return key

        key = _key_name(key)
        key, _, key_type_str = key.partition(":")
        try:
            key_type = self.KEY_TYPES[key_type_str]
        except KeyError:
            raise ValueError(f"Key type={key_type_str} not supported")

        if key not in self:
            for v in self.KEY_GROUPS:
                if key in v:
                    for k in v:
                        if k in self:
                            key = k
                            break

            if key not in self and key in ("step", "endStep", "stepRange"):
                return self._default_step(astype=astype)

        if key_type is None:
            key_type = astype

        if key == "stepRange" and key_type is None:
            key_type = str

        return super()._get(
            key, astype=key_type, default=default, raise_on_missing=raise_on_missing
        )

    def shape(self):
        Nj = self.get("Nj", None)
        Ni = self.get("Ni", None)
        if Ni is None or Nj is None:
            n = len(self.get("values"))
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    def as_namespace(self, ns):
        return {}

    def ls_keys(self):
        return GribMetadata.LS_KEYS

    def namespaces(self):
        return []

    def latitudes(self, dtype=None):
        v = self.get("latitudes")
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def longitudes(self, dtype=None):
        v = self.get("longitudes")
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def x(self, dtype=None):
        grid_type = self.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.longitudes(dtype=dtype)

    def y(self, dtype=None):
        grid_type = self.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.latitudes(dtype=dtype)

    def _unique_grid_id(self):
        return self.get("md5GridSection", None)

    def datetime(self):
        return {
            "base_time": self._base_datetime(),
            "valid_time": self._valid_datetime(),
        }

    def _base_datetime(self):
        date = int(self.get("date", None))
        time = int(self.get("time", None))
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def _valid_datetime(self):
        step = self.get("endStep", None)
        return self._base_datetime() + step_to_delta(step)

    def _default_step(self, astype=None):
        step = "0"
        if astype is None:
            return step
        else:
            return astype(step)

    def projection(self):
        return Projection.from_proj_string(self.get("projTargetString", None))

    def bounding_box(self):
        return BoundingBox(
            north=self.get("latitudeOfFirstGridPointInDegrees", None),
            south=self.get("latitudeOfLastGridPointInDegrees", None),
            west=self.get("longitudeOfFirstGridPointInDegrees", None),
            east=self.get("longitudeOfLastGridPointInDegrees", None),
        )

    from earthkit.data.core.geography import Geography


class VirtualGribField(Field):
    def __init__(self, d):
        super().__init__(metadata=VirtualGribMetadata(d))

    def _values(self, dtype=None):
        v = self._metadata["values"]
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def _make_metadata(self):
        pass


class GribFromDicts(GribFieldList):
    def __init__(self, list_of_dicts, *args, **kwargs):
        self.list_of_dicts = list_of_dicts
        super().__init__(*args, **kwargs)

    def __getitem__(self, n):
        return VirtualGribField(self.list_of_dicts[n])

    def __len__(self):
        return len(self.list_of_dicts)


source = GribFromDicts
