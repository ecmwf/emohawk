# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
from contextlib import closing
from itertools import product

import numpy as np

from earthkit.data.core.fieldlist import Field, FieldList
from earthkit.data.core.geography import Geography
from earthkit.data.core.index import Index, MaskIndex, MultiIndex
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.projections import Projection

from . import Reader

GEOGRAPHIC_COORDS = {
    "x": ["x", "projection_x_coordinate", "lon", "longitude"],
    "y": ["y", "projection_y_coordinate", "lat", "latitude"],
}


def as_datetime(self, time):
    return datetime.datetime.strptime(str(time)[:19], "%Y-%m-%dT%H:%M:%S")


def as_level(self, level):
    n = float(level)
    if int(n) == n:
        return int(n)
    return n


class Slice:
    def __init__(self, name, value, index, is_dimension, is_info):
        self.name = name
        self.index = index
        self.value = value
        self.is_dimension = (not is_info,)
        self.is_info = is_info

    def __repr__(self):
        return "[%s:%s=%s]" % (self.name, self.index, self.value)


class TimeSlice(Slice):
    pass


class Coordinate:
    def __init__(self, variable, info):
        self.variable = variable
        # We only support 1D coordinate for now
        # assert len(variable.dims) == 1
        self.is_info = info
        self.is_dimension = not info

        if variable.values.ndim == 0:
            self.values = [self.convert(variable.values)]
        else:
            self.values = [self.convert(t) for t in variable.values.flatten()]

    def make_slice(self, value):
        return self.slice_class(
            self.variable.name,
            value,
            self.values.index(value),
            self.is_dimension,
            self.is_info,
        )

    def __repr__(self):
        return "%s[name=%s,values=%s]" % (
            self.__class__.__name__,
            self.variable.name,
            len(self.values),
        )


class TimeCoordinate(Coordinate):
    slice_class = TimeSlice
    is_dimension = True
    convert = as_datetime


class LevelCoordinate(Coordinate):
    # This class is just in case we want to specialise
    # 'level', othewise, it is the same as OtherCoordinate
    slice_class = Slice
    is_dimension = False
    convert = as_level


class OtherCoordinate(Coordinate):
    slice_class = Slice
    is_dimension = False
    convert = as_level


class DataSet:
    def __init__(self, ds):
        self._ds = ds
        self._bbox = {}
        self._cache = {}

    @property
    def data_vars(self):
        return self._ds.data_vars

    def __getitem__(self, key):
        if key not in self._cache:
            self._cache[key] = self._ds[key]
        return self._cache[key]

    def bbox(self, variable):
        data_array = self[variable]
        dims = data_array.dims

        lat = dims[-2]
        lon = dims[-1]

        if (lat, lon) not in self._bbox:
            dims = data_array.dims

            latitude = data_array[lat]
            longitude = data_array[lon]

            self._bbox[(lat, lon)] = (
                np.amax(latitude.data),
                np.amin(longitude.data),
                np.amin(latitude.data),
                np.amax(longitude.data),
            )

        return self._bbox[(lat, lon)]


class XArrayFieldGeography(Geography):
    def __init__(self, metadata, da, ds, variable):
        self.metadata = metadata
        self._da = da
        self._ds = ds
        self.north, self.west, self.south, self.east = self._ds.bbox(variable)

    def latitudes(self, dtype=None):
        return self.x(dtype=dtype)

    def longitudes(self, dtype=None):
        return self.y(dtype=dtype)

    def _get_xy(self, axis, flatten=False, dtype=None):
        if axis not in ("x", "y"):
            raise ValueError(f"Invalid axis={axis}")

        points = dict()
        for ax in ("x", "y"):
            for coord in self._da.coords:
                if self._da.coords[coord].attrs.get("axis", "").lower() == ax:
                    break
            else:
                candidates = GEOGRAPHIC_COORDS.get(ax, [])
                for coord in candidates:
                    if coord in self._da.coords:
                        break
                else:
                    raise ValueError(f"No coordinate found with axis '{ax}'")
            points[ax] = self._da.coords[coord]
        points["x"], points["y"] = np.meshgrid(points["x"], points["y"])
        if flatten:
            points[axis] = points[axis].flatten()
        if dtype is not None:
            return points[axis].astype(dtype)
        else:
            return points[axis]

    def x(self, dtype=None):
        return self._get_xy("x", flatten=True, dtype=dtype)

    def y(self, dtype=None):
        return self._get_xy("y", flatten=True, dtype=dtype)

    def shape(self):
        return self._da.shape[-2:]

    def _unique_grid_id(self):
        return self.shape

    def projection(self):
        return Projection.from_cf_grid_mapping(**self._grid_mapping().attrs)

    def bounding_box(self):
        return BoundingBox(
            north=self.north, south=self.south, east=self.east, west=self.west
        )

    def _grid_mapping(self):
        if "grid_mapping" in self._da.attrs:
            grid_mapping = self._ds[self._da.attrs["grid_mapping"]]
        else:
            raise AttributeError(
                "no CF-compliant 'grid_mapping' detected in netCDF attributes"
            )
        return grid_mapping


class XArrayMetadata(RawMetadata):
    def __init__(self, field):
        if not isinstance(field, XArrayField):
            raise TypeError(
                f"XArrayMetadata: expected field type XArrayField, got {type(field)}"
            )
        self._field = field
        self._geo = None

        d = dict(self._field._da.attrs)
        d["variable"] = self._field.variable
        for s in self._field.slices:
            if isinstance(s, TimeSlice):
                d[s.name] = to_datetime(s.value)
            else:
                d[s.name] = s.value
        super().__init__(d)

    def override(self, *args, **kwargs):
        return None

    @property
    def geography(self):
        if self._geo is None:
            self._geo = XArrayFieldGeography(
                self, self._field._da, self._field._ds, self._field.variable
            )
        return self._geo

    def datetime(self):
        t = to_datetime(self._field.time)
        return {"base_time": t, "valid_time": t}

    def ls_keys(self):
        LS_KEYS = ["variable", "level", "time", "units"]
        return LS_KEYS


class XArrayField(Field):
    def __init__(self, ds, variable, slices, non_dim_coords):
        super().__init__()

        self._ds = ds
        self._da = ds[variable]

        # self.north, self.west, self.south, self.east = ds.bbox(variable)

        self.variable = variable
        self.slices = slices
        self.non_dim_coords = non_dim_coords
        # self.name = self.variable

        # print(f"ds={ds}")
        # print(f"da={data_array}")
        # print(f"non_dim_coords={non_dim_coords}")

        self.title = getattr(
            self._da,
            "long_name",
            getattr(self._da, "standard_name", self.variable),
        )

        self.time = non_dim_coords.get("valid_time", non_dim_coords.get("time"))

        # print('====', non_dim_coords)

        # print(f"time={self.time}")

        for s in self.slices:
            if isinstance(s, TimeSlice):
                self.time = s.value

            if s.is_info:
                self.title += " (" + s.name + "=" + str(s.value) + ")"

        # print(f"-> time={self.time}")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.variable},"
            + ",".join([f"{s.name}={s.value}" for s in self.slices])
            + ")"
        )

    def _make_metadata(self):
        return XArrayMetadata(self)

    def to_xarray(self):
        dims = self._da.dims
        v = {}
        for s in self.slices:
            if s.is_dimension:
                if s.name in dims:
                    v[s.name] = s.index
        return self._da.isel(**v)

    def to_pandas(self):
        return self.to_xarray().to_pandas()

    def _to_numpy(self):
        return self.to_xarray().to_numpy()

    def _values(self, dtype=None):
        return self._to_numpy().flatten()

    def to_numpy(self, flatten=False, dtype=None):
        values = self._to_numpy()
        if not flatten:
            values = values.reshape(self.shape)
        else:
            values = values.flatten()
        if dtype is not None:
            values = values.astype(dtype)

        return values


class XArrayFieldListCore(FieldList):
    FIELD_TYPE = None

    def __init__(self, ds, *args, **kwargs):
        self.ds = ds
        self._fields = None
        Index.__init__(self, *args, **kwargs)

    @property
    def fields(self):
        if self._fields is None:
            self._scan()
        return self._fields

    def _scan(self):
        if self._fields is None:
            self._fields = self._get_fields()

    def _get_fields(self):
        return self._get_fields_from_ds(DataSet(self.ds))

    def _get_fields_from_ds(self, ds):  # noqa C901
        # Select only geographical variables
        has_lat = False
        has_lon = False

        fields = []

        skip = set()

        for name in ds.data_vars:
            v = ds[name]
            skip.update(getattr(v, "coordinates", "").split(" "))
            skip.update(getattr(v, "bounds", "").split(" "))
            skip.update(getattr(v, "grid_mapping", "").split(" "))

        for name in ds.data_vars:
            if name in skip:
                continue

            v = ds[name]

            coordinates = []

            # self.log.info('Scanning file: %s var=%s coords=%s', self.path, name, v.coords)

            info = [value for value in v.coords if value not in v.dims]
            non_dim_coords = {}
            for coord in v.coords:
                if coord not in v.dims:
                    non_dim_coords[coord] = ds[coord].values
                    continue

                c = ds[coord]

                # self.log.info("COORD %s %s %s %s", coord, type(coord), hasattr(c, 'calendar'), c)

                standard_name = getattr(c, "standard_name", "")
                axis = getattr(c, "axis", "")
                long_name = getattr(c, "long_name", "")

                use = False

                if (
                    standard_name.lower() in GEOGRAPHIC_COORDS["x"]
                    or (long_name == "longitude")
                    or (axis == "X")
                ):
                    has_lon = True
                    use = True

                if (
                    standard_name.lower() in GEOGRAPHIC_COORDS["y"]
                    or (long_name == "latitude")
                    or (axis == "Y")
                ):
                    has_lat = True
                    use = True

                # print(f"  standard_name={standard_name}")

                # Of course, not every one sets the standard_name
                if (
                    standard_name in ["time", "forecast_reference_time"]
                    or long_name in ["time"]
                    or axis == "T"
                ):
                    # we might not be able to convert time to datetime
                    try:
                        coordinates.append(TimeCoordinate(c, coord in info))
                        use = True
                    except ValueError:
                        break

                # TODO: Support other level types
                if standard_name in [
                    "air_pressure",
                    "model_level_number",
                    "altitude",
                ] or long_name in [
                    "pressure_level"
                ]:  # or axis == 'Z':
                    coordinates.append(LevelCoordinate(c, coord in info))
                    use = True

                if axis in ("X", "Y"):
                    use = True

                if not use:
                    coordinates.append(OtherCoordinate(c, coord in info))

            if not (has_lat and has_lon):
                # self.log.info("NetCDFReader: skip %s (Not a 2 field)", name)
                continue

            for values in product(*[c.values for c in coordinates]):
                slices = []
                for value, coordinate in zip(values, coordinates):
                    slices.append(coordinate.make_slice(value))

                fields.append(self.FIELD_TYPE(ds, name, slices, non_dim_coords))

        # if not fields:
        #     raise Exception("NetCDFReader no 2D fields found in %s" % (self.path,))

        return fields

    def to_pandas(self):
        return self.to_xarray().to_pandas()

    def to_xarray(self, **kwargs):
        return self.ds

    def to_netcdf(self, *args, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataArray.to_netcdf`.
        """
        return self.ds.to_netcdf(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, XArrayFieldList) for _ in sources)
        return XArrayMultiFieldList(sources)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return XArrayMaskFieldList(*args, **kwargs)


class XArrayFieldList(XArrayFieldListCore):
    VERSION = 1

    def __init__(self, ds, **kwargs):
        self.FIELD_TYPE = XArrayField
        super().__init__(ds, **kwargs)

    def __getitem__(self, n):
        if isinstance(n, int):
            return self.fields[n]
        else:
            return super().__getitem__(n)

    def __len__(self):
        return len(self.fields)


class XArrayMaskFieldList(XArrayFieldListCore, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class XArrayMultiFieldList(XArrayFieldListCore, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)

    def to_xarray(self, **kwargs):
        import xarray as xr

        return xr.merge([x.ds for x in self.indexes], **kwargs)


class NetCDFMetadata(XArrayMetadata):
    pass


class NetCDFField(XArrayField):
    def _make_metadata(self):
        return NetCDFMetadata(self)


class NetCDFFieldList(XArrayFieldListCore):
    def __init__(self, path, *args, **kwargs):
        self.FIELD_TYPE = NetCDFField
        self.path = path
        # self._fields = None
        super().__init__(None, *args, **kwargs)

    def _get_fields(self):
        import xarray as xr

        with closing(
            xr.open_mfdataset(self.path, combine="by_coords")
        ) as ds:  # or nested
            return self._get_fields_from_ds(DataSet(ds))

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, NetCDFFieldList) for _ in sources)
        return NetCDFMultiFieldList(sources)

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return NetCDFMaskFieldList(*args, **kwargs)

    def to_xarray(self, **kwargs):
        return type(self).to_xarray_multi_from_paths(self.path, **kwargs)

    def to_netcdf(self, *args, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataArray.to_netcdf`.
        """
        return self.to_xarray().to_netcdf(*args, **kwargs)

    @classmethod
    def to_xarray_multi_from_paths(cls, paths, **kwargs):
        import xarray as xr

        if not isinstance(paths, list):
            paths = [paths]

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))

        return xr.open_mfdataset(
            paths,
            **options,
        )


class NetCDFFieldListInFiles(NetCDFFieldList):
    pass


class NetCDFFieldListInOneFile(NetCDFFieldListInFiles):
    VERSION = 1

    def __init__(self, path, **kwargs):
        assert isinstance(path, str), path
        super().__init__(path, **kwargs)

    def __getitem__(self, n):
        if isinstance(n, int):
            return self.fields[n]
        else:
            return super().__getitem__(n)

    def __len__(self):
        return len(self.fields)


class NetCDFMaskFieldList(NetCDFFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class NetCDFMultiFieldList(NetCDFFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)

    def to_xarray(self, **kwargs):
        return NetCDFFieldList.to_xarray_multi_from_paths(
            [x.path for x in self.indexes], **kwargs
        )


class NetCDFFieldListReader(NetCDFFieldListInOneFile, Reader):
    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        NetCDFFieldList.__init__(self, path)

    def __repr__(self):
        return "NetCDFFieldListReader(%s)" % (self.path,)

    def mutate_source(self):
        # A NetCDFReader is a source itself
        return self


class NetCDFReader(Reader):
    def __init__(self, source, path):
        Reader.__init__(self, source, path)

    def __repr__(self):
        return "NetCDFReader(%s)" % (self.path,)

    def to_numpy(self, flatten=False):
        arr = self.to_xarray().to_array().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def to_pandas(self):
        return self.to_xarray().to_pandas()

    def to_xarray(self, **kwargs):
        return type(self).to_xarray_multi_from_paths([self.path], **kwargs)

    @classmethod
    def to_xarray_multi_from_paths(cls, paths, **kwargs):
        import xarray as xr

        if not isinstance(paths, list):
            paths = [paths]

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))

        return xr.open_mfdataset(
            paths,
            **options,
        )


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = (b"\x89HDF", b"CDF\x01", b"CDF\x02")
        return len(magic) >= 4 and magic[:4] in type_id
    return False


def reader(source, path, magic=None, deeper_check=False):
    if _match_magic(magic, deeper_check):
        fs = NetCDFFieldListReader(source, path)
        if len(fs) > 0:
            return fs
        else:
            return NetCDFReader(source, path)
