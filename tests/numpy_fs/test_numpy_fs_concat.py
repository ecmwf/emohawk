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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


def _check_save_to_disk(ds, len_ref, meta_ref):
    tmp = temp_file()
    ds.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == len_ref
    assert r_tmp.metadata("shortName") == meta_ref
    r_tmp = None


def _check_contents(ds, ds_input, md_full):
    assert len(ds_input) in [2, 3]

    assert len(ds) == len(md_full)
    assert ds.metadata("param") == md_full

    # check slice
    r = ds[1]
    assert r.metadata("param") == "msl"

    r = ds[1:3]
    assert len(r) == 2
    assert r.metadata("param") == ["msl", "t"]
    assert r[0].metadata("param") == "msl"
    assert r[1].metadata("param") == "t"
    assert np.allclose(r[0].values, ds_input[0][1].values)
    assert np.allclose(r[1].values, ds_input[1][0].values)
    with pytest.raises(ValueError):
        _ = r.values

    # check sel
    r = ds.sel(shortName="msl")
    assert len(r) == 1
    assert r.metadata("shortName") == ["msl"]
    assert r[0].metadata("param") == "msl"
    assert np.allclose(r[0].values, ds_input[0][1].values)

    if len(ds_input) == 3:
        r = ds[1:13:4]
        assert len(r) == 3
        assert r.metadata("param") == ["msl", "t", "u"]
        assert r[0].metadata("param") == "msl"
        assert r[1].metadata("param") == "t"
        assert r[2].metadata("param") == "u"


def _prepare_ds(num):
    assert num in [1, 2, 3]
    files = ["test.grib", "test6.grib", "tuv_pl.grib"]
    files = files[:num]

    ds_in = []
    md = []
    for fname in files:
        ds_in.append(from_source("file", earthkit_examples_file(fname)))
        md += ds_in[-1].metadata("param")

    ds = []
    for x in ds_in:
        ds.append(
            FieldList.from_numpy(
                x.values, [m.override(edition=1) for m in x.metadata()]
            )
        )

    return (*ds, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_list_grib_concat_2a(mode):
    ds1, ds2, md = _prepare_ds(2)

    if mode == "oper":
        ds = ds1 + ds2
    else:
        ds = from_source("multi", ds1, ds2)

    _check_contents(ds, [ds1, ds2], md)
    _check_save_to_disk(ds, 8, md)


def test_numpy_list_grib_concat_2b():
    ds1, ds2, md = _prepare_ds(2)
    ds1_ori = ds1
    ds1 += ds2

    _check_contents(ds1, [ds1_ori, ds2], md)
    _check_save_to_disk(ds1, 8, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_list_grib_concat_3a(mode):
    ds1, ds2, ds3, md = _prepare_ds(3)

    if mode == "oper":
        ds = ds1 + ds2
        ds = ds + ds3
    else:
        ds = from_source("multi", ds1, ds2)
        ds = from_source("multi", ds, ds3)

    _check_contents(ds, [ds1, ds2, ds3], md)
    _check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["oper", "multi"])
def test_numpy_list_grib_concat_3b(mode):
    ds1, ds2, ds3, md = _prepare_ds(3)

    if mode == "oper":
        ds = ds1 + ds2 + ds3
    else:
        ds = from_source("multi", ds1, ds2, ds3)

    _check_contents(ds, [ds1, ds2, ds3], md)
    _check_save_to_disk(ds, 26, md)


def test_numpy_list_grib_from_empty_1():
    ds_e = FieldList()
    ds, md = _prepare_ds(1)
    ds1 = ds_e + ds
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.metadata("param") == md
    _check_save_to_disk(ds1, 2, md)


def test_numpy_list_grib_from_empty_2():
    ds_e = FieldList()
    ds, md = _prepare_ds(1)
    ds1 = ds + ds_e
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    assert ds1.metadata("param") == md
    _check_save_to_disk(ds1, 2, md)


def test_numpy_list_grib_from_empty_3():
    ds_e = FieldList()
    ds1, ds2, md = _prepare_ds(2)
    ds = ds_e + ds1 + ds2

    _check_contents(ds, [ds1, ds2], md)
    _check_save_to_disk(ds, 8, md)


def test_numpy_list_grib_from_empty_4():
    ds = FieldList()
    ds1, md = _prepare_ds(1)
    ds += ds1
    assert id(ds) == id(ds1)
    assert len(ds) == 2
    assert ds.metadata("param") == md
    _check_save_to_disk(ds, 2, md)


def test_numpy_list_grib_from_empty_5():
    ds = FieldList()
    ds1, ds2, md = _prepare_ds(2)
    ds += ds1 + ds2

    _check_contents(ds, [ds1, ds2], md)
    _check_save_to_disk(ds, 8, md)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
