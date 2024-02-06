# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from collections import deque

from earthkit.data.readers import stream_reader
from earthkit.data.sources.memory import MemoryBaseSource

from . import Source

LOG = logging.getLogger(__name__)


def parse_stream_kwargs(**kwargs):
    group_by = kwargs.pop("group_by", None)
    batch_size = kwargs.pop("batch_size", 1)
    batch_size, group_by = check_stream_kwargs(batch_size, group_by)
    stream_kwargs = dict(batch_size=batch_size, group_by=group_by)
    return (stream_kwargs, kwargs)


def check_stream_kwargs(batch_size, group_by):
    if group_by is None:
        group_by = []

    if isinstance(group_by, str):
        group_by = [group_by]
    else:
        try:
            group_by = list(group_by)
        except Exception:
            raise TypeError(f"unsupported types in group_by={group_by}")

    if group_by and not all([isinstance(x, str) for x in group_by]):
        raise TypeError(f"group_by={group_by} must contain str values")

    if batch_size is None:
        batch_size = 1

    if batch_size < 0:
        raise ValueError(f"batch_size={batch_size} cannot be negative")

    return (batch_size, group_by)


class StreamMemorySource(MemoryBaseSource):
    def __init__(self, stream, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream
        self._reader_ = None

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream, True)
            if self._reader_ is None:
                raise TypeError(f"could not create reader for stream={self._stream}")
        return self._reader_

    def mutate(self):
        source = self._reader.mutate_source()
        if source not in (None, self):
            source._parent = self
            return source
        return self


class StreamSourceBase(Source):
    def __init__(self, stream, *, batch_size=1, group_by=None):
        super().__init__()
        self._reader_ = None
        self._stream = stream
        self.batch_size, self.group_by = check_stream_kwargs(batch_size, group_by)

    def __iter__(self):
        return self

    def mutate(self):
        return self

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream, False)
            if self._reader_ is None:
                raise TypeError(f"could not create reader for stream={self._stream}")
        return self._reader_


class StreamSingleSource(StreamSourceBase):
    def __init__(self, stream, **kwargs):
        super().__init__(stream, **kwargs)
        assert self.batch_size == 1

    def __next__(self):
        return self._reader.__next__()


class StreamBatchSource(StreamSourceBase):
    def __init__(self, stream, **kwargs):
        super().__init__(stream, **kwargs)
        assert self.batch_size > 1

    def __next__(self):
        return self._get_batch(self.batch_size)

    def _get_batch(self, n):
        return self._reader.read_batch(n)


class StreamGroupSource(StreamSourceBase):
    def __init__(self, stream, **kwargs):
        super().__init__(stream, **kwargs)
        assert self.group_by

    def __next__(self):
        return self._reader.read_group(self.group_by)


class MultiStreamSource(Source):
    def __init__(self, sources, group_by=None, batch_size=1):
        self.sources = sources
        if not isinstance(self.sources, deque):
            self.sources = deque(self.sources)
        self.group_by = group_by
        self.batch_size = batch_size
        self.current = None

    def mutate(self):
        if not self.group_by:
            if self.batch_size == 0:
                from .multi import MultiSource

                return MultiSource([s() for s in self.sources])
            elif self.batch_size > 1:
                return MultiStreamBatchSource(
                    self.sources, batch_size=self.batch_size, group_by=self.group_by
                )

        return self

    def __iter__(self):
        return self

    def _next_source(self):
        try:
            return self.sources.popleft()()
        except IndexError:
            self.sources.clear()
            pass

    def __next__(self):
        if self.current is None:
            self.current = self._next_source()
            if self.current is None:
                raise StopIteration

        try:
            return self.current.__next__()
        except StopIteration:
            self.current = self._next_source()
            if self.current is None:
                raise StopIteration
            return self.current.__next__()


class MultiStreamBatchSource(MultiStreamSource):
    def mutate(self):
        return self

    def __next__(self):
        if self.current is None:
            if self.sources:
                self.current = self._next_source()
            else:
                raise StopIteration

        delta = self.batch_size
        try:
            r = self.current._get_batch(self.batch_size)
            delta -= len(r)
        except StopIteration:
            r = None

        while delta > 0:
            self.current = self._next_source()
            if self.current is None:
                break
            else:
                try:
                    r1 = self.current._get_batch(delta)
                    assert r1 is not None
                    assert len(r1) > 0
                    r = r + r1 if r is not None else r1
                    assert len(r) > 0
                    delta = self.batch_size - len(r)
                except StopIteration:
                    break

        if r is None or len(r) == 0:
            raise StopIteration

        return r


class StreamSource(StreamSourceBase):
    def __init__(self, stream, **kwargs):
        super().__init__(stream, **kwargs)

        # print(f"kwargs={kwargs} {id(kwargs)}")
        # if kwargs:
        #     raise TypeError(f"got invalid keyword argument(s): {list(kwargs.keys())}")

    def mutate(self):
        assert self._reader_ is None

        return _from_stream(
            self._stream, batch_size=self.batch_size, group_by=self.group_by
        )


class StreamSourceMaker:
    def __init__(self, source, stream_kwargs):
        self.in_source = source
        self.stream_kwargs = dict(stream_kwargs)
        self.source = None

    def __call__(self):
        if self.source is None:
            stream = self.in_source.to_stream()
            self.source = _from_stream(stream, **self.stream_kwargs)

            prev = None
            src = self.source
            while src is not prev:
                prev = src
                src = src.mutate()
            self.source = src

        return self.source


def _from_stream(stream, group_by, batch_size):
    _kwargs = dict(batch_size=batch_size, group_by=group_by)

    if group_by:
        return StreamGroupSource(stream, **_kwargs)
    elif batch_size == 0:
        return StreamMemorySource(stream)
    elif batch_size > 1:
        return StreamBatchSource(stream, **_kwargs)
    elif batch_size == 1:
        return StreamSingleSource(stream, **_kwargs)

    raise ValueError(f"Unsupported stream parameters {batch_size=} {group_by=}")


def _from_source(source, **kwargs):
    stream_kwargs, kwargs = parse_stream_kwargs(**kwargs)

    if kwargs:
        raise TypeError(f"got invalid keyword argument(s): {list(kwargs.keys())}")

    if not isinstance(source, (list, tuple)):
        source = [source]

    if len(source) == 1:
        maker = StreamSourceMaker(source[0], stream_kwargs)
        return maker()
    else:
        sources = [StreamSourceMaker(s, stream_kwargs) for s in source]
        return MultiStreamSource(sources, **stream_kwargs)


source = StreamSource
