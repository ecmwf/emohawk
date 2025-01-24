#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import sys

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import ARRAY_BACKENDS
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import check_array_type
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.testing import get_array_namespace
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from array_fl_fixtures import load_array_fl  # noqa: E402

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_write_to_path(array_backend, write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    ds = ds.to_fieldlist(array_backend=array_backend)

    ns = get_array_namespace(array_backend)

    assert ds[0].metadata("shortName") == "2t"
    assert len(ds) == 2
    v1 = ds[0].values + 1
    check_array_type(v1, array_backend)

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_array(v1, md1)

    with temp_file() as tmp:
        write_to_file(write_method, tmp, r)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        r_tmp = r_tmp.to_fieldlist(array_backend=array_backend)
        v_tmp = r_tmp[0].values
        assert ns.allclose(v1, v_tmp)


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("_kwargs", [{}, {"check_nans": True}])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_write_missing(array_backend, _kwargs, write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    ds = ds.to_fieldlist(array_backend=array_backend)
    ns = get_array_namespace(array_backend)

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    assert not ns.isnan(v1[0])
    assert not ns.isnan(v1[1])
    v1[0] = ns.nan
    assert ns.isnan(v1[0])
    assert not ns.isnan(v1[1])

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_array(v1, md1)

    assert ns.isnan(r[0].values[0])
    assert not ns.isnan(r[0].values[1])

    with temp_file() as tmp:
        write_to_file(write_method, tmp, r, **_kwargs)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        v_tmp = r_tmp[0].values
        assert np.isnan(v_tmp[0])
        r_tmp = r_tmp.to_fieldlist(array_backend=array_backend)
        v_tmp = r_tmp[0].values
        assert ns.isnan(v_tmp[0])
        assert not ns.isnan(v_tmp[1])


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_write_check_nans_bad(write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    assert not np.isnan(v1[0])
    assert not np.isnan(v1[1])
    v1[0] = np.nan
    assert np.isnan(v1[0])
    assert not np.isnan(v1[1])

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_numpy(v1, md1)

    assert np.isnan(r[0].values[0])
    assert not np.isnan(r[0].values[1])

    with temp_file() as tmp:
        from eccodes import EncodingError

        with pytest.raises(EncodingError):
            write_to_file(write_method, tmp, r, check_nans=False)


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_write_append(write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    v2 = v + 2

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    md2 = md.override(shortName="2d")

    r1 = FieldList.from_numpy(v1, md1)
    r2 = FieldList.from_numpy(v2, md2)

    # save to disk
    tmp = temp_file()
    write_to_file(write_method, tmp.path, r1)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 1
    assert r_tmp.metadata("shortName") == ["msl"]
    r_tmp = None

    # append
    write_to_file(write_method, tmp.path, r2, append=True)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert r_tmp.metadata("shortName") == ["msl", "2d"]


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_write_generating_proc_id(write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds[0].values
    v1 = v + 1
    v2 = v + 2

    md = ds[0].metadata()
    md1 = md.override(shortName="msl", generatingProcessIdentifier=255)
    md2 = md.override(shortName="2d")

    r1 = FieldList.from_numpy([v1, v2], [md1, md2])

    # save to disk
    with temp_file() as tmp:
        write_to_file(write_method, tmp, r1)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(r_tmp) == 2
        assert r_tmp.metadata("shortName") == ["msl", "2d"]
        assert r_tmp.metadata("generatingProcessIdentifier") == [
            255,
            150,
        ]

        assert np.allclose(r_tmp.values[0], v1)
        assert np.allclose(r_tmp.values[1], v2)


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, None), ({"bits_per_value": 12}, 12), ({"bits_per_value": None}, None)],
)
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_array_fl_grib_write_bits_per_value(array_backend, _kwargs, expected_value, write_method):
    ds, _ = load_array_fl(1, array_backend)

    if expected_value is None:
        expected_value = ds[0].metadata("bitsPerValue")

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.metadata("bitsPerValue") == [expected_value] * len(ds)


@pytest.mark.parametrize(
    "filename,shape",
    [
        (earthkit_examples_file("test.grib"), (11, 19)),
        (earthkit_test_data_file("O32_global.grib1"), (5248,)),
        (earthkit_test_data_file("O32_global.grib2"), (5248,)),
    ],
)
def test_array_fl_grib_single_write_to_path(filename, shape):
    ds = from_source("file", filename)

    assert len(ds) >= 1
    v1 = ds[0].values + 1

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_array(v1, md1)
    assert r[0].shape == shape

    with temp_file() as tmp:
        r.save(tmp)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        # r_tmp = r_tmp.to_fieldlist(array_backend=array_backend)
        assert r_tmp[0].shape == shape
        assert r_tmp[0].metadata("shortName") == "msl"
        v_tmp = r_tmp[0].values
        assert np.allclose(v1, v_tmp)


@pytest.mark.parametrize(
    "filename,shape",
    [
        (earthkit_examples_file("test.grib"), (11, 19)),
        (earthkit_test_data_file("O32_global.grib1"), (5248,)),
        (earthkit_test_data_file("O32_global.grib2"), (5248,)),
    ],
)
@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, None), ({"bits_per_value": 8}, 8), ({"bits_per_value": None}, None)],
)
def test_array_fl_grib_single_write_bits_per_value(filename, shape, _kwargs, expected_value):
    ds0 = from_source("file", filename)

    ds = ds0.from_fields([ds0[0].copy()])
    assert ds[0].shape == shape

    if expected_value is None:
        expected_value = ds[0].metadata("bitsPerValue")

    with temp_file() as tmp:
        ds.save(tmp, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.metadata("bitsPerValue") == [expected_value] * len(ds)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
