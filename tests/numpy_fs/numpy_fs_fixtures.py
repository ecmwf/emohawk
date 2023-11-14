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

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


def load_numpy_fs(num):
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


def load_numpy_fs_file(fname):
    ds_in = from_source("file", earthkit_examples_file(fname))
    md = ds_in.metadata("param")

    ds = FieldList.from_numpy(
        ds_in.values, [m.override(edition=1) for m in ds_in.metadata()]
    )

    return (ds, md)


def check_numpy_fs(ds, ds_input, md_full):
    assert len(ds_input) in [1, 2, 3]

    assert len(ds) == len(md_full)
    assert ds.metadata("param") == md_full
    assert np.allclose(ds[0].values, ds_input[0][0].values)

    # # values metadata
    # keys = ["min", "max"]
    # for k in keys:
    #     assert np.isclose(ds[0].metadata(k), ds_input[0][0].metadata(k))

    # check slice
    r = ds[1]
    assert r.metadata("param") == "msl"

    if len(ds_input) > 1:
        r = ds[1:3]
        assert len(r) == 2
        assert r.metadata("param") == ["msl", "t"]
        assert r[0].metadata("param") == "msl"
        assert r[1].metadata("param") == "t"
        assert np.allclose(r[0].values, ds_input[0][1].values)
        assert np.allclose(r[1].values, ds_input[1][0].values)

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


def check_numpy_fs_from_to_fieldlist(ds, ds_input, md_full, flatten=False, dtype=None):
    assert len(ds_input) in [1, 2, 3]
    assert len(ds) == len(md_full)
    assert ds.metadata("param") == md_full

    np_kwargs = {"flatten": flatten, "dtype": dtype}

    assert np.allclose(
        ds[0].to_numpy(**np_kwargs), ds_input[0][0].to_numpy(**np_kwargs)
    )

    assert ds.to_numpy(**np_kwargs).shape == ds_input[0].to_numpy(**np_kwargs).shape
    assert ds._array.shape == ds_input[0].to_numpy(**np_kwargs).shape

    # check slice
    r = ds[1]
    assert r.metadata("param") == "msl"

    if len(ds_input) > 1:
        r = ds[1:3]
        assert len(r) == 2
        assert r.metadata("param") == ["msl", "t"]
        assert r[0].metadata("param") == "msl"
        assert r[1].metadata("param") == "t"
        assert np.allclose(
            r[0].to_numpy(**np_kwargs), ds_input[0][1].to_numpy(**np_kwargs)
        )
        assert np.allclose(
            r[1].to_numpy(**np_kwargs), ds_input[1][0].to_numpy(**np_kwargs)
        )

        # check sel
        r = ds.sel(shortName="msl")
        assert len(r) == 1
        assert r.metadata("shortName") == ["msl"]
        assert r[0].metadata("param") == "msl"
        assert np.allclose(
            r[0].to_numpy(**np_kwargs), ds_input[0][1].to_numpy(**np_kwargs)
        )

    if len(ds_input) == 3:
        r = ds[1:13:4]
        assert len(r) == 3
        assert r.metadata("param") == ["msl", "t", "u"]
        assert r[0].metadata("param") == "msl"
        assert r[1].metadata("param") == "t"
        assert r[2].metadata("param") == "u"


def check_save_to_disk(ds, len_ref, meta_ref):
    tmp = temp_file()
    ds.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == len_ref
    assert r_tmp.metadata("shortName") == meta_ref
    r_tmp = None
