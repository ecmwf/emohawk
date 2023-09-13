# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import logging

LOG = logging.getLogger(__name__)


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = b"GRIB"
        if not deeper_check:
            return len(magic) >= 4 and magic[:4] == type_id
        else:
            return type_id in magic
    return False


def reader(source, path, magic=None, deeper_check=False):
    if _match_magic(magic, deeper_check):
        from .reader import GRIBReader

        return GRIBReader(source, path)


def memory_reader(source, buf, magic=None, deeper_check=False):
    if _match_magic(magic, deeper_check):
        from .memory import GribFieldListInMemory, GribMessageMemoryReader

        return GribFieldListInMemory(source, GribMessageMemoryReader(buf))


def stream_reader(source, stream, magic=None, deeper_check=False):
    # by default we assume the stream is grib data
    if magic is None or _match_magic(magic, deeper_check):
        from .memory import GribFieldListInMemory, GribStreamReader

        r = GribStreamReader(stream)
        if source.batch_size == 0:
            r = GribFieldListInMemory(source, r)
        return r
