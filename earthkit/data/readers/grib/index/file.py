# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging
import os

from earthkit.data.readers.grib.codes import GribCodesMessagePositionIndex
from earthkit.data.readers.grib.index import GribFieldListInFiles
from earthkit.data.utils.parts import Part

LOG = logging.getLogger(__name__)


class GribFieldListInOneFile(GribFieldListInFiles):
    VERSION = 1

    @property
    def availability_path(self):
        return os.path.join(self.path, ".availability.pickle")

    def __init__(self, path, parts=None, **kwargs):
        assert isinstance(path, str), path

        self.path = path
        self._file_parts = parts
        self.__positions = None
        super().__init__(**kwargs)

    @property
    def _positions(self):
        if self.__positions is None:
            self.__positions = GribCodesMessagePositionIndex(
                self.path, self._file_parts
            )
        return self.__positions

    def part(self, n):
        return Part(self.path, self._positions.offsets[n], self._positions.lengths[n])

    def number_of_parts(self):
        return len(self._positions)
