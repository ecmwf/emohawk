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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_file_or_numpy_fs  # noqa: E402


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_indices_base(mode):
    ds = load_file_or_numpy_fs("tuv_pl.grib", mode)

    ref = {
        "class": ["od"],
        "stream": ["oper"],
        "levtype": ["pl"],
        "type": ["an"],
        "expver": ["0001"],
        "date": [20180801],
        "time": [1200],
        "domain": ["g"],
        "number": [0],
        "levelist": [300, 400, 500, 700, 850, 1000],
        "param": ["t", "u", "v"],
    }

    r = ds.indices()
    assert r == ref

    ref = {
        "levelist": [300, 400, 500, 700, 850, 1000],
        "param": ["t", "u", "v"],
    }
    r = ds.indices(squeeze=True)
    assert r == ref

    ref = ["t", "u", "v"]
    r = ds.index("param")
    assert r == ref


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_indices_sel(mode):
    ds = load_file_or_numpy_fs("tuv_pl.grib", mode)

    ref = {
        "class": ["od"],
        "stream": ["oper"],
        "levtype": ["pl"],
        "type": ["an"],
        "expver": ["0001"],
        "date": [20180801],
        "time": [1200],
        "domain": ["g"],
        "number": [0],
        "levelist": [300, 400, 500, 700, 850, 1000],
        "param": ["t"],
    }

    ds1 = ds.sel(param="t")
    r = ds1.indices()
    assert r == ref

    ref = {
        "levelist": [300, 400, 500, 700, 850, 1000],
    }
    r = ds1.indices(squeeze=True)
    assert r == ref


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_indices_multi(mode):
    f1 = load_file_or_numpy_fs("tuv_pl.grib", mode)
    f2 = load_file_or_numpy_fs("ml_data.grib", mode, folder="data")
    ds = f1 + f2

    ref = {
        "class": ["od"],
        "stream": ["oper"],
        "levtype": ["ml", "pl"],
        "type": ["an", "fc"],
        "expver": ["0001"],
        "date": [20180111, 20180801],
        "time": [1200],
        "domain": ["g"],
        "number": [0],
        "levelist": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            300,
            400,
            500,
            700,
            850,
            1000,
        ],
        "param": ["lnsp", "t", "u", "v"],
    }

    r = ds.indices()
    assert r == ref


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_indices_multi_Del(mode):
    f1 = load_file_or_numpy_fs("tuv_pl.grib", mode)
    f2 = load_file_or_numpy_fs("ml_data.grib", mode, folder="data")
    ds = f1 + f2

    ref = {
        "class": ["od"],
        "stream": ["oper"],
        "levtype": ["ml", "pl"],
        "type": ["an", "fc"],
        "expver": ["0001"],
        "date": [20180111, 20180801],
        "time": [1200],
        "domain": ["g"],
        "number": [0],
        "levelist": [93, 500],
        "param": ["t"],
    }

    ds1 = ds.sel(param="t", level=[93, 500])
    r = ds1.indices()
    assert r == ref


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_indices_order_by(mode):
    ds = load_file_or_numpy_fs("tuv_pl.grib", mode)

    ref = {
        "class": ["od"],
        "stream": ["oper"],
        "levtype": ["pl"],
        "type": ["an"],
        "expver": ["0001"],
        "date": [20180801],
        "time": [1200],
        "domain": ["g"],
        "number": [0],
        "levelist": [300, 400, 500, 700, 850, 1000],
        "param": ["t", "u", "v"],
    }

    ds1 = ds.order_by(levelist="descending")
    r = ds1.indices()
    assert r == ref
