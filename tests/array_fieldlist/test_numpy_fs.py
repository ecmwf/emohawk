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
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from array_fl_fixtures import check_array_fl  # noqa: E402
from array_fl_fixtures import check_array_fl_from_to_fieldlist  # noqa: E402


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_single_field(write_method):
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
    write_to_file(write_method, tmp.path, r)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    _check_field(r_tmp)


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_multi_field(write_method):
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
    write_to_file(write_method, tmp.path, r)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert np.allclose(v1, r_tmp.values)
    for i, f in enumerate(r_tmp):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"


def test_array_fl_grib_from_list_of_arrays():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md_full = ds.metadata("param")
    assert len(ds) == 2

    v = [ds[0].values, ds[1].values]
    md = [f.metadata().override(generatingProcessIdentifier=150) for f in ds]
    r = FieldList.from_numpy(v, md)

    check_array_fl(r, [ds], md_full)


def test_array_fl_grib_from_list_of_arrays_bad():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    v = ds[0].values
    md = [f.metadata().override(generatingProcessIdentifier=150) for f in ds]

    with pytest.raises(ValueError):
        _ = FieldList.from_numpy(v, md)

    with pytest.raises(ValueError):
        _ = FieldList.from_numpy([v], md)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"dtype": np.float32},
        {"flatten": False},
        {"flatten": True},
        {"flatten": True, "dtype": np.float32},
    ],
)
def test_array_fl_grib_from_to_fieldlist(kwargs):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md_full = ds.metadata("param")
    assert len(ds) == 2

    r = ds.to_fieldlist(array_backend="numpy", **kwargs)
    check_array_fl_from_to_fieldlist(r, [ds], md_full, **kwargs)


def test_array_fl_grib_from_to_fieldlist_repeat():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md_full = ds.metadata("param")
    assert len(ds) == 2

    kwargs = {}
    r = ds.to_fieldlist(array_backend="numpy", **kwargs)
    check_array_fl_from_to_fieldlist(r, [ds], md_full, **kwargs)

    kwargs = {"flatten": True, "dtype": np.float32}
    r1 = r.to_fieldlist(array_backend="numpy", **kwargs)
    assert r1 is not r
    check_array_fl_from_to_fieldlist(r1, [ds], md_full, **kwargs)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
