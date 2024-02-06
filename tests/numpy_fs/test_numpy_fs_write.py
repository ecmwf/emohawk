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
from earthkit.data.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from numpy_fs_fixtures import load_numpy_fs  # noqa: E402

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize("_kwargs", [{}, {"check_nans": True}])
def test_numpy_fs_grib_write_missing(_kwargs):
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
        r.save(tmp, **_kwargs)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        v_tmp = r_tmp[0].values
        assert np.isnan(v_tmp[0])
        assert not np.isnan(v_tmp[1])


def test_numpy_fs_grib_write_check_nans_bad():
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
            r.save(tmp, check_nans=False)


def test_numpy_fs_grib_write_append():
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
    r1.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 1
    assert r_tmp.metadata("shortName") == ["msl"]
    r_tmp = None

    # append
    r2.save(tmp.path, append=True)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert r_tmp.metadata("shortName") == ["msl", "2d"]


def test_numpy_fs_grib_write_generating_proc_id():
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
        r1.save(tmp)
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


@pytest.mark.parametrize(
    "_kwargs,expected_value", [({}, 16), ({"bits_per_value": 12}, 12)]
)
def test_numpy_fs_grib_write_bits_per_value(_kwargs, expected_value):
    ds, _ = load_numpy_fs(1)

    with temp_file() as tmp:
        ds.save(tmp, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.metadata("bitsPerValue") == [expected_value] * len(ds)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
