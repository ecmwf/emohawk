# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import weakref
from importlib import import_module

from earthkit.data.core import Base
from earthkit.data.core.settings import SETTINGS
from earthkit.data.decorators import locked

LOG = logging.getLogger(__name__)


class ReaderMeta(type(Base), type(os.PathLike)):
    pass


class Reader(Base, os.PathLike, metaclass=ReaderMeta):
    appendable = False  # Set to True if the data can be appended to and existing file
    binary = True

    def __init__(self, source, path):
        LOG.debug("Reader for %s is %s", path, self.__class__.__name__)

        self._source = weakref.ref(source)
        self.path = path

    @property
    def source(self):
        return self._source()

    @property
    def filter(self):
        return self.source.filter

    @property
    def merger(self):
        return self.source.merger

    def mutate(self):
        # Give a chance to `directory` or `zip` to change the reader
        return self

    def mutate_source(self):
        # The source may ask if it needs to mutate
        return None

    def ignore(self):
        # Used by multi-source
        return False

    def cache_file(self, *args, **kwargs):
        return self.source.cache_file(*args, **kwargs)

    def save(self, path, **kwargs):
        mode = "wb" if self.binary else "w"
        with open(path, mode) as f:
            self.write(f, **kwargs)

    def write(self, f, **kwargs):
        if not self.appendable:
            assert f.tell() == 0
        mode = "rb" if self.binary else "r"
        with open(self.path, mode) as g:
            while True:
                chunk = g.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    def __fspath__(self):
        return self.path

    def index_content(self):
        LOG.warning(f"index-content(): Ignoring {self.path}")
        return []

    def ranges(self):
        self.source._kw


_READERS = {}


# TODO: Add plugins
@locked
def _readers(method_name):
    if not _READERS:
        here = os.path.dirname(__file__)
        for path in sorted(os.listdir(here)):
            if path[0] in ("_", "."):
                continue

            if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
                name, _ = os.path.splitext(path)
                try:
                    for method in ["reader", "memory_reader", "stream_reader"]:
                        module = import_module(f".{name}", package=__name__)
                        if hasattr(module, method):
                            _READERS[(name, method)] = getattr(module, method)
                            if hasattr(module, "aliases"):
                                for a in module.aliases:
                                    assert a not in _READERS
                                    _READERS[(a, method_name)] = getattr(module, method)
                except Exception:
                    LOG.exception("Error loading reader %s", name)

    return {k[0]: v for k, v in _READERS.items() if k[1] == method_name}


def _find_reader(method_name, source, path_or_data, **kwargs):
    """Helper function to create a reader.

    Tries all the registered methods stored in _READERS.
    """
    for deeper_check in (False, True):
        # We do two passes, the second one
        # allow the plugin to look deeper in the buffer
        for name, r in _readers(method_name).items():
            reader = r(source, path_or_data, deeper_check=deeper_check, **kwargs)
            if reader is not None:
                return reader.mutate()

    return _unknown(method_name, source, path_or_data, **kwargs)


def _unknown(method_name, source, path_or_data, **kwargs):
    from .unknown import UnknownMemoryReader, UnknownReader, UnknownStreamReader

    unknowns = {
        "reader": UnknownReader,
        "stream_reader": UnknownStreamReader,
        "memory_reader": UnknownMemoryReader,
    }
    return unknowns[method_name](source, path_or_data, **kwargs)


def reader(source, path, **kwargs):
    """Create the reader for a file/directory specified by path"""
    assert isinstance(path, str), source

    if hasattr(source, "reader"):
        reader = source.reader
        LOG.debug("Looking for a reader for %s (%s)", path, reader)
        if callable(reader):
            return reader(source, path)
        if isinstance(reader, str):
            return _readers()[reader.replace("-", "_")](
                source, path, magic=None, deeper_check=False
            )

        raise TypeError(
            "Provided reader must be a callable or a string, not %s" % type(reader)
        )

    if os.path.isdir(path):
        from .directory import DirectoryReader

        return DirectoryReader(source, path).mutate()
    LOG.debug("Reader for %s", path)

    n_bytes = SETTINGS.get("reader-type-check-bytes")
    with open(path, "rb") as f:
        magic = f.read(n_bytes)

    LOG.debug("Looking for a reader for %s (%s)", path, magic)

    return _find_reader(
        "reader",
        source,
        path,
        magic=magic,
        **kwargs,
    )


def memory_reader(source, buffer):
    """Create a reader for data held in a memory buffer"""
    assert isinstance(buffer, (bytes, bytearray)), source
    n_bytes = SETTINGS.get("reader-type-check-bytes")
    magic = buffer[: min(n_bytes, len(buffer) - 1)]

    return _find_reader("memory_reader", source, buffer, magic=magic)


def stream_reader(source, stream, memory, content_type=None):
    """Create a reader for a stream"""
    magic = None
    if hasattr(stream, "peek") and callable(stream.peek):
        try:
            n_bytes = SETTINGS.get("reader-type-check-bytes")
            magic = stream.peek(n_bytes)
            if len(magic) > n_bytes:
                magic = magic[:n_bytes]
        except Exception:
            pass

    return _find_reader(
        "stream_reader",
        source,
        stream,
        magic=magic,
        memory=memory,
        content_type=content_type,
    )
