# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.readers import stream_reader
from earthkit.data.sources.memory import MemoryBaseSource

from . import Source

LOG = logging.getLogger(__name__)


class StreamMemorySource(MemoryBaseSource):
    def __init__(self, reader, **kwargs):
        super().__init__(**kwargs)
        self._reader = reader

    def __iter__(self):
        return iter(self._reader)


class StreamSource(Source):
    def __init__(self, stream, group_by=None, **kwargs):
        super().__init__()
        self._stream = stream
        self._reader_ = None
        self._group_by = group_by if group_by is not None else []

        if isinstance(self._group_by, str):
            self._group_by = [self._group_by]
        else:
            try:
                self._group_by = list(self._group_by)
            except Exception:
                raise TypeError(f"unsupported types in group_by={self._group_by}")

        if self._group_by and not all([isinstance(x, str) for x in self._group_by]):
            raise TypeError(f"`group_by`={self._group_by} must contain str values")

        if self._group_by and "batch_size" in kwargs:
            raise TypeError(
                "got an invalid keyword argument. batch_size cannot be used when group_by is set"
            )

        self._batch_size = kwargs.pop("batch_size", 1)
        if self._batch_size is None:
            self._batch_size = 1

        if self._batch_size < 0:
            raise ValueError(f"batch_size={self._batch_size} cannot be negative")
        if kwargs:
            raise TypeError(f"got invalid keyword argument(s): {list(kwargs.keys())}")

    @property
    def batch_size(self):
        return self._batch_size

    @property
    def group_by(self):
        return self._group_by

    def mutate(self):
        if self.batch_size == 0:
            source = StreamMemorySource(self._reader)
            return source
        else:
            return self

    def __iter__(self):
        return self

    def __next__(self):
        assert self.batch_size > 0
        if self.group_by:
            return self._reader.read_group(self.group_by)
        else:
            if self.batch_size == 1:
                return self._reader.__next__()
            else:
                return self._reader.read_batch(self.batch_size)

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream)
            self._stream = None
        return self._reader_


source = StreamSource
