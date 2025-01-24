# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from functools import cached_property

import numpy as np

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.utils.bbox import BoundingBox

from . import Reader


class GeoTIFFGeography(Geography):

    def __init__(self, ds):
        self._ds = ds
        self.x_dim = ds.rio.x_dim
        self.y_dim = ds.rio.y_dim

    def _latlon_coords(self):
        try:
            from pyproj import Transformer
        except ImportError:
            raise ImportError("geotiff handling requires 'pyproj' to be installed")

        return Transformer.from_crs(self._ds.rio.crs, "EPSG:4326", always_xy=True).transform(
            *self._xy_coords()
        )

    def latitudes(self, dtype=None):
        return self._latlon_coords()[0]

    def longitudes(self, dtype=None):
        return self._latlon_coords()[1]

    def _xy_coords(self):
        x = self._ds.coords[self.x_dim].values
        y = self._ds.coords[self.y_dim].values
        return np.meshgrid(x, y)

    def x(self, dtype=None):
        return self._xy_coords()[0]

    def y(self, dtype=None):
        return self._xy_coords()[1]

    def shape(self):
        return self._ds.rio.height, self._ds.rio.width

    def _unique_grid_id(self):
        return (*self.shape(), self._ds.rio.crs.to_wkt())

    def projection(self):
        from earthkit.data.utils.projections import Projection

        return Projection.from_cf_grid_mapping(**self._grid_mapping)

    @property
    def _grid_mapping(self):
        if self._ds.rio.grid_mapping == "spatial_ref":
            return self._ds.coords["spatial_ref"].attrs
        raise NotImplementedError

    def bounding_box(self):
        left, bottom, right, top = self._ds.rio.transform_bounds("EPSG:4326")
        return BoundingBox(north=top, west=left, south=bottom, east=right)

    def gridspec(self):
        raise NotImplementedError

    def resolution(self):
        # Get width and height of pixels in units of the CRS
        x, y = self._ds.rio.resolution()
        crs = self._ds.rio.crs
        units, factor = crs.units_factor
        # Geographic coordinate systems use latitude and longitude
        if crs.is_geographic and units == "degree":
            x = abs(round(x * 1_000_000) / 1_000_000)
            y = abs(round(y * 1_000_000) / 1_000_000)
            assert x == y, (x, y)
            return x
        raise NotImplementedError(f"resolution for {crs} ({units}, {factor})")

    def mars_grid(self):
        raise NotImplementedError

    def mars_area(self):
        raise NotImplementedError


class GeoTIFFMetadata(RawMetadata):

    LS_KEYS = ["variable", "band"]

    def __init__(self, field, band, geography=None):
        self._field = field
        self._geo = geography
        super().__init__({"variable": field._da.name, "band": band, **field._da.attrs})

    @property
    def geography(self):
        if self._geo is None:
            self._geo = GeoTIFFGeography(self._field._da)
        return self._geo

    def ls_keys(self):
        return self.LS_KEYS


class GeoTIFFField(Field):
    """A GeoTIFF band"""

    def __init__(self, da, band, geography=None):
        super().__init__()
        self._da = da
        self._geo = geography
        self.band = band

    def __repr__(self):
        return f"{self.__class__.__name__}({self.band},{self._da.name})"

    @cached_property
    def _metadata(self):
        return GeoTIFFMetadata(self, self.band, geography=self._geo)

    def to_xarray(self):
        return self._da

    def to_pandas(self):
        # Series with x and y in MultiIndex, not y-Index and x in columns
        series = self._da.to_pandas().stack()
        series.name = self._da.name
        return series

    def _values(self, dtype=None):
        return self._da.values.astype(dtype)

    def write(self, f):
        self._not_implemented()


class GeoTIFFFieldList(FieldList):
    """A list of GeoTIFF bands"""

    FIELD_TYPE = GeoTIFFField

    def __init__(self, path, **kwargs):
        self._fields = None
        self.path = path
        self._ds = self.rioxarray_read(band_as_variable=True, mask_and_scale=True, decode_times=True)
        # Shared geography instance for all fields/bands
        self._geo = GeoTIFFGeography(self._ds)
        super().__init__(**kwargs)

    def rioxarray_read(self, **kwargs):
        try:
            import rioxarray
        except ImportError:
            raise ImportError("geotiff handling requires 'rioxarray' to be installed")

        options = dict()
        options.update(kwargs.get("rioxarray_open_rasterio_kwargs", {}))
        if not options:
            options = dict(**kwargs)

        return rioxarray.open_rasterio(self.path, **options)

    def to_xarray(self, **kwargs):
        return self.rioxarray_read(**kwargs)

    def to_pandas(self):
        import pandas as pd

        series = [field.to_pandas() for field in self]
        return pd.concat(series, keys=[s.name for s in series])

    def __len__(self):
        return len(self._ds.data_vars)

    def _getitem(self, n):
        if isinstance(n, int):
            return self.fields[n]

    @property
    def fields(self):
        if self._fields is None:
            self._fields = self._get_fields(self._ds)
        return self._fields

    def _get_fields(self, ds, names=None):
        fields = []
        # Follow GDAL convention and count GeoTIFF bands from 1
        for band, (name, da) in enumerate(ds.data_vars.items(), start=1):
            # Prefer long_name over band_* naming of band_as_variable=True
            if "long_name" in da.attrs:
                da = da.rename(da.attrs["long_name"])
            fields.append(self.FIELD_TYPE(da, band, geography=self._geo))
        return fields

    def describe(self, *args, **kwargs):
        self._not_implemented()

    # def save(self, filename, append=False, **kwargs):
    #     self._not_implemented()

    # def write(self, f, **kwargs):
    #     self._not_implemented()


class GeoTIFFReader(GeoTIFFFieldList, Reader):
    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        GeoTIFFFieldList.__init__(self, path)

    def __repr__(self):
        return f"GeoTIFFReader({self.path})"

    def mutate_source(self):
        return self


def _match_magic(magic):
    if magic is not None:
        # https://docs.ogc.org/is/19-008r4/19-008r4.html#_tiff_core_test
        # Bytes 0-1: 'II' (little endian) or 'MM' (big endian)
        # Bytes 2-3: 42 as short in the corresponding byte order
        # Bytes 4-7: offset to first image file directory
        # ASCII: I = 73, M = 77, * = 42
        return len(magic) >= 8 and magic[:4] in {b"II*\x00", b"MM\x00*"}
    return False


def reader(source, path, *, magic=None, **kwargs):
    if _match_magic(magic):
        return GeoTIFFReader(source, path)
