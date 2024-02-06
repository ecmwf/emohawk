# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import mimetypes
import pathlib

from earthkit.data.readers import Reader


class XarrayMixIn:
    def to_xarray(self, **kwargs):
        try:
            from eccovjson.api import Eccovjson
        except Exception:
            raise ModuleNotFoundError(
                "this feature requires 'eccovjson' to be installed!"
            )

        decoder = Eccovjson().decode(self._json())
        return decoder.to_xarray()


class CovjsonReader(XarrayMixIn, Reader):
    def __init__(self, source, path):
        super().__init__(source, path)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def mutate_source(self):
        # A Covjson is a source itself
        return self

    def _json(self):
        import json

        with open(self.path, "r") as f:
            d = json.load(f)
            return d


class CovjsonStreamReader(Reader):
    def __init__(self, stream):
        self.stream = stream

    def __next__(self):
        import json

        d = self.stream.read()
        if d:
            return CovjsonInMemory(json.loads(d))
        else:
            raise StopIteration

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def mutate_source(self):
        # A Covjson is a source itself
        return self


class CovjsonMemoryReader(Reader):
    def __init__(self, buf):
        self.buf = buf

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def mutate_source(self):
        import json

        return CovjsonInMemory(json.loads(self.buf))

    @staticmethod
    def _from_stream(stream):
        d = stream.read()
        return CovjsonMemoryReader(d)


class CovjsonInMemory(XarrayMixIn, Reader):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def mutate_source(self):
        # A Covjson is a source itself
        return self

    def _json(self):
        return self.data


def _match_content_type(content_type):
    return content_type is not None and content_type == "application/prs.coverage+json"


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = b'{"type": "CoverageCollection"'
        if not deeper_check:
            return magic.startswith(type_id)
        else:
            return type_id in magic
    return False


def reader(
    source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs
):
    def _reader():
        return CovjsonReader(source, path)

    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        return _reader()

    extension = pathlib.Path(path).suffix
    if extension in [".covjson"]:
        return _reader()

    kind, compression = mimetypes.guess_type(path)
    if kind in ["application/prs.cov+json"]:
        return _reader()


def memory_reader(
    source, buffer, *, magic=None, deeper_check=False, content_type=None, **kwargs
):
    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        return CovjsonMemoryReader(buffer)


def stream_reader(
    source,
    stream,
    *,
    magic=None,
    deeper_check=False,
    content_type=None,
    memory=False,
    **kwargs,
):
    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        if memory:
            return CovjsonMemoryReader._from_stream(stream)
        return CovjsonStreamReader(stream)
