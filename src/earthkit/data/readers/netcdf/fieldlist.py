# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from functools import cached_property
from itertools import product

import deprecation

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex

from .coords import LevelCoordinate
from .coords import OtherCoordinate
from .coords import TimeCoordinate
from .dataset import GEOGRAPHIC_COORDS
from .dataset import DataSet
from .field import NetCDFField
from .field import XArrayField

LOG = logging.getLogger(__name__)


def get_fields_from_ds(
    ds,
    field_type=None,
    check_only=False,
):  # noqa C901

    fields = []

    skip = set()

    def _skip_attr(v, attr_name):
        attr_val = getattr(v, attr_name, "")
        if isinstance(attr_val, str):
            skip.update(attr_val.split(" "))

    for name in ds.data_vars:
        v = ds[name]
        _skip_attr(v, "coordinates")
        _skip_attr(v, "bounds")
        _skip_attr(v, "grid_mapping")

    for name in ds.data_vars:
        # Select only geographical variables
        has_lat = False
        has_lon = False

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
            coord_name = getattr(c, "name", "")

            # LOG.debug(f"{standard_name=} {long_name=} {axis=} {coord_name}")
            use = False

            if (
                standard_name.lower() in GEOGRAPHIC_COORDS["x"]
                or (long_name == "longitude")
                or (axis == "X")
                or coord_name.lower() in GEOGRAPHIC_COORDS["x"]
            ):
                has_lon = True
                use = True

            if (
                standard_name.lower() in GEOGRAPHIC_COORDS["y"]
                or (long_name == "latitude")
                or (axis == "Y")
                or coord_name.lower() in GEOGRAPHIC_COORDS["y"]
            ):
                has_lat = True
                use = True

            # Of course, not every one sets the standard_name
            if (
                standard_name in ["time", "forecast_reference_time"]
                or long_name in ["time"]
                or coord_name.lower() in ["time"]
                or axis == "T"
            ):
                # we might not be able to convert time to datetime
                try:
                    coordinates.append(TimeCoordinate(c, coord in info))
                    use = True
                except ValueError:
                    break

            # TODO: Support other level types
            if (
                standard_name
                in [
                    "air_pressure",
                    "model_level_number",
                    "altitude",
                ]
                or long_name in ["pressure_level"]
                or coord_name in ["level"]
            ):  # or axis == 'Z':
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

            if check_only:
                return True

            fields.append(field_type(ds, name, slices, non_dim_coords))

    # if not fields:
    #     raise Exception("NetCDFReader no 2D fields found in %s" % (self.path,))

    if check_only:
        return False

    return fields


class XArrayFieldListCore(FieldList):
    FIELD_TYPE = None

    def __init__(self, *args, **kwargs):
        self._fields = None
        super().__init__(*kwargs)

    # @cached_property
    @property
    def fields(self):
        if self._fields is None:
            self._fields = self._get_fields(DataSet(self.xr_dataset))
        return self._fields

    def has_fields(self):
        if self._fields is None:
            return get_fields_from_ds(
                DataSet(self.xr_dataset),
                field_type=self.FIELD_TYPE,
                check_only=True,
            )
        else:
            return len(self._fields) > 0

    def _get_fields(self, ds):
        return get_fields_from_ds(ds, field_type=self.FIELD_TYPE)

    def to_pandas(self, **kwargs):
        return self.to_xarray(**kwargs).to_pandas()

    def to_xarray(self, **kwargs):
        return self.xr_dataset

    @classmethod
    def to_xarray_multi_from_paths(cls, paths, **kwargs):
        import xarray as xr

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))
        if not options:
            options = dict(**kwargs)

        return xr.open_mfdataset(
            paths,
            **options,
        )

    def to_netcdf(self, *args, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataArray.to_netcdf`.
        """
        return self.to_xarray().to_netcdf(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, XArrayFieldList) for _ in sources)
        return XArrayMultiFieldList(sources)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return XArrayMaskFieldList(*args, **kwargs)

    def _write(self, target, **kwargs):
        assert target is not None
        encoder = kwargs.get("encoder", None)
        if encoder is None and kwargs.get("default_encoder", None) is None:
            kwargs["default_encoder"] = "netcdf"
        target._write(self, **kwargs)

    def _encode_grib(self, encoder, **kwargs):
        return encoder._from_xarray(self.to_xarray(), **kwargs)

    def default_encoder(self):
        return "netcdf"


class XArrayFieldList(XArrayFieldListCore):
    VERSION = 1

    def __init__(self, ds, **kwargs):
        self.FIELD_TYPE = XArrayField
        self._ds = ds
        super().__init__(**kwargs)

    @cached_property
    def xr_dataset(self):
        return self._ds

    def _getitem(self, n):
        if isinstance(n, int):
            return self.fields[n]

    def __len__(self):
        return len(self.fields)

    def __repr__(self):
        return "XArrayFieldList "  # TODO: some __repr__ of the data: {self.data}


class XArrayMaskFieldList(XArrayFieldListCore, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_mask(self, self)


class XArrayMultiFieldList(XArrayFieldListCore, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_multi(self, self)

    def to_xarray(self, **kwargs):
        import xarray as xr

        return xr.merge([x._ds for x in self._indexes], **kwargs)


class NetCDFFieldList(XArrayFieldListCore):
    FIELD_TYPE = NetCDFField

    def __init__(self, path, *args, **kwargs):
        self.path = path
        super().__init__(None, *args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, NetCDFFieldList) for _ in sources)
        return NetCDFMultiFieldList(sources)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return NetCDFMaskFieldList(*args, **kwargs)

    def to_xarray(self, **kwargs):
        # if self.path.startswith("http"):
        #     return xr.open_dataset(self.path, **kwargs)
        return type(self).to_xarray_multi_from_paths([self.path], **kwargs)

    # def save(self, *args, **kwargs):
    #     return self.to_netcdf(*args, **kwargs)

    # def write(self, *args, **kwargs):
    #     return self.to_netcdf(*args, **kwargs)


class NetCDFFieldListFromFileOrURL(NetCDFFieldList):
    def __init__(self, path_or_url, **kwargs):
        assert isinstance(path_or_url, str), path_or_url
        super().__init__(path_or_url, **kwargs)
        self.path_or_url = path_or_url

    @cached_property
    def xr_dataset(self):
        import xarray as xr

        return xr.open_dataset(self.path_or_url)

    def _getitem(self, n):
        if isinstance(n, int):
            return self.fields[n]

    def __len__(self):
        return len(self.fields)


class NetCDFFieldListFromFile(NetCDFFieldListFromFileOrURL):
    def __init__(self, path):
        super().__init__(path)

    def __repr__(self):
        return "NetCDFFieldListFromFile(%s)" % (self.path_or_url,)

    def write(self, f, **kwargs):
        import shutil

        with open(self.path, "rb") as s:
            shutil.copyfileobj(s, f, 1024 * 1024)


class NetCDFFieldListFromURL(NetCDFFieldListFromFileOrURL):
    def __init__(self, url):
        super().__init__(url)

    def __repr__(self):
        return "NetCDFFieldListFromURL(%s)" % (self.path_or_url,)


class NetCDFMaskFieldList(NetCDFFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_mask(self, self)
        self.path = "<mask>"

    # TODO: Implement this, but discussion required
    def to_xarray(self, *args, **kwargs):
        self._not_implemented()

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    def write(self, *args, **kwargs):
        self._not_implemented()

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    def save(self, *args, **kwargs):
        self._not_implemented()


class NetCDFMultiFieldList(NetCDFFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_multi(self, self)
        # self.paths = [s.path for s in args[0]]
        self.path = "<multi>"

    def to_xarray(self, **kwargs):
        # try:

        if not kwargs:
            kwargs = dict(combine="by_coords")

        for x in self._indexes:
            if isinstance(x, NetCDFMaskFieldList):
                raise NotImplementedError(
                    "NetCDFMultiFieldList.to_xarray() does not supports NetCDFMaskFieldList"
                )

        return NetCDFFieldList.to_xarray_multi_from_paths([x.path for x in self._indexes], **kwargs)
