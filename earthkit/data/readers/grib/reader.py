# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.readers import Reader
from earthkit.data.readers.grib.index import GribMultiFieldList
from earthkit.data.readers.grib.index.file import GribFieldListInOneFile

LOG = logging.getLogger(__name__)


class GRIBReader(GribFieldListInOneFile, Reader):
    appendable = True  # GRIB messages can be added to the same file

    def __init__(self, source, path, parts=None):
        Reader.__init__(self, source, path)
        GribFieldListInOneFile.__init__(self, path, parts=parts)

    def __repr__(self):
        return "GRIBReader(%s)" % (self.path,)

    @classmethod
    def merge(cls, readers):
        assert all(isinstance(s, GRIBReader) for s in readers), readers
        assert len(readers) > 1

        return GribMultiFieldList(readers)

    def mutate_source(self):
        # A GRIBReader is a source itself
        return self
