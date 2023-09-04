#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import pytest
import yaml

from earthkit.data import from_source
from earthkit.data.core.gridspec import GridSpec
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.testing import earthkit_test_data_file


def gridspec_list():
    d = []
    for grid_type in ["regular_ll", "regular_gg", "reduced_gg"]:
        with open(
            earthkit_test_data_file(os.path.join("gridspec", f"{grid_type}.yaml")), "r"
        ) as f:
            r = yaml.safe_load(f)
            d.extend(r)
    return d


@pytest.mark.parametrize("item", gridspec_list())
def test_grib_gridspec_from_metadata(item):
    from earthkit.data.readers.grib.gridspec import make_gridspec

    md = RawMetadata(item["metadata"])
    ref = item["gridspec"]
    name = item["file"]

    gridspec = make_gridspec(md)
    assert dict(gridspec) == ref, name


def test_grib_gridspec_from_file():
    ds = from_source(
        "file",
        earthkit_test_data_file(os.path.join("gridspec", "t_-60_75_40_10_5x5.grib1")),
    )

    ref = {
        "type": "regular_ll",
        "grid": [5.0, 5.0],
        "area": [75.0, -60.0, 10.0, 40.0],
        "jPointsAreConsecutive": 0,
        "iScansNegatively": 0,
        "jScansPositively": 0,
    }
    gs = ds[0].metadata().gridspec
    assert isinstance(gs, GridSpec)
    assert dict(gs) == ref


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
