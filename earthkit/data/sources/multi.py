# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.mergers import make_merger, merge_by_class
from earthkit.data.sources.empty import EmptySource
from earthkit.data.utils import tqdm
from earthkit.data.utils.bbox import BoundingBox

from . import Source

LOG = logging.getLogger(__name__)


class MultiSource(Source):
    def __init__(self, *sources, filter=None, merger=None, **kwargs):
        super().__init__(**kwargs)
        if len(sources) == 1 and isinstance(sources[0], list):
            sources = sources[0]

        sources = self._from_sources(sources)

        self.sources = [s.mutate() for s in sources if not s.ignore()]
        self.filter = filter
        self.merger = merger
        self._lengths = [None] * len(self.sources)

    def ignore(self):
        return len(self.sources) == 0

    def mutate(self):
        if len(self.sources) == 1:
            return self.sources[0].mutate()

        if len(self.sources) == 0:
            return EmptySource()

        if self.merger is None:
            merged = merge_by_class(self.sources)
            if merged is not None:
                return merged.mutate()

        return self

    def _set_dataset(self, dataset):
        super()._set_dataset(dataset)
        for s in self.sources:
            s._set_dataset(dataset)

    def __iter__(self):
        return itertools.chain(*self.sources)

    def __getitem__(self, n):
        if n < 0:
            n = len(self) + n

        i = 0
        while n >= self._length(i):
            n -= self._length(i)
            i += 1
        return self.sources[i][n]

    def sel(self, *args, **kwargs):
        raise NotImplementedError

    def __len__(self):
        return sum(self._length(i) for i, _ in enumerate(self.sources))

    def _length(self, i):
        if self._lengths[i] is None:
            self._lengths[i] = len(self.sources[i])
        return self._lengths[i]

    def __repr__(self) -> str:
        string = ",".join(repr(s) for s in self.sources)
        return f"{self.__class__.__name__}({string})"

    def save(self, path, **kwargs):
        with open(path, "wb") as f:
            for s in self.sources:
                s.write(f, **kwargs)

    def graph(self, depth=0):
        print(" " * depth, self.__class__.__name__, self.merger)
        for s in self.sources:
            s.graph(depth + 3)

    def to_xarray(self, **kwargs):
        return make_merger(self.merger, self.sources).to_xarray(**kwargs)

    def to_pandas(self, **kwargs):
        return make_merger(self.merger, self.sources).to_pandas(**kwargs)

    def statistics(self, **kwargs):
        return make_merger(self.merger, self.sources).statistics(**kwargs)

    def _from_sources(self, sources):
        callables = []
        has_callables = False
        for s in sources:
            if callable(s):
                has_callables = True
                callables.append(s)
            else:
                callables.append(lambda *args, **kwargs: s)

        if not has_callables:
            return sources

        nthreads = min(self.settings("number-of-download-threads"), len(callables))
        if nthreads < 2:
            return [s() for s in sources]

        def _call(s, *args, **kwargs):
            return s(*args, **kwargs)

        with SoftThreadPool(nthreads=nthreads) as pool:
            futures = [pool.submit(_call, s, observer=pool) for s in sources]

            iterator = (f.result() for f in futures)
            sources = list(tqdm(iterator, leave=False, total=len(futures)))

        return sources

    def datetime(self, **kwargs):
        result = dict()
        for s in self.sources:
            result.update(s.datetime(**kwargs))
        return {k: sorted(v) for k, v in result.items()}

    def bounding_box(self):
        return BoundingBox.union([s.bounding_box() for s in self.sources])


source = MultiSource
