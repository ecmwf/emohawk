# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import eccodes

from earthkit.data.readers import Reader
from earthkit.data.readers.grib.codes import GribCodesHandle, GribField
from earthkit.data.readers.grib.index import GribFieldList

LOG = logging.getLogger(__name__)


class GribMemoryReader(Reader):
    def __init__(self):
        self._peeked = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._peeked is not None:
            msg = self._peeked
            self._peeked = None
            return msg
        handle = self._next_handle()
        msg = self._message_from_handle(handle)
        if handle is not None:
            return msg
        raise StopIteration

    def _next_handle(self):
        raise NotImplementedError

    def _message_from_handle(self, handle):
        if handle is not None:
            return GribFieldInMemory(GribCodesHandle(handle, None, None))

    def peek(self):
        """Returns the next available message without consuming it"""
        if self._peeked is None:
            handle = self._next_handle()
            self._peeked = self._message_from_handle(handle)
        return self._peeked

    def read_batch(self, n):
        fields = []
        for _ in range(n):
            try:
                fields.append(self.__next__())
            except StopIteration:
                break
        if not fields:
            raise StopIteration

        return GribFieldListInMemory.from_fields(fields)

    def read_group(self, group):
        assert isinstance(group, list)

        fields = []
        current_group = {}
        while True:
            f = self.peek()
            if f is not None:
                group_md = f._attributes(group)
                if not current_group:
                    current_group = group_md
                if current_group == group_md:
                    fields.append(f)
                    self.__next__()
                else:
                    break
            elif fields:
                break
            else:
                raise StopIteration

        return GribFieldListInMemory.from_fields(fields)


class GribFileMemoryReader(GribMemoryReader):
    def __init__(self, path):
        super().__init__()
        self.fp = open(path, "rb")

    def __del__(self):
        self.fp.close()

    def _next_handle(self):
        return eccodes.codes_new_from_file(self.fp, eccodes.CODES_PRODUCT_GRIB)


class GribMessageMemoryReader(GribMemoryReader):
    def __init__(self, buf):
        super().__init__()
        self.buf = buf

    def __del__(self):
        self.buf = None

    def _next_handle(self):
        if self.buf is None:
            return None
        handle = eccodes.codes_new_from_message(self.buf)
        self.buf = None
        return handle


class GribStreamReader(GribMemoryReader):
    """Wrapper around eccodes.Streamreader. The problem is that when iterating via
    the StreamReader it returns an eccodes.GRIBMessage that releases the handle when deleted.
    However, the handle has to be managed by earthkit-data so we access it directly
    using _next_handle
    """

    def __init__(self, stream):
        super().__init__()
        self._stream = stream
        self._reader = eccodes.StreamReader(stream)

    def __del__(self):
        self._stream.close()

    def _next_handle(self):
        return self._reader._next_handle()

    def mutate(self):
        return self

    def mutate_source(self):
        return self


class GribFieldInMemory(GribField):
    """Represents a GRIB message in memory"""

    def __init__(self, handle):
        super().__init__(None, None, None)
        self._handle = handle

    @GribField.handle.getter
    def handle(self):
        return self._handle

    @GribField.handle.getter
    def offset(self):
        return None


class GribFieldListInMemory(GribFieldList, Reader):
    """Represent a GRIB field list in memory"""

    @staticmethod
    def from_fields(fields):
        fs = GribFieldListInMemory(None, None)
        fs._fields = fields
        fs._loaded = True
        return fs

    def __init__(self, source, reader, *args, **kwargs):
        """
        The reader must support __next__.
        """
        if source is not None:
            Reader.__init__(self, source, None)
        GribFieldList.__init__(self, *args, **kwargs)

        self._reader = reader
        self._loaded = False
        self._fields = []

    def __len__(self):
        self._load()
        return len(self._fields)

    def _getitem(self, n):
        self._load()
        if isinstance(n, int):
            n = n if n >= 0 else len(self) + n
            return self._fields[n]

    def _load(self):
        if not self._loaded:
            self._fields = [f for f in self._reader]
            self._loaded = True
            self._reader = None

    def mutate_source(self):
        return self

    @classmethod
    def merge(cls, readers):
        assert all(isinstance(s, GribFieldListInMemory) for s in readers), readers
        assert len(readers) > 1

        from itertools import chain

        return GribFieldListInMemory.from_fields(list(chain(*[f for f in readers])))
