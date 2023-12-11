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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from indexing_fixtures import get_tmp_fixture  # noqa


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


@pytest.mark.cache
@pytest.mark.parametrize("mode", ["file", "multi", "directory"])
@pytest.mark.parametrize(
    "params,expected_meta",
    [
        ("param", dict(shortName=["t"] * 6 + ["u"] * 6 + ["v"] * 6)),
        (["param"], dict(shortName=["t"] * 6 + ["u"] * 6 + ["v"] * 6)),
        (
            ["param", "level"],
            dict(
                shortName=["t"] * 6 + ["u"] * 6 + ["v"] * 6,
                level=[300, 400, 500, 700, 850, 1000] * 3,
            ),
        ),
        (dict(param="ascending"), dict(shortName=["t"] * 6 + ["u"] * 6 + ["v"] * 6)),
        (dict(param="descending"), dict(shortName=["v"] * 6 + ["u"] * 6 + ["t"] * 6)),
        (
            dict(param="ascending", level="ascending"),
            dict(
                shortName=["t"] * 6 + ["u"] * 6 + ["v"] * 6,
                level=[300, 400, 500, 700, 850, 1000] * 3,
            ),
        ),
        (
            dict(param="ascending", level="descending"),
            dict(
                shortName=["t"] * 6 + ["u"] * 6 + ["v"] * 6,
                level=[1000, 850, 700, 500, 400, 300] * 3,
            ),
        ),
        (
            dict(param=["u", "v", "t"]),
            dict(shortName=["u"] * 6 + ["v"] * 6 + ["t"] * 6),
        ),
        (
            dict(param=["u", "v", "t"], level=[1000, 850, 300, 500, 400, 700]),
            dict(
                shortName=["u"] * 6 + ["v"] * 6 + ["t"] * 6,
                level=[1000, 850, 300, 500, 400, 700] * 3,
            ),
        ),
        # (
        #     dict(param=_CustomOrder()),
        #     dict(shortName=["u"] * 6 + ["v"] * 6 + ["t"] * 6),
        # ),
    ],
)
def test_indexing_order_by_grib_file(mode, params, expected_meta):
    tmp, path = get_tmp_fixture(mode)
    ds = from_source("file", path, indexing=True)
    assert len(ds) == 18

    g = ds.order_by(params)
    assert len(g) == len(ds)

    for k, v in expected_meta.items():
        assert g.metadata(k) == v
