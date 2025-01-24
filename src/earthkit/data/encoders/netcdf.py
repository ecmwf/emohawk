# (C) Copyright 2023 ECMWF.
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


class NetCDFEncodedData(EncodedData):
    def __init__(self, ds):
        self.ds = ds

    def to_bytes(self):
        return self.ds.to_netcdf(None)

    def to_file(self, f):
        self.ds.earthkit.to_netcdf(f)
        # self.ds.to_netcdf(f)

    def metadata(self, key):
        raise NotImplementedError


class NetCDFEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.wrappers import get_wrapper

            data = get_wrapper(data)
            return data._encode(self, **kwargs)
        else:
            raise ValueError("No data to encode")

    def _encode(
        self,
        data=None,
        values=None,
        min=None,
        max=None,
        check_nans=False,
        metadata={},
        template=None,
        # return_bytes=False,
        missing_value=9999,
        **kwargs,
    ):
        return NetCDFEncodedData(data.to_xarray())

    def _encode_field(self, field, **kwargs):
        return self._encode(field, **kwargs)

    def _encode_fieldlist(self, data, **kwargs):
        return self._encode(data, **kwargs)


encoder = NetCDFEncoder
