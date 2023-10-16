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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from numpy_fs_fixtures import load_numpy_fs_file  # noqa: E402

# Note: Almost all grib metadata tests are also run for numpyfs.
# See grib/test_grib_summary.py


def test_numpy_fs_dump():
    f, _ = load_numpy_fs_file("test6.grib")

    namespaces = (
        "default",
        "geography",
        "ls",
        "mars",
        "parameter",
        "time",
        "vertical",
    )

    # default
    r = f[0].dump(_as_raw=True)
    ref = [
        {
            "title": "ls",
            "data": {
                "edition": 1,
                "centre": "ecmf",
                "typeOfLevel": "isobaricInhPa",
                "level": 1000,
                "dataDate": 20180801,
                "stepRange": "0",
                "dataType": "an",
                "shortName": "t",
                "packingType": "grid_simple",
                "gridType": "regular_ll",
            },
            "tooltip": "Keys in the ecCodes ls namespace",
        },
        {
            "title": "geography",
            "data": {
                # "bitmapPresent": 0,
                "latitudeOfFirstGridPointInDegrees": 90.0,
                "longitudeOfFirstGridPointInDegrees": 0.0,
                "latitudeOfLastGridPointInDegrees": -90.0,
                "longitudeOfLastGridPointInDegrees": 330.0,
                "iScansNegatively": 0,
                "jScansPositively": 0,
                "jPointsAreConsecutive": 0,
                "jDirectionIncrementInDegrees": 30.0,
                "iDirectionIncrementInDegrees": 30.0,
                "gridType": "regular_ll",
            },
            "tooltip": "Keys in the ecCodes geography namespace",
        },
        {
            "title": "mars",
            "data": {
                "domain": "g",
                "levtype": "pl",
                "levelist": 1000,
                "date": 20180801,
                "time": 1200,
                "step": 0,
                "param": "t",
                "class": "od",
                "type": "an",
                "stream": "oper",
                "expver": "0001",
            },
            "tooltip": "Keys in the ecCodes mars namespace",
        },
        {
            "title": "parameter",
            "data": {
                "centre": "ecmf",
                "paramId": 130,
                "units": "K",
                "name": "Temperature",
                "shortName": "t",
            },
            "tooltip": "Keys in the ecCodes parameter namespace",
        },
        {
            "title": "time",
            "data": {
                "dataDate": 20180801,
                "dataTime": 1200,
                "stepUnits": 1,
                "stepType": "instant",
                "stepRange": "0",
                "startStep": 0,
                "endStep": 0,
                "validityDate": 20180801,
                "validityTime": 1200,
            },
            "tooltip": "Keys in the ecCodes time namespace",
        },
        {
            "title": "vertical",
            "data": {"typeOfLevel": "isobaricInhPa", "level": 1000},
            "tooltip": "Keys in the ecCodes vertical namespace",
        },
    ]

    assert len(r) == len(namespaces)
    assert isinstance(r, list)
    for d in r:
        ns = d["title"]
        assert ns in namespaces
        if ns not in ("default", "statistics"):
            assert d == [x for x in ref if x["title"] == ns][0], ns

    # a namespace
    r = f[0].dump(namespace="mars", _as_raw=True)
    ref = [
        {
            "title": "mars",
            "data": {
                "domain": "g",
                "levtype": "pl",
                "levelist": 1000,
                "date": 20180801,
                "time": 1200,
                "step": 0,
                "param": "t",
                "class": "od",
                "type": "an",
                "stream": "oper",
                "expver": "0001",
            },
            "tooltip": "Keys in the ecCodes mars namespace",
        }
    ]
    assert r == ref

    # namespace reformatted
    r = f[0].dump(namespace="mars", _as_raw=False)
    ref = {
        "mars": {
            "domain": "g",
            "levtype": "pl",
            "levelist": 1000,
            "date": 20180801,
            "time": 1200,
            "step": 0,
            "param": "t",
            "class": "od",
            "type": "an",
            "stream": "oper",
            "expver": "0001",
        }
    }
    assert r == ref


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
