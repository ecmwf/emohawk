#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import sys

import pytest

from earthkit.data import from_source

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_file_or_numpy_fs  # noqa: E402


# @pytest.mark.skipif(("GITHUB_WORKFLOW" in os.environ) or True, reason="Not yet ready")
@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_order_by_single_message(mode):
    s = load_file_or_numpy_fs("test_single.grib", mode, folder="data")

    r = s.order_by("shortName")
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"

    r = s.order_by(["shortName"])
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"

    r = s.order_by(["shortName", "level"])
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"


class _CustomOrder:
    def __call__(self, x, y):
        r = dict(t=2, u=0, v=1)
        a = r[x]
        b = r[y]
        if a == b:
            return 0
        if a > b:
            return 1
        if a < b:
            return -1


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "params,expected_meta",
    [
        ("shortName", dict(shortName=["t", "t", "u", "u", "v", "v"])),
        (["shortName"], dict(shortName=["t", "t", "u", "u", "v", "v"])),
        (
            ["shortName", "level"],
            dict(
                shortName=["t", "t", "u", "u", "v", "v"],
                level=[850, 1000, 850, 1000, 850, 1000],
            ),
        ),
        (dict(shortName="ascending"), dict(shortName=["t", "t", "u", "u", "v", "v"])),
        (dict(shortName="descending"), dict(shortName=["v", "v", "u", "u", "t", "t"])),
        (
            dict(shortName="ascending", level="ascending"),
            dict(
                shortName=["t", "t", "u", "u", "v", "v"],
                level=[850, 1000, 850, 1000, 850, 1000],
            ),
        ),
        (
            dict(shortName="ascending", level="descending"),
            dict(
                shortName=["t", "t", "u", "u", "v", "v"],
                level=[1000, 850, 1000, 850, 1000, 850],
            ),
        ),
        (
            dict(shortName=_CustomOrder()),
            dict(shortName=["u", "u", "v", "v", "t", "t"]),
        ),
        (
            dict(shortName=["u", "v", "t"]),
            dict(shortName=["u", "u", "v", "v", "t", "t"]),
        ),
        (
            dict(shortName=["u", "v", "t"], level=[1000, 850]),
            dict(
                shortName=["u", "u", "v", "v", "t", "t"],
                level=[1000, 850, 1000, 850, 1000, 850],
            ),
        ),
    ],
)
def test_grib_order_by_single_file_(
    mode,
    params,
    expected_meta,
):
    f = load_file_or_numpy_fs("test6.grib", mode)

    g = f.order_by(params)
    assert len(g) == len(f)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "params,expected_meta",
    [
        (
            "shortName",
            dict(shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"]),
        ),
        (
            ["shortName"],
            dict(shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"]),
        ),
        (
            ["shortName", "level"],
            dict(
                shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"],
                level=[500, 850, 850, 1000, 850, 1000, 850, 1000, 500, 850],
            ),
        ),
        (
            dict(shortName="ascending"),
            dict(shortName=["t", "t", "t", "t", "u", "u", "v", "v", "z", "z"]),
        ),
        (
            dict(shortName="descending"),
            dict(shortName=["z", "z", "v", "v", "u", "u", "t", "t", "t", "t"]),
        ),
    ],
)
def test_grib_order_by_multi_file(mode, params, expected_meta):
    f1 = load_file_or_numpy_fs("test4.grib", mode)
    f2 = load_file_or_numpy_fs("test6.grib", mode)
    f = from_source("multi", [f1, f2])

    g = f.order_by(params)
    assert len(g) == len(f)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_order_by_with_sel(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    g = f.sel(level=500)
    assert len(g) == 3
    r = g.order_by("shortName")
    assert len(r) == len(g)
    assert r.metadata("shortName") == ["t", "u", "v"]

    g = f.sel(level=500)
    assert len(g) == 3
    r = g.order_by({"shortName": "descending"})
    assert len(r) == len(g)
    assert r.metadata("shortName") == ["v", "u", "t"]


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_order_by_valid_datetime(mode):
    f = load_file_or_numpy_fs("t_time_series.grib", mode, folder="data")

    g = f.order_by(valid_datetime="descending")
    assert len(g) == 10

    ref = [
        datetime.datetime(2020, 12, 23, 12, 0),
        datetime.datetime(2020, 12, 23, 12, 0),
        datetime.datetime(2020, 12, 21, 21, 0),
        datetime.datetime(2020, 12, 21, 21, 0),
        datetime.datetime(2020, 12, 21, 18, 0),
        datetime.datetime(2020, 12, 21, 18, 0),
        datetime.datetime(2020, 12, 21, 15, 0),
        datetime.datetime(2020, 12, 21, 15, 0),
        datetime.datetime(2020, 12, 21, 12, 0),
        datetime.datetime(2020, 12, 21, 12, 0),
    ]

    assert g.metadata("valid_datetime") == ref
