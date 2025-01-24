# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import re
import weakref
from importlib import import_module

from earthkit.data.core import Base
from earthkit.data.core.caching import cache_file
from earthkit.data.core.config import CONFIG
from earthkit.data.core.plugins import find_plugin
from earthkit.data.core.plugins import register as register_plugin


class Source(Base):
    """Doc"""

    name = None
    home_page = "-"
    licence = "-"
    documentation = "-"
    citation = "-"

    _dataset = None
    _parent = None

    source_filename = None

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def config(self, name):
        return CONFIG.get(name)

    def mutate(self):
        # Give a chance to `multi` to change source
        return self

    def ignore(self):
        """Indicates to ignore this source in concatenation/merging.

        Returns
        -------
        bool
        """
        # Used by multi-source
        return False

    def __add__(self, other):
        from earthkit.data.sources import from_source

        return from_source("multi", self, other)

    def cache_file(self, create, args, **kwargs):
        owner = self.name
        if self.dataset:
            owner = self.dataset.name
        if owner is None:
            owner = re.sub(r"(?!^)([A-Z]+)", r"-\1", self.__class__.__name__).lower()

        return cache_file(owner, create, args, **kwargs)

    @property
    def dataset(self):
        if self._dataset is None:
            return None
        return self._dataset()

    @dataset.setter
    def dataset(self, dataset):
        self._set_dataset(weakref.ref(dataset))

    def _set_dataset(self, dataset):
        self._dataset = dataset

    @property
    def parent(self):
        if self._parent is None:
            return None
        return self._parent()

    @parent.setter
    def parent(self, parent):
        self._set_parent(weakref.ref(parent))

    def _set_parent(self, parent):
        self._parent = parent

    def _repr_html_(self):
        return self.__repr__()

    def graph(self, depth=0):
        print(" " * depth, self)

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def default_encoder(self):
        return None


class SourceLoader:
    kind = "source"

    def load_module(self, module):
        return import_module(module, package=__name__).source

    def load_entry(self, entry):
        entry = entry.load()
        if callable(entry):
            return entry
        return entry.source

    def load_remote(self, name):
        return None


class SourceMaker:
    SOURCES = {}

    def __call__(self, name, *args, **kwargs):
        loader = SourceLoader()

        if name in self.SOURCES:
            klass = self.SOURCES[name]
        else:
            klass = find_plugin(os.path.dirname(__file__), name, loader)
            self.SOURCES[name] = klass

        source = klass(*args, **kwargs)

        if getattr(source, "name", None) is None:
            source.name = name

        return source

    def __getattr__(self, name):
        return self(name.replace("_", "-"))


get_source = SourceMaker()


def from_source(name: str, *args, lazily=False, **kwargs) -> Source:
    if lazily:
        return from_source_lazily(name, *args, **kwargs)

    prev = None
    src = get_source(name, *args, **kwargs)
    while src is not prev:
        prev = src
        src = src.mutate()
    return src


def from_source_lazily(name, *args, **kwargs):
    from earthkit.data.utils.lazy import LazySource

    return LazySource(name, *args, **kwargs)


def register(name, proc):
    register_plugin("source", name, proc)
