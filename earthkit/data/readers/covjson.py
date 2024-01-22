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


class CovjsonReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def mutate_source(self):
        # A Covjson is a source itself
        return self

    def to_xarray(self, **kwargs):
        try:
            from eccovjson.api import Eccovjson
        except Exception:
            raise ModuleNotFoundError(
                "this feature requires 'eccovjson' to be installed!"
            )

        import json

        with open(self.path, "r") as f:
            d = json.load(f)
            decoder = Eccovjson().decode(d)
            return decoder.to_xarray()


def reader(
    source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs
):
    if content_type is not None and content_type == "application/prs.coverage+json":
        return CovjsonReader(source, path)

    extension = pathlib.Path(path).suffix
    if extension in [".covjson"]:
        return CovjsonReader(source, path)

    kind, compression = mimetypes.guess_type(path)
    if kind in ["application/prs.cov+json"]:
        return CovjsonReader(source, path)
