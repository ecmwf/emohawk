# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.readers import memory_reader

from . import Source

LOG = logging.getLogger(__name__)


class MemoryBaseSource(Source):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __iter__(self):
        return iter(self._reader)

    def __len__(self):
        return len(self._reader)

    def __getitem__(self, n):
        return self._reader[n]

    def sel(self, *args, **kwargs):
        return self._reader.sel(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        return self._reader.order_by(*args, **kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_numpy(self, **kwargs):
        return self._reader.to_numpy(**kwargs)

    @property
    def values(self):
        return self._reader.values

    def to_fieldlist(self, *args, **kwargs):
        return self._reader.to_fieldlist(*args, **kwargs)

    def save(self, path, **kwargs):
        return self._reader.save(path, **kwargs)

    def write(self, f, **kwargs):
        return self._reader.write(f, **kwargs)

    def scaled(self, *args, **kwargs):
        return self._reader.scaled(*args, **kwargs)

    def _attributes(self, names):
        return self._reader._attributes(names)

    # def __fspath__(self):
    #     return self.path

    def metadata(self, *args, **kwargs):
        return self._reader.metadata(*args, **kwargs)

    def ls(self, *args, **kwargs):
        return self._reader.ls(*args, **kwargs)

    def describe(self, *args, **kwargs):
        return self._reader.describe(*args, **kwargs)

    def datetime(self, **kwargs):
        return self._reader.datetime(**kwargs)

    def bounding_box(self):
        return self._reader.bounding_box()

    def statistics(self, **kwargs):
        return self._reader.statistics(**kwargs)


class MemorySource(MemoryBaseSource):
    def __init__(self, buf, **kwargs):
        self._buf = buf
        self._reader_ = None

    def mutate(self):
        source = self._reader.mutate_source()
        if source not in (None, self):
            source._parent = self
            return source
        return self

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = memory_reader(self, self._buf)
            self._buf = None
        return self._reader_


source = MemorySource
