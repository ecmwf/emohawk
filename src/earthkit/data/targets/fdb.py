# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import SimpleTarget

LOG = logging.getLogger(__name__)


class FDBTarget(SimpleTarget):
    def __init__(self, fdb=None, config=None, userconfig=None, **kwargs):
        super().__init__(**kwargs)
        self._fdb = fdb
        self._fdb_kwargs = {}
        if config is not None:
            self._fdb_kwargs["config"] = config
        if userconfig is not None:
            self._fdb_kwargs["userconfig"] = userconfig

    @property
    def fdb(self):
        if self._fdb is None:
            import pyfdb

            self._fdb = pyfdb.FDB(**self._fdb_kwargs)
        return self._fdb

    def flush(self):
        self.fdb.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.flush()

    def _write(self, data, **kwargs):
        r = self._encode(data, **kwargs)
        if hasattr(r, "__iter__"):
            for d in r:
                self.fdb.archive(d.to_bytes())
        else:
            self.fdb.archive(r.to_bytes())


target = FDBTarget
