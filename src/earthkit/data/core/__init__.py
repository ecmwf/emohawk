# (C) Copyright 2020- ECMWF.  #
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from abc import abstractmethod
from collections import defaultdict

LOG = logging.getLogger(__name__)

PRIVATE_ATTRIBUTES = {"observer": lambda: None}


class MetaBase(type):
    def __call__(cls, *args, **kwargs):
        obj = cls.__new__(cls, *args, **kwargs)
        args, kwargs = cls.patch(obj, *args, **kwargs)
        obj.__init__(*args, **kwargs)
        return obj

    def patch(cls, obj, *args, **kwargs):
        private_attributes = {}
        private_attributes.update(PRIVATE_ATTRIBUTES)
        private_attributes.update(kwargs.pop("_PRIVATE_ATTRIBUTES", {}))

        for k, v in private_attributes.items():
            setattr(obj, k, kwargs.pop(k, v))

        return args, kwargs


class Base(metaclass=MetaBase):
    # Convertors
    def to_numpy(self, **kwargs):
        """Convert into a numpy array"""
        self._not_implemented()

    @abstractmethod
    def to_xarray(self, **kwargs):
        """Convert into an xarray dataset"""
        self._not_implemented()

    @abstractmethod
    def to_pandas(self, **kwargs):
        """Convert into a pandas dataframe"""
        self._not_implemented()

    # Change class
    def mutate(self):
        return self

    @classmethod
    def merge(cls, *args, **kwargs):
        """Merge the object with other ones."""
        return None

    @abstractmethod
    def metadata(self, *args, **kwargs):
        """Return metadata."""
        self._not_implemented()

    # I/O
    @abstractmethod
    def to_target(self, *args, **kwargs):
        """Write data into the specified target."""
        self._not_implemented()

    @abstractmethod
    def datetime(self):
        """Return datetime."""
        self._not_implemented()

    @abstractmethod
    def bounding_box(self):
        """Return the bounding box."""
        self._not_implemented()

    @abstractmethod
    def sel(self, *args, **kwargs):
        """Filter the object based on metadata."""
        self._not_implemented()

    @abstractmethod
    def isel(self, *args, **kwargs):
        self._not_implemented()

    @abstractmethod
    def order_by(self, *args, **kwargs):
        """Reorder the elements of the object."""
        self._not_implemented()

    def unique_values(self, *coords, remapping=None, patches=None, progress_bar=False):
        """Given a list of metadata attributes, such as date, param, levels,
        returns the list of unique values for each attributes
        """
        from earthkit.data.core.order import build_remapping

        assert len(coords)
        assert all(isinstance(k, str) for k in coords), coords

        remapping = build_remapping(remapping, patches)
        iterable = self

        if progress_bar:
            from earthkit.data.utils.progbar import progress_bar

            if progress_bar:
                iterable = progress_bar(
                    iterable=self,
                    desc=f"Finding coords in dataset for {coords}",
                )

        vals = defaultdict(dict)
        for f in iterable:
            metadata = remapping(f.metadata)
            for k in coords:
                v = metadata(k, default=None)
                vals[k][v] = True

        vals = {k: tuple(values.keys()) for k, values in vals.items()}

        return vals

    # @abstractmethod
    # def to_points(self, *args, **kwargs):
    #     self._not_implemented()

    # @abstractmethod
    # def to_latlon(self, *args, **kwargs):
    #     self._not_implemented()

    def __add__(self, other):
        self._not_implemented()

    #
    def _not_implemented(self):
        import inspect

        func = inspect.stack()[1][3]
        module = self.__class__.__module__
        name = self.__class__.__name__

        extra = ""
        if hasattr(self, "path"):
            extra = f" on {self.path}"
        raise NotImplementedError(f"{module}.{name}.{func}(){extra}")

    def batched(self, *args):
        """Return iterator for batches of data"""
        self._not_implemented()

    def group_by(self, *args):
        """Return iterator for batches of data grouped by metadata keys"""
        self._not_implemented()
