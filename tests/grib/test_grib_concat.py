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

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


def _check_save_to_disk(ds, len_ref, meta_ref):
    # save to disk
    tmp = temp_file()
    ds.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == len_ref
    assert r_tmp.metadata("shortName") == meta_ref
    r_tmp = None


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_grib_concat(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))

    if mode == "oper":
        ds = ds1 + ds2
    else:
        ds = from_source("multi", ds1, ds2)

    # check metadata
    assert len(ds) == 8
    md = ds1.metadata("param") + ds2.metadata("param")
    assert ds.metadata("param") == md

    # check slice
    r = ds[1]
    assert r.metadata("param") == "msl"

    r = ds[1:3]
    assert len(r) == 2
    assert r.metadata("param") == ["msl", "t"]
    assert r[0].metadata("param") == "msl"
    assert r[1].metadata("param") == "t"

    # check sel
    r = ds.sel(param="2t")
    assert len(r) == 1
    assert r.metadata("param") == ["2t"]
    assert r[0].metadata("param") == "2t"

    # check saving to disk
    _check_save_to_disk(ds, 8, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_grib_concat_3a(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))
    ds3 = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    md = ds1.metadata("param") + ds2.metadata("param") + ds3.metadata("param")

    if mode == "oper":
        ds = ds1 + ds2
        ds = ds + ds3
    else:
        ds = from_source("multi", ds1, ds2)
        ds = from_source("multi", ds, ds3)

    assert len(ds) == 26
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_grib_concat_3b(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))
    ds3 = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    md = ds1.metadata("param") + ds2.metadata("param") + ds3.metadata("param")

    if mode == "oper":
        ds = ds1 + ds2 + ds3
    else:
        ds = from_source("multi", ds1, ds2, ds3)

    assert len(ds) == 26
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 26, md)


def test_grib_from_empty_1():
    ds_e = FieldList()
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds.metadata("param")

    ds1 = ds_e + ds
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    _check_save_to_disk(ds1, 2, md)


def test_grib_from_empty_2():
    ds_e = FieldList()
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds.metadata("param")

    ds1 = ds + ds_e
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    _check_save_to_disk(ds1, 2, md)


def test_grib_from_empty_3():
    ds_e = FieldList()
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))
    md = ds1.metadata("param") + ds2.metadata("param")

    ds3 = ds_e + ds1 + ds2
    assert len(ds3) == 8
    _check_save_to_disk(ds3, 8, md)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
