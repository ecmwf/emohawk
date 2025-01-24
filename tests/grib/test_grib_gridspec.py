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

from earthkit.data import FieldList
from earthkit.data import from_source
from earthkit.data.core.gridspec import GridSpec
from earthkit.data.core.temporary import temp_file
from earthkit.data.readers.grib.gridspec import GridSpecConverter
from earthkit.data.readers.grib.gridspec import make_gridspec
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.testing import write_to_file

SUPPORTED_GRID_TYPES = [
    "sh",
    "regular_ll",
    "reduced_ll",
    "regular_gg",
    "reduced_gg",
    "healpix",
]
UNSUPPORTED_GRID_TYPES = ["rotated_ll", "rotated_gg", "reduced_rotated_gg"]


def _make_gridspec_list(grid_types):
    d = []
    if isinstance(grid_types, str):
        grid_types = [grid_types]

    for gr in grid_types:
        with open(earthkit_test_data_file(os.path.join("gridspec", f"{gr}.yaml")), "r") as f:
            r = yaml.safe_load(f)
            for t in r:
                assert "file" in t, f"Missing 'file' key in {t}"
                assert "gridspec" in t, f"Missing 'gridspec' key in {t}"
                assert "metadata" in t, f"Missing 'metadata' key in {t}"
            d.extend(r)

    # print(d)
    return d


def gridspec_list(grid_types):
    if isinstance(grid_types, str):
        grid_types = [grid_types]

    for item in _make_gridspec_list(grid_types):
        yield (item["metadata"], item["gridspec"], item["file"])


# def gridspec_list_invalid(grid_types=None):
#     if grid_types is not None:
#         if isinstance(grid_types, str):
#             grid_types = [grid_types]
#     else:
#         grid_types = ["rotated_ll", "rotated_gg", "reduced_rotated_gg"]

#     for item in gridspec_list(grid_types):
#         yield (item["metadata"], item["gridspec"], item["file"])


@pytest.mark.parametrize(
    "metadata,ref,name",
    gridspec_list(SUPPORTED_GRID_TYPES),
)
def test_grib_gridspec_from_metadata_valid(metadata, ref, name):
    if name in [
        "regular_ll/wrf_swh_aegean_ll_jscanpos.grib1",
        "regular_ll/wind_uk_ll_jscanpos_jcons.grib1",
        # "regular_ll/t_global_0_360_5x5.grib1",
    ]:
        pytest.skip()

    gridspec = make_gridspec(metadata)
    assert dict(gridspec) == ref, name


@pytest.mark.parametrize(
    "metadata,ref,name",
    gridspec_list(UNSUPPORTED_GRID_TYPES),
)
def test_grib_gridspec_from_metadata_invalid_1(metadata, ref, name):
    with pytest.raises(ValueError):
        make_gridspec(metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {"gridType": "lambert"},
        {"gridType": "lambert_azimuthal_equal_area"},
        {"gridType": "mercator"},
        {"gridType": "polar_stereographic"},
    ],
)
def test_grib_gridspec_from_metadata_invalid_2(metadata):
    with pytest.raises(ValueError):
        make_gridspec(metadata)


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


@pytest.mark.parametrize("metadata,gridspec,name", gridspec_list("regular_ll"))
def test_grib_metadata_from_gridspec_valid(metadata, gridspec, name):
    if name in [
        "regular_ll/wrf_swh_aegean_ll_jscanpos.grib1",
        "regular_ll/wind_uk_ll_jscanpos_jcons.grib1",
        # "regular_ll/t_global_0_360_5x5.grib1",
    ]:
        pytest.skip()

    edition = int(name[-1])
    assert edition in [1, 2]
    md, _ = GridSpecConverter.to_metadata(gridspec, edition=edition)
    assert md == metadata, name


@pytest.mark.parametrize(
    "metadata,gridspec,name",
    gridspec_list(
        [
            "sh",
            "reduced_ll",
            "regular_gg",
            "reduced_gg",
            "healpix",
        ]
    ),
)
def test_grib_metadata_from_gridspec_invalid(metadata, gridspec, name):
    if name in [
        "regular_ll/wrf_swh_aegean_ll_jscanpos.grib1",
        "regular_ll/wind_uk_ll_jscanpos_jcons.grib1",
        # "regular_ll/t_global_0_360_5x5.grib1",
    ]:
        pytest.skip()

    edition = int(name[-1])
    assert edition in [1, 2]
    with pytest.raises(ValueError):
        _, _ = GridSpecConverter.to_metadata(gridspec, edition=edition)


@pytest.mark.parametrize(
    "input_file",
    [
        "test-data/grids/reduced_gg/O32_global.grib1",
        "test-data/grids/reduced_gg/O32_global.grib2",
        "test-data/grids/healpix/H4_ring.grib2",
        "test-data/grids/healpix/H4_nested.grib2",
    ],
)
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_gridspec_to_fieldlist(input_file, write_method):
    import numpy as np

    def make_lat_lon(dx):
        lat_v = np.linspace(90, -90, int(180 / dx) + 1)
        lon_v = np.linspace(0, 360 - dx, int(360 / dx))
        lon, lat = np.meshgrid(lon_v, lat_v)
        return lat, lon

    ds_in = from_source(
        "url",
        earthkit_remote_test_data_file(input_file),
    )

    # target grid: 5x5
    gs = {"grid": [5, 5]}
    v = np.random.rand(37, 72)
    md = ds_in[0].metadata().override(gridspec=gs)
    ds = FieldList.from_numpy(v.flatten(), md)

    assert len(ds) == 1

    # make references
    ref = dict(
        Ni=72,
        Nj=37,
        Nx=72,
        Ny=37,
        gridType="regular_ll",
        iDirectionIncrementInDegrees=5.0,
        iScansNegatively=0,
        jDirectionIncrementInDegrees=5.0,
        jPointsAreConsecutive=0,
        jScansPositively=0,
        latitudeOfFirstGridPointInDegrees=90.0,
        latitudeOfLastGridPointInDegrees=-90.0,
        longitudeOfFirstGridPointInDegrees=0.0,
        longitudeOfLastGridPointInDegrees=355.0,
    )

    lat_ref, lon_ref = make_lat_lon(5)

    # check latlon
    latlon = ds[0].to_latlon()
    lat = latlon["lat"]
    lon = latlon["lon"]
    assert np.allclose(lat.flatten(), lat_ref.flatten())
    assert np.allclose(lon.flatten(), lon_ref.flatten())

    # check metadata
    res = {k: ds[0].metadata(k) for k in ref.keys()}
    assert res == ref

    # save
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)

        # values
        v_tmp = r_tmp[0].values
        assert np.allclose(v_tmp, v.flatten(), atol=1e-3)

        # latlon
        latlon = r_tmp[0].to_latlon()
        lat = latlon["lat"]
        lon = latlon["lon"]
        assert np.allclose(lat.flatten(), lat_ref.flatten())
        assert np.allclose(lon.flatten(), lon_ref.flatten())

        v_tmp = r_tmp[0].values
        assert np.allclose(v_tmp, v.flatten(), atol=1e-3)
        res = {k: r_tmp[0].metadata(k) for k in ref.keys()}
        assert res == ref


def _global_grids():
    import json

    from earthkit.data.utils.paths import earthkit_conf_file

    with open(earthkit_conf_file("global_grids.json"), "r") as f:
        d = json.load(f)

    for _, v in d.items():
        yield v


# these are all the cases for the earthkit-regrid target grids
@pytest.mark.parametrize("edition", [1, 2])
@pytest.mark.parametrize("grid", _global_grids())
def test_grib_global_ll_gridspec_to_metadata(edition, grid):
    gs = {"grid": grid["grid"]}
    md, num = GridSpecConverter.to_metadata(gs, edition=edition)

    ref = dict(
        Ni=grid["shape"][1],
        Nj=grid["shape"][0],
        Nx=grid["shape"][1],
        Ny=grid["shape"][0],
        gridType="regular_ll",
        iDirectionIncrementInDegrees=grid["grid"][0],
        iScansNegatively=0,
        jDirectionIncrementInDegrees=grid["grid"][1],
        jPointsAreConsecutive=0,
        jScansPositively=0,
        latitudeOfFirstGridPointInDegrees=grid["area"][0],
        latitudeOfLastGridPointInDegrees=grid["area"][2],
        longitudeOfFirstGridPointInDegrees=grid["area"][1],
        longitudeOfLastGridPointInDegrees=grid["area"][3],
    )
    assert ref == md
    assert grid["shape"][0] * grid["shape"][1] == num


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
