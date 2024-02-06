# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import Writer


class GribWriter(Writer):
    DATA_FORMAT = "grib"

    def write(self, f, values, metadata, check_nans=True, bits_per_value=16):
        r"""Write a GRIB field to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        values: ndarray
            Values of the GRIB field.
        metadata: :class:`GribMetadata`
            Metadata of the GRIB field.
        check_nans: bool
            Replace nans in ``values`` with GRIB missing values when writing to``f``.
        bits_per_value: int
            Set the ``bitsPerValue`` GRIB key in the generated GRIB message.
        """
        handle = metadata._handle.clone()

        handle.set_long("bitsPerValue", bits_per_value)

        if check_nans:
            import numpy as np

            if np.isnan(values).any():
                missing_value = handle.MISSING_VALUE
                values = np.nan_to_num(values, nan=missing_value)
                handle.set_double("missingValue", missing_value)
                handle.set_long("bitmapPresent", 1)

        handle.set_values(values)
        handle.write(f)


Writer = GribWriter
