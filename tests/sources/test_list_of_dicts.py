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

import pytest

from earthkit.data import from_source


@pytest.fixture
def lod():
    prototype = {
        "gridType": "regular_ll",
        "Nx": 2,
        "Ny": 3,
        "distinctLatitudes": [-10.0, 0.0, 10.0],
        "distinctLongitudes": [0.0, 10.0],
        "_param_id": 167,
        "values": [[1, 2], [3, 4], [5, 6]],
        "date": "20180801",
        "time": "1200",
    }
    return [
        {"param": "t", "levelist": 500, **prototype},
        {"param": "t", "levelist": 850, **prototype},
        {"param": "u", "levelist": 500, **prototype},
        {"param": "u", "levelist": 850, **prototype},
        {"param": "d", "levelist": 850, **prototype},
        {"param": "d", "levelist": 600, **prototype},
    ]


def test_list_of_dicts(lod):
    ds = from_source("list-of-dicts", lod)

    assert len(ds) == 6
    ref = [("t", 500), ("t", 850), ("u", 500), ("u", 850), ("d", 850), ("d", 600)]
    assert ds.metadata("param", "levelist") == ref

    assert ds[0].metadata("step") == "0"

    assert ds[0].datetime() == {
        "base_time": datetime.datetime(2018, 8, 1, 12, 0),
        "valid_time": datetime.datetime(2018, 8, 1, 12, 0),
    }


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
