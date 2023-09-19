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

import pytest

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from numpy_fs_fixtures import (  # noqa: E402
    check_numpy_fs,
    check_save_to_disk,
    load_numpy_fs,
)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_fs_grib_concat_2a(mode):
    ds1, ds2, md = load_numpy_fs(2)

    if mode == "oper":
        ds = ds1 + ds2
    else:
        ds = from_source("multi", ds1, ds2)

    check_numpy_fs(ds, [ds1, ds2], md)
    check_save_to_disk(ds, 8, md)


def test_numpy_fs_grib_concat_2b():
    ds1, ds2, md = load_numpy_fs(2)
    ds1_ori = ds1
    ds1 += ds2

    check_numpy_fs(ds1, [ds1_ori, ds2], md)
    check_save_to_disk(ds1, 8, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_fs_grib_concat_3a(mode):
    ds1, ds2, ds3, md = load_numpy_fs(3)

    if mode == "oper":
        ds = ds1 + ds2
        ds = ds + ds3
    else:
        ds = from_source("multi", ds1, ds2)
        ds = from_source("multi", ds, ds3)

    check_numpy_fs(ds, [ds1, ds2, ds3], md)
    check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_fs_grib_concat_3b(mode):
    ds1, ds2, ds3, md = load_numpy_fs(3)

    if mode == "oper":
        ds = ds1 + ds2 + ds3
    else:
        ds = from_source("multi", ds1, ds2, ds3)

    check_numpy_fs(ds, [ds1, ds2, ds3], md)
    check_save_to_disk(ds, 26, md)


def test_numpy_fs_grib_from_empty_1():
    ds_e = FieldList()
    ds, md = load_numpy_fs(1)
    ds1 = ds_e + ds
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.metadata("param") == md
    check_save_to_disk(ds1, 2, md)


def test_numpy_fs_grib_from_empty_2():
    ds_e = FieldList()
    ds, md = load_numpy_fs(1)
    ds1 = ds + ds_e
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.metadata("param") == md
    check_save_to_disk(ds1, 2, md)


def test_numpy_fs_grib_from_empty_3():
    ds_e = FieldList()
    ds1, ds2, md = load_numpy_fs(2)
    ds = ds_e + ds1 + ds2

    check_numpy_fs(ds, [ds1, ds2], md)
    check_save_to_disk(ds, 8, md)


def test_numpy_fs_grib_from_empty_4():
    ds = FieldList()
    ds1, md = load_numpy_fs(1)
    ds += ds1
    assert id(ds) == id(ds1)
    assert len(ds) == 2
    assert ds.metadata("param") == md
    check_save_to_disk(ds, 2, md)


def test_numpy_fs_grib_from_empty_5():
    ds = FieldList()
    ds1, ds2, md = load_numpy_fs(2)
    ds += ds1 + ds2

    check_numpy_fs(ds, [ds1, ds2], md)
    check_save_to_disk(ds, 8, md)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
