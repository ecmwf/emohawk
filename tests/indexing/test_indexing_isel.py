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


@pytest.mark.cache
@pytest.mark.parametrize("mode", ["file", "multi", "directory"])
@pytest.mark.parametrize(
    "params,expected_meta,metadata_keys",
    [
        (dict(param=1, level=2), [["u", 500]], ["shortName", "level:l"]),
        (dict(param=1, level=2), [[131, 500]], ["paramId", "level:l"]),
        (
            dict(param=[0, 1], level=[2, 3]),
            [
                ["t", 500],
                ["t", 700],
                ["u", 500],
                ["u", 700],
            ],
            ["shortName", "level:l"],
        ),
        (
            dict(param=[0], level=[3, 2], type=0),
            [
                ["t", 500, "an"],
                ["t", 700, "an"],
            ],
            ["shortName", "level:l", "marsType"],
        ),
        (
            dict(level=-1),
            [
                ["t", 1000],
                ["u", 1000],
                ["v", 1000],
            ],
            ["shortName", "level:l"],
        ),
    ],
)
def test_indexing_isel_grib_file(mode, params, expected_meta, metadata_keys):
    tmp, path = get_tmp_fixture(mode)
    ds = from_source("file", path, indexing=True)
    assert len(ds) == 18

    g = ds.isel(**params)
    assert len(g) == len(expected_meta)

    # we sort the result to make the contents checking simpler
    g = g.order_by(["param", "level"])

    if len(expected_meta) > 0:
        keys = list(params.keys())
        if metadata_keys:
            keys = metadata_keys

        assert g.metadata(keys) == expected_meta


@pytest.mark.cache
def test_indexing_isel_grib_file_invalid_key():
    tmp, path = get_tmp_fixture("file")
    ds = from_source("file", path, indexing=True)
    assert len(ds) == 18

    r = ds.isel(INVALIDKEY=0)
    assert len(r) == 0

    with pytest.raises(IndexError):
        ds.isel(level=500)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
