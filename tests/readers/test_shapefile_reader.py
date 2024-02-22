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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils.bbox import BoundingBox


def test_shapefile():
    ds = from_source("file", earthkit_test_data_file("NUTS_RG_20M_2021_3035.shp.zip"))
    assert len(ds) == 2010

    # slicing
    r = ds[1]
    assert r.NUTS_ID == "HR"
    assert r.NAME_LATN == "Hrvatska"
    assert len(r.geometry.geoms) == 16

    # iteration
    cnt = 0
    for f in ds:
        assert isinstance(f.NUTS_ID, str)
        cnt += 1

    assert cnt == 2010

    # conversion
    gpf = ds.to_pandas()
    assert len(gpf) == 2010
    r = gpf.iloc[1]
    assert r.NUTS_ID == "HR"
    assert r.NAME_LATN == "Hrvatska"
    assert len(r.geometry.geoms) == 16

    gpf = ds.to_geopandas()
    assert len(gpf) == 2010
    r = gpf.iloc[1]
    assert r.NUTS_ID == "HR"
    assert r.NAME_LATN == "Hrvatska"
    assert len(r.geometry.geoms) == 16

    v = ds.to_numpy()
    assert v.shape == (2010, 10)

    v = ds.to_numpy(flatten=True)
    assert v.shape == (2010 * 10,)


def test_shapefile_bounding_box():
    ds = from_source("file", earthkit_test_data_file("NUTS_RG_20M_2021_3035.shp.zip"))

    ref = BoundingBox(north=84.73, west=44.83, south=24.6, east=324.42)
    bb = ds.bounding_box()
    assert np.allclose(np.array(bb.as_list()), np.array(ref.as_list()))


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
