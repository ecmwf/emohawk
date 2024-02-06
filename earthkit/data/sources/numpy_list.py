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
from earthkit.data.readers.grib.pandas import PandasMixIn
from earthkit.data.readers.grib.xarray import XarrayMixIn

LOG = logging.getLogger(__name__)


class NumpyField(Field):
    r"""Represent a field consisting of an ndarray and metadata object.

    Parameters
    ----------
    array: ndarray
        Array storing the values of the field
    metadata: :class:`Metadata`
        Metadata object describing the field metadata.
    """

    def __init__(self, array, metadata):
        self._array = array
        super().__init__(metadata=metadata)

    def _make_metadata(self):
        pass

    def _values(self, dtype=None):
        if dtype is None:
            return self._array
        else:
            return self._array.astype(dtype, copy=False)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def write(self, f, **kwargs):
        r"""Write the field to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        **kwargs: dict, optional
            Other keyword arguments passed to :meth:`data.writers.grib.GribWriter.write`.
        """
        from earthkit.data.writers import write

        write(f, self.values, self._metadata, **kwargs)


class NumpyFieldListCore(PandasMixIn, XarrayMixIn, FieldList):
    def __init__(self, array, metadata, *args, **kwargs):
        self._array = array
        self._metadata = metadata

        if not isinstance(self._metadata, list):
            self._metadata = [self._metadata]

        if isinstance(self._array, np.ndarray):
            if self._array.shape[0] != len(self._metadata):
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
        elif isinstance(self._array, list):
            if len(self._array) != len(self._metadata):
                raise ValueError(
                    (
                        f"array len ({len(self._array)}) differs "
                        f"from number of metadata objects ({len(self._metadata)})"
                    )
                )

            for i, a in enumerate(self._array):
                if not isinstance(a, np.ndarray):
                    raise ValueError(
                        f"All array element must be an ndarray. Type at position={i} is {type(a)}"
                    )

        else:
            raise TypeError("array must be an ndarray or a list of ndarrays")

        # hide internal metadata related to values
        self._metadata = [md._hide_internal_keys() for md in self._metadata]

        super().__init__(*args, **kwargs)

    def _shape_match(self, shape1, shape2):
        if shape1 == shape2:
            return True
        if len(shape1) == 1 and shape1[0] == np.prod(shape2):
            return True
        return False

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return NumpyMaskFieldList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, NumpyFieldListCore) for _ in sources)
        merger = ListMerger(sources)
        # merger = MultiUnwindMerger(sources)
        return merger.to_fieldlist()

    def __repr__(self):
        return f"{self.__class__.__name__}(fields={len(self)})"

    def _to_numpy_fieldlist(self, **kwargs):
        if self[0]._array_matches(self._array[0], **kwargs):
            return self
        else:
            return type(self)(self.to_numpy(**kwargs), self._metadata)

    def save(self, filename, append=False, check_nans=True, bits_per_value=16):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str
            The target file path.
        append: bool
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists.
        check_nans: bool
            Replace nans in the values with GRIB missing values when generating the output.
        bits_per_value: int
            Set the ``bitsPerValue`` GRIB key in the generated output.
        """
        super().save(
            filename,
            append=append,
            check_nans=check_nans,
            bits_per_value=bits_per_value,
        )


class MultiUnwindMerger:
    def __init__(self, sources):
        self.sources = list(self._flatten(sources))

    def _flatten(self, sources):
        if isinstance(sources, NumpyMultiFieldList):
            for s in sources.indexes:
                yield from self._flatten(s)
        elif isinstance(sources, list):
            for s in sources:
                yield from self._flatten(s)
        else:
            yield sources

    def to_fieldlist(self):
        return NumpyMultiFieldList(self.sources)


class ListMerger:
    def __init__(self, sources):
        self.sources = sources

    def to_fieldlist(self):
        array = []
        metadata = []
        for s in self.sources:
            for f in s:
                array.append(f._array)
                metadata.append(f._metadata)
        return NumpyFieldList(array, metadata)


class NumpyFieldList(NumpyFieldListCore):
    r"""Represent a list of :obj:`NumpyField <data.sources.numpy_list.NumpyField>`\ s.

    The preferred way to create a NumpyFieldList is to use either the
    static :obj:`from_numpy` method or the :obj:`to_fieldlist` method.

    See Also
    --------
    from_numpy
    to_fieldlist

    """

    def _getitem(self, n):
        if isinstance(n, int):
            return NumpyField(self._array[n], self._metadata[n])

    def __len__(self):
        return (
            len(self._array) if isinstance(self._array, list) else self._array.shape[0]
        )


class NumpyMaskFieldList(NumpyFieldListCore, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class NumpyMultiFieldList(NumpyFieldListCore, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
