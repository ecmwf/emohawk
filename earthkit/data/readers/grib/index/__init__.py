# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math
import os
from abc import abstractmethod

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.index import Index, MaskIndex, MultiIndex
from earthkit.data.decorators import alias_argument
from earthkit.data.indexing.database import (
    FILEPARTS_KEY_NAMES,
    MORE_KEY_NAMES,
    MORE_KEY_NAMES_WITH_UNDERSCORE,
    STATISTICS_KEY_NAMES,
)
from earthkit.data.readers.grib.codes import GribField
from earthkit.data.readers.grib.pandas import PandasMixIn
from earthkit.data.readers.grib.xarray import XarrayMixIn
from earthkit.data.utils import progress_bar
from earthkit.data.utils.availability import Availability

LOG = logging.getLogger(__name__)


class GribFieldList(PandasMixIn, XarrayMixIn, FieldList):
    r"""Represents a list of :obj:`GribField <data.readers.grib.codes.GribField>`\ s.

    We can **iterate** through the fields as follows:

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
    >>> len(ds)
    6
    >>> for f in ds:
    ...     print(f)
    ...
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

    :obj:`Fieldset` objects can be **concatenated** with the + operator:

    >>> import earthkit.data
    >>> ds1 = earthkit.data.from_source("file", "docs/examples/test.grib")
    >>> len(ds1)
    2
    >>> ds2 = earthkit.data.from_source("file", "docs/examples/test6.grib")
    >>> len(ds2)
    6
    >>> ds = ds1 + ds2
    >>> len(ds)
    8

    Standard Python slicing works:

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
    >>> len(ds)
    6
    >>> ds[0]
    GribField(t,1000,20180801,1200,0,0)
    >>> for f in ds[0:3]:
    ...     print(f)
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    >>> for f in ds[0:4:2]:
    ...     print(f)
    GribField(t,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    >>> ds[-1]
    GribField(v,850,20180801,1200,0,0)
    >>> for f in ds[-2:]:
    ...     print(f)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

    Slicing also works with a list or an ndarray:

    >>> for f in ds[[1, 3]]:
    ...     print(f)
    ...
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    >>> for f in ds[np.array([1, 3])]:
    ...     print(f)
    ...
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)

    """

    _availability = None

    def __init__(self, *args, **kwargs):
        if self.availability_path is not None and os.path.exists(
            self.availability_path
        ):
            self._availability = Availability(self.availability_path)

        Index.__init__(self, *args, **kwargs)

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return GribMaskFieldList(*args, **kwargs)

    @property
    def availability_path(self):
        return None

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, GribFieldList) for _ in sources)
        return GribMultiFieldList(sources)

    def _custom_availability(self, ignore_keys=None, filter_keys=lambda k: True):
        def dicts():
            for i in progress_bar(
                iterable=range(len(self)), desc="Building availability"
            ):
                dic = self.get_metadata(i)

                for k in list(dic.keys()):
                    if not filter_keys(k):
                        dic.pop(k)
                        continue
                    if ignore_keys and k in ignore_keys:
                        dic.pop(k)
                        continue
                    if dic[k] is None:
                        dic.pop(k)
                        continue

                yield dic

        from earthkit.data.utils.availability import Availability

        return Availability(dicts())

    @property
    def availability(self):
        if self._availability is not None:
            return self._availability
        LOG.debug("Building availability")

        self._availability = self._custom_availability(
            ignore_keys=FILEPARTS_KEY_NAMES
            + STATISTICS_KEY_NAMES
            + MORE_KEY_NAMES_WITH_UNDERSCORE
            + MORE_KEY_NAMES
        )
        return self.availability

    def _is_full_hypercube(self):
        non_empty_coords = {
            k: v
            for k, v in self.availability._tree.unique_values().items()
            if len(v) > 1
        }
        expected_size = math.prod([len(v) for k, v in non_empty_coords.items()])
        return len(self) == expected_size

    @alias_argument("levelist", ["level", "levellist"])
    @alias_argument("levtype", ["leveltype"])
    @alias_argument("param", ["variable", "parameter"])
    @alias_argument("number", ["realization", "realisation"])
    @alias_argument("class", "klass")
    def _normalize_kwargs_names(self, **kwargs):
        return kwargs


class GribMaskFieldList(GribFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class GribMultiFieldList(GribFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)


class GribFieldListInFiles(GribFieldList):
    # Remote FieldLists (with urls) are also here,
    # as the actual fieldlist is accessed on a file in cache.
    # This class changes the interface (__getitem__ and __len__)
    # into the interface (part and number_of_parts).
    def _getitem(self, n):
        if isinstance(n, int):
            part = self.part(n if n >= 0 else len(self) + n)
            return GribField(part.path, part.offset, part.length)

    def __len__(self):
        return self.number_of_parts()

    @abstractmethod
    def part(self, n):
        self._not_implemented()

    @abstractmethod
    def number_of_parts(self):
        self._not_implemented()
