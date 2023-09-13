# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import numpy as np

from earthkit.data.core.fieldlist import Field, FieldList
from earthkit.data.core.index import MaskIndex, MultiIndex
from earthkit.data.core.metadata import Metadata

LOG = logging.getLogger(__name__)


class NumpyField(Field):
    def __init__(self, array, metadata):
        self._array = array
        super().__init__(metadata=metadata)

    def _make_metadata(self):
        pass

    def _values(self, dtype=None):
        if dtype is None:
            return self._array
        else:
            return self._array.astype(dtype)

    def write(self, f):
        from earthkit.data.writers import write

        write(f, self.values, self._metadata, check_nans=False)


class NumpyFieldList(FieldList):
    def __init__(self, array, metadata, *args, **kwargs):
        self._array = array
        self._metadata = metadata

        if not isinstance(self._metadata, list):
            self._metadata = [self._metadata]

        for md in self._metadata:
            if not isinstance(md, Metadata):
                raise TypeError("metadata must be a subclass of MetaData")

        if self._array.shape[0] != len(self._metadata):
            import numpy as np

            # we have a single array and a single metadata
            if len(self._metadata) == 1 and self._shape_match(
                self._array.shape, self._metadata[0].geography.shape()
            ):
                self._array = np.array([self._array])
            else:
                raise ValueError(
                    (
                        f"first array dimension ({self._array.shape[0]}) differs "
                        f"from number of metadata objects ({len(self._metadata)})"
                    )
                )

        super().__init__(*args, **kwargs)

    def __getitem__(self, n):
        return NumpyField(self._array[n], self._metadata[n])

    def __len__(self):
        return self._array.shape[0]

    def _shape_match(self, shape1, shape2):
        if shape1 == shape2:
            return True
        if len(shape1) == 1 and shape1[0] == np.prod(shape2):
            return True
        return False


class NumpyMaskFieldList(NumpyFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class NumpyMultiFieldList(NumpyFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
