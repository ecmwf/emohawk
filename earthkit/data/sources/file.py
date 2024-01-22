# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import glob
import logging
import os

from earthkit.data import from_source
from earthkit.data.core.caching import CACHE
from earthkit.data.readers import reader

from . import Source

LOG = logging.getLogger(__name__)


class FileSourceMeta(type(Source), type(os.PathLike)):
    def patch(cls, obj, *args, **kwargs):
        if "reader" in kwargs:
            setattr(obj, "reader", kwargs.pop("reader"))

        return super().patch(obj, *args, **kwargs)


class FileSource(Source, os.PathLike, metaclass=FileSourceMeta):
    _reader_ = None
    content_type = None

    def __init__(self, path=None, filter=None, merger=None, **kwargs):
        Source.__init__(self, **kwargs)
        self.path = path
        self.filter = filter
        self.merger = merger

    def mutate(self):
        if isinstance(self.path, (list, tuple)):
            if len(self.path) == 1:
                self.path = self.path[0]
            else:
                return from_source(
                    "multi",
                    [from_source("file", p, **self._kwargs) for p in self.path],
                    filter=self.filter,
                    merger=self.merger,
                )

        # here we must have a file or a directory
        if self._kwargs.get("indexing", False):
            from earthkit.data.sources.file_indexed import FileIndexedSource

            kw = dict(self._kwargs)
            kw.pop("indexing", None)
            return FileIndexedSource(self.path, filter=filter, merger=self.merger, **kw)

        # Give a chance to directories and zip files
        # to return a multi-source
        source = self._reader.mutate_source()
        if source not in (None, self):
            source._parent = self
            return source
        return self

    def ignore(self):
        return self._reader.ignore()

    @classmethod
    def merge(cls, sources):
        from earthkit.data.mergers import merge_by_class

        assert all(isinstance(s, FileSource) for s in sources)
        return merge_by_class([s._reader for s in sources])

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = reader(self, self.path, content_type=self.content_type)
        return self._reader_

    def __iter__(self):
        return iter(self._reader)

    def __len__(self):
        return len(self._reader)

    def __getitem__(self, n):
        return self._reader[n]

    def sel(self, *args, **kwargs):
        return self._reader.sel(*args, **kwargs)

    def isel(self, *args, **kwargs):
        return self._reader.isel(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        return self._reader.order_by(*args, **kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_pandas(self, **kwargs):
        LOG.debug("Calling reader.to_pandas %s", self)
        return self._reader.to_pandas(**kwargs)

    def to_numpy(self, **kwargs):
        return self._reader.to_numpy(**kwargs)

    @property
    def values(self):
        return self._reader.values

    def save(self, path, **kwargs):
        return self._reader.save(path, **kwargs)

    def write(self, f, **kwargs):
        return self._reader.write(f, **kwargs)

    def scaled(self, *args, **kwargs):
        return self._reader.scaled(*args, **kwargs)

    def _attributes(self, names):
        return self._reader._attributes(names)

    def __repr__(self):
        path = getattr(self, "path", None)
        if isinstance(path, str):
            cache_dir = CACHE.directory()
            path = path.replace(cache_dir, "CACHE:")
        try:
            reader_class_name = str(self._reader.__class__.__name__)
        except AttributeError as e:
            reader_class_name = str(e)
        except:  # noqa: E722
            reader_class_name = "Unknown"
        return f"{self.__class__.__name__}({path},{reader_class_name})"

    def __fspath__(self):
        return self.path

    def metadata(self, *args, **kwargs):
        return self._reader.metadata(*args, **kwargs)

    def indices(self, *args, **kwargs):
        return self._reader.indices(*args, **kwargs)

    def index(self, *args, **kwargs):
        return self._reader.index(*args, **kwargs)

    def head(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

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


class IndexedFileSource(FileSource):
    def mutate(self):
        pass


class File(FileSource):
    def __init__(
        self,
        path,
        expand_user=True,
        expand_vars=False,
        unix_glob=True,
        recursive_glob=True,
        filter=None,
        merger=None,
        **kwargs,
    ):
        if not isinstance(path, (list, tuple)):
            if expand_user:
                path = os.path.expanduser(path)

            if expand_vars:
                path = os.path.expandvars(path)

            if unix_glob and set(path).intersection(set("[]?*")):
                matches = glob.glob(path, recursive=recursive_glob)
                if len(matches) == 1:
                    path = matches[0]
                if len(matches) > 1:
                    path = sorted(matches)

        super().__init__(path, filter, merger, **kwargs)


source = File
