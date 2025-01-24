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


class CSVEncodedData(EncodedData):
    def __init__(self, df):
        self.df = df

    def to_bytes(self):
        raise NotImplementedError

    def to_file(self, f, **kwargs):
        self.df.to_csv(f, **kwargs)

    def metadata(self, key):
        raise NotImplementedError


class CSVEncoder(Encoder):
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

    def _encode(self, data, **kwargs):
        assert data is not None
        return CSVEncodedData(data.to_pandas())

    def _encode_field(self, field, **kwargs):
        return self._encode(field, **kwargs)

    def _encode_fieldlist(self, fieldlist, **kwargs):
        raise NotImplementedError


encoder = CSVEncoder
