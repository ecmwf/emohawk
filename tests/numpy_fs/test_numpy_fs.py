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
import sys

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from numpy_fs_fixtures import check_numpy_fs  # noqa: E402


def test_numpy_fs_grib_single_field():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    lat, lon, v = ds[0].data(flatten=True)
    v1 = v + 1

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_numpy(v1, md1)

    def _check_field(r):
        assert len(r) == 1
        assert np.allclose(r[0].values, v1)
        assert r[0].shape == ds[0].shape
        assert r[0].metadata("shortName") == "msl"
        _lat, _lon, _v = r[0].data(flatten=True)
        assert np.allclose(_lat, lat)
        assert np.allclose(_lon, lon)
        assert np.allclose(_v, v1)

    _check_field(r)

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    _check_field(r_tmp)


def test_numpy_fs_grib_multi_field():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds.values
    v1 = v + 1

    md1 = [f.metadata().override(shortName="2d") for f in ds]
    r = FieldList.from_numpy(v1, md1)

    assert len(r) == 2
    assert np.allclose(v1, r.values)
    for i, f in enumerate(r):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert np.allclose(v1, r_tmp.values)
    for i, f in enumerate(r_tmp):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"


def test_numpy_fs_grib_gridspec_override():
    ds = from_source(
        "file",
        earthkit_test_data_file(os.path.join("gridspec", "t_75_-60_10_40_5x5.grib1")),
    )

    # define gridspec for new grid
    gs = {
        "type": "regular_ll",
        "grid": [10.0, 10.0],
        "area": [70.0, -50.0, 20.0, 10.0],
        "j_points_consecutive": 0,
        "i_scans_negatively": 0,
        "j_scans_positively": 0,
    }

    # reference metadata
    ref = {
        "gridType": "regular_ll",
        "Nx": 7,
        "Ni": 7,
        "Ny": 6,
        "Nj": 6,
        "iDirectionIncrementInDegrees": 10.0,
        "jDirectionIncrementInDegrees": 10.0,
        "latitudeOfFirstGridPointInDegrees": 70.0,
        "latitudeOfLastGridPointInDegrees": 20.0,
        "longitudeOfFirstGridPointInDegrees": -50.0,
        "longitudeOfLastGridPointInDegrees": 10.0,
        "jPointsAreConsecutive": 0,
        "iScansNegatively": 0,
        "jScansPositively": 0,
        "numberOfDataPoints": 42,
    }

    md_new = ds[0].metadata().override(gridspec=gs)
    for k, v in ref.items():
        assert md_new[k] == v

    v_new = np.ones(6 * 7)
    r = FieldList.from_numpy(v_new, md_new)
    assert len(r) == 1
    assert np.allclose(r[0].values, v_new)
    for k, v in ref.items():
        assert r[0].metadata(k) == v


def test_numpy_fs_grib_from_list_of_arrays():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md_full = ds.metadata("param")
    assert len(ds) == 2

    v = [ds[0].values, ds[1].values]
    md = [f.metadata().override(generatingProcessIdentifier=150) for f in ds]
    r = FieldList.from_numpy(v, md)

    check_numpy_fs(r, [ds], md_full)


def test_numpy_fs_grib_from_list_of_arrays_bad():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    v = ds[0].values
    md = [f.metadata().override(generatingProcessIdentifier=150) for f in ds]

    with pytest.raises(ValueError):
        _ = FieldList.from_numpy(v, md)

    with pytest.raises(ValueError):
        _ = FieldList.from_numpy([v], md)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
