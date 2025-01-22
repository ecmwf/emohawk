# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import EncodedData
from . import Encoder

LOG = logging.getLogger(__name__)


class GeoTIFFEncodedData(EncodedData):

    _GDAL_DRIVER = "GTiff"

    def __init__(self, ds):
        self.ds = ds

    def to_bytes(self, **kwargs):
        import rasterio.io

        m = rasterio.io.MemoryFile()
        self._to_raster(m, **kwargs)
        return m.getbuffer()

    def to_file(self, f, **kwargs):
        self._to_raster(f, **kwargs)

    def _to_raster(self, dst, **kwargs):
        options = {"driver": self._GDAL_DRIVER}
        options.update(kwargs)
        self.ds.rio.to_raster(dst, **options)

    def metadata(self, key):
        raise NotImplementedError


class GeoTIFFEncoder(Encoder):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(self, data, **kwargs):
        if data is None:
            raise ValueError("No data to encode")

        from ..wrappers import get_wrapper

        data = get_wrapper(data)
        return data._encode(self, **kwargs)

    def _encode(self, data, **kwargs):
        ds = data.to_xarray()
        if ds.rio.crs is None:
            crs = data.projection().to_cartopy_crs()
            ds.rio.write_crs(crs, inplace=True)
        return GeoTIFFEncodedData(ds)

    def _encode_field(self, field, **kwargs):
        return self._encode(field, **kwargs)

    def _encode_fieldlist(self, fieldlist, **kwargs):
        return self._encode(fieldlist, **kwargs)


encoder = GeoTIFFEncoder
