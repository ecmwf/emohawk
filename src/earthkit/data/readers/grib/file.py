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
from earthkit.data.readers.grib.index.file import GribFieldListInOneFile

LOG = logging.getLogger(__name__)


class GRIBReader(GribFieldListInOneFile, Reader):
    appendable = True  # GRIB messages can be added to the same file

    def __init__(self, source, path, parts=None):
        array_backend = source._kwargs.get("array_backend", None)
        store_grib_fields_in_memory = source._kwargs.get("store_grib_fields_in_memory", None)
        grib_handle_cache_size = source._kwargs.get("grib_handle_cache_size", None)
        use_grib_metadata_cache = source._kwargs.get("use_grib_metadata_cache", None)

        Reader.__init__(self, source, path)
        GribFieldListInOneFile.__init__(
            self,
            path,
            parts=parts,
            array_backend=array_backend,
            store_grib_fields_in_memory=store_grib_fields_in_memory,
            grib_handle_cache_size=grib_handle_cache_size,
            use_grib_metadata_cache=use_grib_metadata_cache,
        )

    def __repr__(self):
        return "GRIBReader(%s)" % (self.path,)

    def mutate_source(self):
        # A GRIBReader is a source itself
        return self
