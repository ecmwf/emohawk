# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from datetime import timedelta
from functools import cached_property

import numpy as np

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import MetadataAccessor
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.indexing.fieldlist import ClonedFieldCore
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import to_datetime

from .coords import LevelSlice
from .coords import TimeSlice

LOG = logging.getLogger(__name__)


class XArrayFieldGeography(Geography):
    def __init__(self, metadata, ds, variable):
        self.metadata = metadata
        self.variable = variable
        self.ds = ds
        self.north, self.west, self.south, self.east = self.ds.bbox(variable)

    def latitudes(self, dtype=None):
        return self.ds._get_latlon(self.data_array, flatten=True, dtype=dtype)[0]

    def longitudes(self, dtype=None):
        return self.ds._get_latlon(self.data_array, flatten=True, dtype=dtype)[1]

    def x(self, dtype=None):
        return self.ds._get_xy(self.data_array, flatten=True, dtype=dtype)[0]

    def y(self, dtype=None):
        return self.ds._get_xy(self.data_array, flatten=True, dtype=dtype)[1]

    def shape(self):
        _, coords = self.ds._get_xy_coords(self.data_array)
        return tuple([self.data_array.coords[v].size for v in coords])

    def _unique_grid_id(self):
        return self.shape()

    def projection(self):
        from earthkit.data.utils.projections import Projection

        return Projection.from_cf_grid_mapping(**self._grid_mapping().attrs)

    def bounding_box(self):
        return BoundingBox(north=self.north, south=self.south, east=self.east, west=self.west)

    def _grid_mapping(self):
        da = self.data_array
        if "grid_mapping" in da.attrs:
            grid_mapping = self.ds[da.attrs["grid_mapping"]]
        else:
            raise AttributeError("no CF-compliant 'grid_mapping' detected in netCDF attributes")
        return grid_mapping

    def gridspec(self):
        raise NotImplementedError("gridspec is not implemented for netcdf/xarray")

    @property
    def data_array(self):
        return self.ds[self.variable]

    def resolution(self):
        # TODO: implement resolution
        return None

    def mars_grid(self):
        # TODO: implement mars_grid
        return None

    def mars_area(self):
        # TODO: code me
        return [self.north, self.west, self.south, self.east]


class XArrayMetadata(RawMetadata):
    LS_KEYS = ["variable", "level", "valid_datetime", "units"]
    NAMESPACES = [
        "default",
        "mars",
    ]
    MARS_KEYS = ["param", "step", "levelist", "levtype", "number", "date", "time"]

    ACCESSORS = {
        "valid_datetime": ["valid_datetime", "valid_time"],
        "base_datetime": ["base_datetime", "forecast_reference_time", "base_time"],
    }

    def __init__(self, field):
        if not isinstance(field, XArrayField):
            raise TypeError(f"XArrayMetadata: expected field type XArrayField, got {type(field)}")
        self._field = field

        data_array = field._ds[field.variable]
        d = dict(data_array.attrs)

        time = field.non_dim_coords.get("valid_time", field.non_dim_coords.get("time"))
        level = None
        level_type = "sfc"

        for s in field.slices:
            if isinstance(s, TimeSlice):
                time = s.value

            if isinstance(s, LevelSlice):
                level = s.value
                level_type = {"pressure": "pl"}.get(s.name, s.name)

        step = 0
        if time is not None:
            self.time = to_datetime(time)
            if "forecast_reference_time" in field._ds.data_vars:
                forecast_reference_time = field._ds["forecast_reference_time"].data
                assert forecast_reference_time.ndim == 0, forecast_reference_time
                forecast_reference_time = forecast_reference_time.astype("datetime64[s]")
                forecast_reference_time = forecast_reference_time.astype(object)
                step = (time - forecast_reference_time).total_seconds()
                assert step % 3600 == 0, step
                step = int(step // 3600)
                d["step"] = step

            date = self.time - timedelta(hours=step)
            d["date"] = int(date.strftime("%Y%m%d"))
            d["time"] = int(date.strftime("%H%M"))

        else:
            self.time = None

        d["variable"] = self._field.variable
        d["level"] = level
        d["levtype"] = level_type

        super().__init__(d)

    def override(self, *args, **kwargs):
        if not args and not kwargs:
            return self
        return None

    @cached_property
    def geography(self):
        return XArrayFieldGeography(self, self._field._ds, self._field.variable)

    def namespaces(self):
        return self.NAMESPACES

    def as_namespace(self, namespace=None):
        if not isinstance(namespace, str) and namespace is not None:
            raise TypeError("namespace must be a str or None")

        if namespace == "default" or namespace == "" or namespace is None:
            return dict(self)
        elif namespace == "mars":
            return self._as_mars()

    def _as_mars(self):
        return dict(
            param=self["variable"],
            step=self.get("step", None),
            levelist=self["level"],
            levtype=self["levtype"],
            number=None,
            date=self.get("date", None),
            time=self.get("time", None),
        )

    def datetime(self):
        return {
            "base_time": self.base_datetime(),
            "valid_time": self.valid_datetime(),
        }

    def base_datetime(self):
        v = self.valid_datetime()
        if v is not None:
            return v - timedelta(hours=self.get("hour", 0))

    def valid_datetime(self):
        if self.time is not None:
            return to_datetime(self.time)

    @MetadataAccessor(ACCESSORS)
    def get(self, key, default=None, *, raise_on_missing=False, **kwargs):
        if key.startswith("mars."):
            key = key[5:]
            if key not in self.MARS_KEYS:
                if raise_on_missing:
                    raise KeyError(f"Invalid key '{key}' in namespace='mars'")
                else:
                    return default
                # if kwargs.get("raise_on_missing", False):
                #     raise KeyError(f"Invalid key '{key}' in namespace='mars'")
                # else:
                #     return kwargs.get("default", None)

        def _key_name(key):
            if key == "param":
                key = "variable"
            elif key == "levelist":
                key = "level"
            return key

        return super().get(_key_name(key), default=default, raise_on_missing=raise_on_missing, **kwargs)

    def ls_keys(self):
        return self.LS_KEYS

    def data_format(self):
        return "netcdf"


class XArrayField(Field):
    def __init__(self, ds, variable, slices, non_dim_coords):
        super().__init__()
        self._ds = ds
        self._da = ds[variable]

        # self.north, self.west, self.south, self.east = ds.bbox(variable)

        self.variable = variable
        self.slices = slices
        self.non_dim_coords = non_dim_coords
        self.name = self.variable

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.variable},"
            + ",".join([f"{s.name}={s.value}" for s in self.slices])
            + ")"
        )

    @cached_property
    def _metadata(self):
        return XArrayMetadata(self)

    def to_xarray(self):
        da = self._ds[self.variable]
        dims = da.dims
        v = {}
        for s in self.slices:
            if s.is_dimension:
                if s.name in dims:
                    v[s.name] = s.index
        return da.isel(**v)

    def to_pandas(self):
        return self.to_xarray().to_pandas()

    # def _to_numpy(self):
    #     return self.to_xarray().to_numpy()

    def _to_numpy(self):
        dimensions = dict((s.name, s.index) for s in self.slices)
        # values = self.owner.xr_dataset[self.variable].isel(dimensions).values
        values = self._ds[self.variable].isel(dimensions).values
        return values

    def _values(self, dtype=None):
        if dtype is None:
            return self._to_numpy()
        else:
            return self._to_numpy().astype(dtype, copy=False)

    @cached_property
    def grid_mapping(self):
        def tidy(x):
            if isinstance(x, np.ndarray):
                return x.tolist()
            if isinstance(x, (tuple, list)):
                return [tidy(y) for y in x]
            if isinstance(x, dict):
                return {k: tidy(v) for k, v in x.items()}
            return x

        # return tidy(
        #     self.owner.xr_dataset[
        #         self.owner.xr_dataset[self.variable].grid_mapping
        #     ].attrs
        # )

        return tidy(self._ds[self._ds[self.variable].grid_mapping].attrs)

    def clone(self, **kwargs):
        return ClonedXarrayField(self, **kwargs)


class ClonedXarrayField(ClonedFieldCore, XArrayField):
    def __init__(self, field, **kwargs):
        ClonedFieldCore.__init__(self, field, **kwargs)
        XArrayField.__init__(self, field.ds, field.variable, field.slices, field.non_dim_coords)


class NetCDFMetadata(XArrayMetadata):
    pass


class NetCDFField(XArrayField):
    @cached_property
    def _metadata(self):
        return NetCDFMetadata(self)
