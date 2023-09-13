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
from earthkit.data.readers.grib.gridspec import GridSpecConverter, make_gridspec
from earthkit.data.testing import earthkit_test_data_file


def gridspec_list(grid_type=None):
    d = []
    grid_types = [
        "sh",
        "regular_ll",
        "reduced_ll",
        "regular_gg",
        "reduced_gg",
        "mercator",
        "polar_stereographic",
        "lambert",
        "lambert_azimuthal_equal_area",
    ]

    if grid_type is not None:
        grid_types = grid_type
        if isinstance(grid_types, str):
            grid_types = [grid_types]

    for gr in grid_types:
        with open(
            earthkit_test_data_file(os.path.join("gridspec", f"{gr}.yaml")), "r"
        ) as f:
            r = yaml.safe_load(f)
            d.extend(r)
    return d


@pytest.mark.parametrize(
    "metadata,ref,name",
    [(item["metadata"], item["gridspec"], item["file"]) for item in gridspec_list()],
)
def test_grib_gridspec_from_metadata(metadata, ref, name):
    if name in [
        "regular_ll/wrf_swh_aegean_ll_jscanpos.grib1",
        "regular_ll/wind_uk_ll_jscanpos_jcons.grib1",
    ]:
        pytest.skip()

    gridspec = make_gridspec(metadata)
    assert dict(gridspec) == ref, name


def test_grib_gridspec_from_file():
    ds = from_source(
        "file",
        earthkit_test_data_file(os.path.join("gridspec", "t_75_-60_10_40_5x5.grib1")),
    )

    ref = {
        "type": "regular_ll",
        "grid": [5.0, 5.0],
        "area": [75.0, -60.0, 10.0, 40.0],
        "j_points_consecutive": 0,
        "i_scans_negatively": 0,
        "j_scans_positively": 0,
    }
    gs = ds[0].metadata().gridspec
    assert isinstance(gs, GridSpec)
    assert dict(gs) == ref


@pytest.mark.parametrize(
    "gridspec,ref,name",
    [
        (item["gridspec"], item["metadata"], item["file"])
        for item in gridspec_list("regular_ll")
    ],
)
def test_grib_metadata_from_gridspec(gridspec, ref, name):
    if name in [
        "regular_ll/wrf_swh_aegean_ll_jscanpos.grib1",
        "regular_ll/wind_uk_ll_jscanpos_jcons.grib1",
    ]:
        pytest.skip()

    edition = int(name[-1])
    assert edition in [1, 2]
    md, _ = GridSpecConverter.to_metadata(gridspec, edition=edition)
    assert md == ref, name


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
