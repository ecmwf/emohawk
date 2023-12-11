# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import logging
import math
from abc import abstractmethod
from collections import defaultdict

import numpy as np

import earthkit.data
from earthkit.data.core.order import build_remapping, normalize_order_by
from earthkit.data.core.select import normalize_selection, selection_from_index
from earthkit.data.sources import Source

LOG = logging.getLogger(__name__)


class OrderOrSelection:
    actions = {}

    def __str__(self):
        return f"{self.__class__.__name__}({self.actions})"

    @property
    def is_empty(self):
        return not self.actions


class Selection(OrderOrSelection):
    def __init__(self, kwargs, remapping=None):
        self.remapping = build_remapping(remapping)

        class InList:
            def __init__(self, lst):
                self.first = True
                self.lst = lst  # lazy casting: lst will be modified

            def __call__(self, x):
                if self.first and x is not None:
                    self.lst = [
                        type(x) if not type(x) is type(y) else y for y in self.lst
                    ]
                    self.first = False
                return x in self.lst

        class InSlice:
            def __init__(self, slc):
                self.slc = slc
                if self.slc.start is None and self.slc.stop is None:
                    raise ValueError("Invalid selection value: slice(None, None)")

                if (
                    self.slc.start is not None
                    and self.slc.stop is not None
                    and self.slc.stop < self.slc.start
                ):
                    self.slc = slice(self.slc.stop, self.slc.start)

            def __call__(self, x):
                return not (
                    (self.slc.start is not None and x < self.slc.start)
                    or (self.slc.stop is not None and x > self.slc.stop)
                )

        self.actions = {}
        for k, v in kwargs.items():
            if v is None or v is earthkit.data.ALL:
                self.actions[k] = lambda x: True
                continue

            if callable(v):
                self.actions[k] = v
                continue

            if isinstance(v, slice):
                self.actions[k] = InSlice(v)
                continue

            if not isinstance(v, (list, tuple, set)):
                v = [v]

            v = set(v)

            self.actions[k] = InList(v)

    def match_element(self, element):
        metadata = self.remapping(element.metadata)
        return all(v(metadata(k, default=None)) for k, v in self.actions.items())


class OrderBase(OrderOrSelection):
    def __init__(self, kwargs, remapping):
        self.actions = self.build_actions(kwargs)
        self.remapping = remapping

    @abstractmethod
    def build_actions(self, kwargs):
        raise NotImplementedError()

    def compare_elements(self, a, b):
        a_metadata = self.remapping(a.metadata)
        b_metadata = self.remapping(b.metadata)
        for k, v in self.actions.items():
            n = v(a_metadata(k, default=None), b_metadata(k, default=None))
            if n != 0:
                return n
        return 0


class Order(OrderBase):
    def build_actions(self, kwargs):
        actions = {}

        def ascending(a, b):
            if a == b:
                return 0
            if a > b:
                return 1
            if a < b:
                return -1
            raise ValueError(f"{a},{b}")

        def descending(a, b):
            if a == b:
                return 0
            if a > b:
                return -1
            if a < b:
                return 1
            raise ValueError(f"{a},{b}")

        class Compare:
            def __init__(self, order):
                self.order = order

            def __call__(self, a, b):
                return ascending(self.get(a), self.get(b))

            def get(self, x):
                return self.order[x]

        for k, v in kwargs.items():
            if v == "ascending" or v is None:
                actions[k] = ascending
                continue

            if v == "descending":
                actions[k] = descending
                continue

            if callable(v):
                actions[k] = v
                continue

            assert isinstance(
                v, (list, tuple)
            ), f"Invalid argument for {k}: {v} ({type(v)})"

            order = {}
            for i, key in enumerate(v):
                order[str(key)] = i
                try:
                    order[int(key)] = i
                except ValueError:
                    pass
                try:
                    order[float(key)] = i
                except ValueError:
                    pass
            actions[k] = Compare(order)

        return actions


class Index(Source):
    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return MaskIndex(*args, **kwargs)

    @abstractmethod
    def __len__(self):
        self._not_implemented()

    def _normalize_kwargs_names(self, **kwargs):
        return kwargs

    def sel(self, *args, remapping=None, **kwargs):
        """Uses metadata values to select a subset of the elements from a fieldlist-like object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter condition as dict.
            (See below for details).
        remapping: dict
            Creates new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.
            (See below for details).

        Returns
        -------
        object
            Returns a new object with the filtered elements. It contains a view to the data in the
            original object, so no data is copied.


        Filter conditions are specified by a set of **metadata** keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single value::

            ds.sel(param="t")

        - list of values::

            ds.sel(param=["u", "v"])

        - **slice** of values (defines a **closed interval**, so treated as inclusive of both the start
        and stop values, unlike normal Python indexing)::

            # filter levels between 300 and 500 inclusively
            ds.sel(level=slice(300, 500))

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> len(ds)
        18

        Selecting by a single key ("param"):

        >>> subset = ds.sel(param="t")
        >>> for f in subset:
        ...     print(f)
        ...
        GribField(t,1000,20180801,1200,0,0)
        GribField(t,850,20180801,1200,0,0)
        GribField(t,700,20180801,1200,0,0)
        GribField(t,500,20180801,1200,0,0)
        GribField(t,400,20180801,1200,0,0)
        GribField(t,300,20180801,1200,0,0)


        Selecting by multiple keys ("param", "level") with a list and slice of values:

        >>> subset = ds.sel(param=["u", "v"], level=slice(400, 700))
        >>> for f in subset:
        ...     print(f)
        ...
        GribField(u,700,20180801,1200,0,0)
        GribField(v,700,20180801,1200,0,0)
        GribField(u,500,20180801,1200,0,0)
        GribField(v,500,20180801,1200,0,0)
        GribField(u,400,20180801,1200,0,0)
        GribField(v,400,20180801, 1200,0,0)

        Using ``remapping`` to specify the selection by a key created from two other keys
        (we created key "param_level" from "param" and "levelist"):

        >>> for f in ds.order_by(
        ...     param_level=["t850", "u1000"],
        ...     remapping={"param_level": "{param}{levelist}"},
        ... ):
        ...     print(f)
        GribField(t,850,20180801,1200,0,0)
        GribField(u,1000,20180801,1200,0,0)
        """
        kwargs = normalize_selection(*args, **kwargs)
        kwargs = self._normalize_kwargs_names(**kwargs)
        if not kwargs:
            return self

        selection = Selection(kwargs, remapping=remapping)
        if selection.is_empty:
            return self

        indices = (
            i for i, element in enumerate(self) if selection.match_element(element)
        )

        return self.new_mask_index(self, indices)

    def isel(self, *args, **kwargs):
        """Uses metadata value indices to select a subset of the elements from a
        fieldlist-like object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter conditions.
            (See below for details).
        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the filtering on.
            (See below for details).

        Returns
        -------
        object
            Returns a new object with the filtered elements. It contains a view to the data in
            the original object, so no data is copied.


        :obj:`isel` works similarly to :obj:`sel` but conditions are specified by indices of metadata
        keys. A metadata index stores the unique, **sorted** values of the corresponding metadata key
        from all the fields in the input data. If the object is a
        obj:`FieldList <data.readers.grib.index.FieldList>`
        to list the indices that have more than one values use
        :meth:`FieldList.indices() <data.readers.grib.index.FieldList.indices>`, or to find
        out the values of a specific index use :meth:`FieldList.index()
        <data.readers.grib.index.FieldList.index>`.

        Filter conditions are specified by a set of **metadata** keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single index::

            ds.sel(param=1)

        - list of indices::

            ds.sel(param=[1, 3])

        - **slice** of values (behaves like normal Python indexing, stop value not included)::

            # filter levels on level indices 1 and 2
            ds.sel(level=slice(1,3))

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")

        >>> len(ds)
        18
        >>> ds.indices
        {'levelist': (1000, 850, 700, 500, 400, 300), 'param': ('t', 'u', 'v')}

        >>> subset = ds.isel(param=0)
        >>> len(ds)
        6

        >>> for f in subset:
        ...     print(f)
        ...
        GribField(t,1000,20180801,1200,0,0)
        GribField(t,850,20180801,1200,0,0)
        GribField(t,700,20180801,1200,0,0)
        GribField(t,500,20180801,1200,0,0)
        GribField(t,400,20180801,1200,0,0)
        GribField(t,300,20180801,1200,0,0)

        >>> subset = ds.isel(param=[1, 2], level=slice(2, 4))
        >>> len(subset)
        4

        >>> for f in subset:
        ...     print(f)
        ...
        GribField(u,700,20180801,1200,0,0)
        GribField(v,700,20180801,1200,0,0)
        GribField(u,500,20180801,1200,0,0)
        GribField(v,500,20180801,1200,0,0)

        """
        kwargs = normalize_selection(*args, **kwargs)
        kwargs = self._normalize_kwargs_names(**kwargs)
        if not kwargs:
            return self

        kwargs = selection_from_index(self.index, kwargs)

        if not kwargs:
            return self.new_mask_index(self, [])

        return self.sel(**kwargs)

    def order_by(self, *args, remapping=None, **kwargs):
        """Changes the order of the elements in a fieldlist-like object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on.
            (See below for details)
        remapping: dict
            Defines new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on.
            (See below for details)

        Returns
        -------
        object
            Returns a new object with reordered elements. It contains a view to the data in the
            original object, so no data is copied.


        Ordering by a single metadata key ("param"). The default ordering direction
        is ``ascending``:

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> for f in ds.order_by("param"):
        ...     print(f)
        ...
        GribField(t,850,20180801,1200,0,0)
        GribField(t,1000,20180801,1200,0,0)
        GribField(u,850,20180801,1200,0,0)s
        GribField(u,1000,20180801,1200,0,0)
        GribField(v,850,20180801,1200,0,0)
        GribField(v,1000,20180801,1200,0,0)

        Ordering by multiple keys (first by "level" then by "param"):

        >>> for f in ds.order_by(["level", "param"]):
        ...     print(f)
        ...
        GribField(t,850,20180801,1200,0,0)
        GribField(u,850,20180801,1200,0,0)
        GribField(v,850,20180801,1200,0,0)
        GribField(t,1000,20180801,1200,0,0)
        GribField(u,1000,20180801,1200,0,0)
        GribField(v,1000,20180801,1200,0,0)

        Specifying the ordering direction:

        >>> for f in ds.order_by(param="ascending", level="descending"):
        ...     print(f)
        ...
        GribField(t,1000,20180801,1200,0,0)
        GribField(t,850,20180801,1200,0,0)
        GribField(u,1000,20180801,1200,0,0)
        GribField(u,850,20180801,1200,0,0)
        GribField(v,1000,20180801,1200,0,0)
        GribField(v,850,20180801,1200,0,0)

        Using the list of all the values of a key ("param") to define the order:

        >>> for f in ds.order_by(param=["u", "t", "v"]):
        ...     print(f)
        ...
        GribField(u,1000,20180801,1200,0,0)
        GribField(u,850,20180801,1200,0,0)
        GribField(t,1000,20180801,1200,0,0)
        GribField(t,850,20180801,1200,0,0)
        GribField(v,1000,20180801,1200,0,0)
        GribField(v,850,20180801,1200,0,0)

        Using ``remapping`` to specify the order by a key created from two other keys
        (we created key "param_level" from "param" and "levelist"):

        >>> ordering = ["t850", "t1000", "u1000", "v850", "v1000", "u850"]
        >>> for f in ds.order_by(
        ...     param_level=ordering, remapping={"param_level": "{param}{levelist}"}
        ... ):
        ...     print(f)
        GribField(t,850,20180801,1200,0,0)
        GribField(t,1000,20180801,1200,0,0)
        GribField(u,1000,20180801,1200,0,0)
        GribField(v,850,20180801,1200,0,0)
        GribField(v,1000,20180801,1200,0,0)
        GribField(u,850,20180801,1200,0,0)
        """
        kwargs = normalize_order_by(*args, **kwargs)
        kwargs = self._normalize_kwargs_names(**kwargs)

        remapping = build_remapping(remapping)

        if not kwargs:
            return self

        order = Order(kwargs, remapping=remapping)
        # order = Order(*args, **kwargs)
        if order.is_empty:
            return self

        def cmp(i, j):
            return order.compare_elements(self[i], self[j])

        indices = list(range(len(self)))
        indices = sorted(indices, key=functools.cmp_to_key(cmp))
        return self.new_mask_index(self, indices)

    def __getitem__(self, n):
        if isinstance(n, slice):
            return self.from_slice(n)
        if isinstance(n, (tuple, list, np.ndarray)):
            return self.from_multi(n)
        if isinstance(n, dict):
            return self.from_dict(n)
        return self._getitem(n)

    def from_slice(self, s):
        indices = range(len(self))[s]
        return self.new_mask_index(self, indices)

    def from_mask(self, lst):
        indices = [i for i, x in enumerate(lst) if x]
        return self.new_mask_index(self, indices)

    def from_multi(self, a):
        # will raise IndexError if an index is out of bounds
        n = len(self)
        indices = np.arange(0, n if n > 0 else 0)
        indices = indices[a].tolist()
        return self.new_mask_index(self, indices)

    def from_dict(self, dic):
        return self.sel(dic)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, Index) for _ in sources)
        return MultiIndex(sources)

    def to_numpy(self, *args, **kwargs):
        import numpy as np

        return np.array([f.to_numpy(*args, **kwargs) for f in self])

    def full(self, *coords):
        return FullIndex(self, *coords)


class MaskIndex(Index):
    def __init__(self, index, indices):
        self._index = index
        self._indices = list(indices)
        # super().__init__(
        #     *self.index._init_args,
        #     order_by=self.index._init_order_by,
        #     **self.index._init_kwargs,
        # )

    def _getitem(self, n):
        n = self._indices[n]
        return self._index[n]

    def __len__(self):
        return len(self._indices)

    def __repr__(self):
        return "MaskIndex(%r,%s)" % (self._index, self._indices)


class MultiIndex(Index):
    def __init__(self, indexes, *args, **kwargs):
        self._indexes = list(indexes)
        super().__init__(*args, **kwargs)
        # self.indexes = list(i for i in indexes if len(i))
        # TODO: propagate  index._init_args, index._init_order_by, index._init_kwargs, for each i in indexes?

    def sel(self, *args, **kwargs):
        if not args and not kwargs:
            return self
        return self.__class__(i.sel(*args, **kwargs) for i in self._indexes)

    def _getitem(self, n):
        k = 0
        while n >= len(self._indexes[k]):
            n -= len(self._indexes[k])
            k += 1
        return self._indexes[k][n]

    def __len__(self):
        return sum(len(i) for i in self._indexes)

    def graph(self, depth=0):
        print(" " * depth, self.__class__.__name__)
        for s in self._indexes:
            s.graph(depth + 3)

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ",".join(repr(i) for i in self._indexes),
        )


class ForwardingIndex(Index):
    def __init__(self, index):
        self._index = index

    def __len__(self):
        return len(self._index)


class ScaledField:
    def __init__(self, field, offset, scaling):
        self.field = field
        self.offset = offset
        self.scaling = scaling

    def to_numpy(self, **kwargs):
        return (self.field.to_numpy(**kwargs) - self.offset) * self.scaling


class ScaledIndex(ForwardingIndex):
    def __init__(self, index, offset, scaling):
        super().__init__(index)
        self.offset = offset
        self.scaling = scaling

    def __getitem__(self, n):
        return ScaledField(self.index[n], self.offset, self.scaling)


class FullIndex(Index):
    def __init__(self, index, *coords):
        import numpy as np

        self._index = index

        # Pass1, unique values
        unique = index.unique_values(*coords)
        shape = tuple(len(v) for v in unique.values())

        name_to_index = defaultdict(dict)

        for k, v in unique.items():
            for i, e in enumerate(v):
                name_to_index[k][e] = i

        self.size = math.prod(shape)
        self.shape = shape
        self.holes = np.full(shape, False)

        for f in index:
            idx = tuple(name_to_index[k][f.metadata(k, default=None)] for k in coords)
            self.holes[idx] = True

        self.holes = self.holes.flatten()
        print("+++++++++", self.holes.shape, coords, self.shape)

    def __len__(self):
        return self.size

    def _getitem(self, n):
        assert self.holes[n], f"Attempting to access hole {n}"
        return self._index[sum(self.holes[:n])]
