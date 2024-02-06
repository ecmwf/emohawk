#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import sys

import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_file_or_numpy_fs  # noqa: E402


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_describe(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    # full contents
    df = f.describe()
    df = df.data

    ref = {
        "level": {
            ("t", "isobaricInhPa"): "1000,300,...",
            ("u", "isobaricInhPa"): "1000,300,...",
            ("v", "isobaricInhPa"): "1000,300,...",
        },
        "date": {
            ("t", "isobaricInhPa"): "20180801",
            ("u", "isobaricInhPa"): "20180801",
            ("v", "isobaricInhPa"): "20180801",
        },
        "time": {
            ("t", "isobaricInhPa"): "1200",
            ("u", "isobaricInhPa"): "1200",
            ("v", "isobaricInhPa"): "1200",
        },
        "step": {
            ("t", "isobaricInhPa"): "0",
            ("u", "isobaricInhPa"): "0",
            ("v", "isobaricInhPa"): "0",
        },
        "paramId": {
            ("t", "isobaricInhPa"): "130",
            ("u", "isobaricInhPa"): "131",
            ("v", "isobaricInhPa"): "132",
        },
        "class": {
            ("t", "isobaricInhPa"): "od",
            ("u", "isobaricInhPa"): "od",
            ("v", "isobaricInhPa"): "od",
        },
        "stream": {
            ("t", "isobaricInhPa"): "oper",
            ("u", "isobaricInhPa"): "oper",
            ("v", "isobaricInhPa"): "oper",
        },
        "type": {
            ("t", "isobaricInhPa"): "an",
            ("u", "isobaricInhPa"): "an",
            ("v", "isobaricInhPa"): "an",
        },
        "experimentVersionNumber": {
            ("t", "isobaricInhPa"): "0001",
            ("u", "isobaricInhPa"): "0001",
            ("v", "isobaricInhPa"): "0001",
        },
    }

    assert ref == df.to_dict()

    # repeated use
    df = f.describe()
    df = df.data
    assert ref == df.to_dict()

    # single param by shortName
    df = f.describe("t")
    df = df.data

    ref = {
        0: {
            "shortName": "t",
            "typeOfLevel": "isobaricInhPa",
            "level": "1000,300,400,850,500,700",
            "date": "20180801",
            "time": "1200",
            "step": "0",
            "paramId": "130",
            "class": "od",
            "stream": "oper",
            "type": "an",
            "experimentVersionNumber": "0001",
        }
    }

    assert ref[0] == df[0].to_dict()

    # repeated use
    df = f.describe(param="t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe("t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe(param="t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    # single param by paramId
    df = f.describe(130)
    df = df.data

    ref = {
        0: {
            "shortName": "t",
            "typeOfLevel": "isobaricInhPa",
            "level": "1000,300,400,850,500,700",
            "date": "20180801",
            "time": "1200",
            "step": "0",
            "paramId": "130",
            "class": "od",
            "stream": "oper",
            "type": "an",
            "experimentVersionNumber": "0001",
        }
    }

    assert ref[0] == df[0].to_dict()

    df = f.describe(param=130)
    df = df.data
    assert ref[0] == df[0].to_dict()


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_ls(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    # default keys
    f1 = f[0:4]
    df = f1.ls()

    ref = {
        "centre": {0: "ecmf", 1: "ecmf", 2: "ecmf", 3: "ecmf"},
        "shortName": {0: "t", 1: "u", 2: "v", 3: "t"},
        "typeOfLevel": {
            0: "isobaricInhPa",
            1: "isobaricInhPa",
            2: "isobaricInhPa",
            3: "isobaricInhPa",
        },
        "level": {0: 1000, 1: 1000, 2: 1000, 3: 850},
        "dataDate": {0: 20180801, 1: 20180801, 2: 20180801, 3: 20180801},
        "dataTime": {0: 1200, 1: 1200, 2: 1200, 3: 1200},
        "stepRange": {0: "0", 1: "0", 2: "0", 3: "0"},
        "dataType": {0: "an", 1: "an", 2: "an", 3: "an"},
        "number": {0: 0, 1: 0, 2: 0, 3: 0},
        "gridType": {
            0: "regular_ll",
            1: "regular_ll",
            2: "regular_ll",
            3: "regular_ll",
        },
    }

    assert ref == df.to_dict()

    # extra keys
    f1 = f[0:2]
    df = f1.ls(extra_keys=["paramId"])

    ref = {
        "centre": {0: "ecmf", 1: "ecmf"},
        "shortName": {0: "t", 1: "u"},
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 1000, 1: 1000},
        "dataDate": {0: 20180801, 1: 20180801},
        "dataTime": {0: 1200, 1: 1200},
        "stepRange": {0: "0", 1: "0"},
        "dataType": {0: "an", 1: "an"},
        "number": {0: 0, 1: 0},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
        "paramId": {0: 130, 1: 131},
    }

    assert ref == df.to_dict()


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_ls_keys(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    # default keys
    # positive num (=head)
    df = f.ls(n=2, keys=["shortName", "bottomLevel", "gridType"])
    ref = {
        "shortName": {0: "t", 1: "u"},
        "bottomLevel": {0: 1000, 1: 1000},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
    }

    assert ref == df.to_dict()

    # negative num (=tail)
    df = f.ls(n=-2, keys=["shortName", "bottomLevel", "gridType"])
    ref = {
        "shortName": {0: "u", 1: "v"},
        "bottomLevel": {0: 300, 1: 300},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
    }

    assert ref == df.to_dict()


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_ls_namespace(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    df = f.ls(n=2, namespace="vertical")
    ref = {
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 1000, 1: 1000},
    }
    assert ref == df.to_dict()

    df = f.ls(n=2, namespace="vertical", extra_keys="shortName")

    ref = {
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 1000, 1: 1000},
        "shortName": {0: "t", 1: "u"},
    }
    assert ref == df.to_dict()


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_ls_invalid_num(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    with pytest.raises(ValueError):
        f.ls(n=0)

    with pytest.raises(ValueError):
        f.ls(0)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_ls_invalid_arg(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    with pytest.raises(TypeError):
        f.ls(invalid=1)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_ls_num(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    # default keys

    # positive num (=head)
    df = f.ls(n=2)
    ref = {
        "centre": {0: "ecmf", 1: "ecmf"},
        "shortName": {0: "t", 1: "u"},
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 1000, 1: 1000},
        "dataDate": {0: 20180801, 1: 20180801},
        "dataTime": {0: 1200, 1: 1200},
        "stepRange": {0: "0", 1: "0"},
        "dataType": {0: "an", 1: "an"},
        "number": {0: 0, 1: 0},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
    }

    assert ref == df.to_dict()

    df = f.ls(2)
    assert ref == df.to_dict()

    # negative num (=tail)
    df = f.ls(n=-2)
    ref = {
        "centre": {0: "ecmf", 1: "ecmf"},
        "shortName": {0: "u", 1: "v"},
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 300, 1: 300},
        "dataDate": {0: 20180801, 1: 20180801},
        "dataTime": {0: 1200, 1: 1200},
        "stepRange": {0: "0", 1: "0"},
        "dataType": {0: "an", 1: "an"},
        "number": {0: 0, 1: 0},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
    }

    assert ref == df.to_dict()

    df = f.ls(-2)
    assert ref == df.to_dict()


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_head_num(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    # default keys
    df = f.head(n=2)
    ref = {
        "centre": {0: "ecmf", 1: "ecmf"},
        "shortName": {0: "t", 1: "u"},
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 1000, 1: 1000},
        "dataDate": {0: 20180801, 1: 20180801},
        "dataTime": {0: 1200, 1: 1200},
        "stepRange": {0: "0", 1: "0"},
        "dataType": {0: "an", 1: "an"},
        "number": {0: 0, 1: 0},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
    }

    assert ref == df.to_dict()

    df = f.head(2)
    assert ref == df.to_dict()


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_tail_num(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    # default keys
    df = f.tail(n=2)
    ref = {
        "centre": {0: "ecmf", 1: "ecmf"},
        "shortName": {0: "u", 1: "v"},
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 300, 1: 300},
        "dataDate": {0: 20180801, 1: 20180801},
        "dataTime": {0: 1200, 1: 1200},
        "stepRange": {0: "0", 1: "0"},
        "dataType": {0: "an", 1: "an"},
        "number": {0: 0, 1: 0},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
    }

    assert ref == df.to_dict()

    df = f.tail(2)
    assert ref == df.to_dict()


@pytest.mark.parametrize("mode", ["file"])
def test_grib_dump(mode):
    f = load_file_or_numpy_fs("test6.grib", mode)

    namespaces = (
        "default",
        "geography",
        "ls",
        "mars",
        "parameter",
        "statistics",
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
                "bitmapPresent": 0,
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

    # test_datetime()
    main(__file__)
