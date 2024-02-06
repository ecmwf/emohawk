#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np

import earthkit.data


def test_netcdf_fieldlist_string_coord():
    import xarray as xr

    a = xr.DataArray(
        [
            [[11, 12, 13], [21, 22, 23], [31, 32, 33]],
            [[14, 15, 16], [24, 25, 26], [34, 35, 36]],
        ],
        coords={"level": ["500", "700"], "x": [1, 2, 3], "y": [4, 5, 6]},
        name="dummyvar",
    )

    ds = earthkit.data.from_object(a)

    assert ds
    assert len(ds) == 2
    assert ds.metadata("level") == ["500", "700"]

    x_ref = np.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
    y_ref = np.array([[4, 4, 4], [5, 5, 5], [6, 6, 6]])
    assert np.allclose(ds[0].to_points()["x"], x_ref)
    assert np.allclose(ds[0].to_points()["y"], y_ref)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
