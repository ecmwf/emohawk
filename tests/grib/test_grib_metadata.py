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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_file_or_numpy_fs  # noqa: E402


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("shortName", "2t"),
        ("shortName:s", "2t"),
        ("shortName:str", "2t"),
        ("centre", "ecmf"),
        ("centre:l", 98),
        ("level", 0),
        ("level:l", 0),
        ("level:int", 0),
        (["shortName"], ["2t"]),
        (["shortName", "level"], ["2t", 0]),
        (("shortName"), "2t"),
        (("shortName", "level"), ("2t", 0)),
    ],
)
def test_grib_metadata_grib(mode, key, expected_value):
    f = load_file_or_numpy_fs("test_single.grib", mode, folder="data")
    sn = f.metadata(key)
    assert sn == [expected_value]
    sn = f[0].metadata(key)
    assert sn == expected_value


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key,astype,expected_value",
    [
        ("shortName", str, "2t"),
        ("shortName", None, "2t"),
        ("centre", None, "ecmf"),
        ("centre", str, "ecmf"),
        ("centre", int, 98),
        ("level", None, 0),
        ("level", str, "0"),
        ("level", int, 0),
    ],
)
def test_grib_metadata_astype_1(mode, key, astype, expected_value):
    f = load_file_or_numpy_fs("test_single.grib", mode, folder="data")
    sn = f.metadata(key, astype=astype)
    assert sn == [expected_value]
    sn = f[0].metadata(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("shortName", ["t", "u", "v"] * 6),
        ("shortName:s", ["t", "u", "v"] * 6),
        ("shortName:str", ["t", "u", "v"] * 6),
        ("level", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("level:l", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("level:int", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
    ],
)
def test_grib_metadata_18(mode, key, expected_value):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    sn = f.metadata(key)
    assert sn == expected_value


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key,astype,expected_value",
    [
        ("shortName", str, ["t", "u", "v"] * 6),
        ("shortName", None, ["t", "u", "v"] * 6),
        (
            "level",
            int,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
        (
            "level",
            None,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
    ],
)
def test_grib_metadata_astype_18(mode, key, astype, expected_value):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    sn = f.metadata(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("latitudeOfFirstGridPointInDegrees", 90.0),
        ("latitudeOfFirstGridPointInDegrees:d", 90.0),
        ("latitudeOfFirstGridPointInDegrees:float", 90.0),
    ],
)
def test_grib_metadata_double_1(mode, key, expected_value):
    f = load_file_or_numpy_fs("test_single.grib", mode, folder="data")
    r = f.metadata(key)
    assert len(r) == 1
    assert np.isclose(r[0], expected_value)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key",
    [
        ("latitudeOfFirstGridPointInDegrees"),
        ("latitudeOfFirstGridPointInDegrees:d"),
        ("latitudeOfFirstGridPointInDegrees:float"),
    ],
)
def test_grib_metadata_double_18(mode, key):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    ref = [90.0] * 18
    r = f.metadata(key)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "key,astype",
    [
        ("latitudeOfFirstGridPointInDegrees", None),
        ("latitudeOfFirstGridPointInDegrees", float),
    ],
)
def test_grib_metadata_double_astype_18(mode, key, astype):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    ref = [90.0] * 18

    r = f.metadata(key, astype=astype)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_get_long_array_1(mode):
    f = load_file_or_numpy_fs(
        "rgg_small_subarea_cellarea_ref.grib", mode, folder="data"
    )

    assert len(f) == 1
    pl = f.metadata("pl")
    assert len(pl) == 1
    pl = pl[0]
    assert isinstance(pl, np.ndarray)
    assert len(pl) == 73
    assert pl[0] == 24
    assert pl[1] == 28
    assert pl[20] == 104
    assert pl[72] == 312


@pytest.mark.parametrize("mode", ["file"])
def test_grib_get_double_array_values_1(mode):
    f = load_file_or_numpy_fs("test_single.grib", mode, folder="data")

    v = f.metadata("values")
    assert len(v) == 1
    v = v[0]
    assert isinstance(v, np.ndarray)
    eps = 1e-5
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )


@pytest.mark.parametrize("mode", ["file"])
def test_grib_get_double_array_values_18(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    v = f.metadata("values")
    assert isinstance(v, list)
    assert len(v) == 18
    for d in v:
        assert isinstance(d, np.ndarray)
        assert d.shape == (84,)

    eps = 1e-5
    check_array(
        v[0],
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    check_array(
        v[15],
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_get_double_array_1(mode):
    f = load_file_or_numpy_fs("ml_data.grib", mode, folder="data")[0]
    # f is now a field!
    v = f.metadata("pv")
    assert isinstance(v, np.ndarray)
    assert len(v) == 276
    assert np.isclose(v[0], 0.0)
    assert np.isclose(v[1], 2.0003650188446045)
    assert np.isclose(v[20], 316.4207458496094)
    assert np.isclose(v[275], 1.0)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_get_double_array_18(mode):
    f = load_file_or_numpy_fs("ml_data.grib", mode, folder="data")
    v = f.metadata("pv")
    assert isinstance(v, list)
    assert len(v) == 36
    for row in v:
        assert isinstance(row, np.ndarray)
        assert len(row) == 276

    eps = 0.001
    assert np.isclose(v[0][1], 2.0003650188446045, eps)
    assert np.isclose(v[0][20], 316.4207458496094, eps)
    assert np.isclose(v[17][1], 2.0003650188446045, eps)
    assert np.isclose(v[17][20], 316.4207458496094, eps)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_metadata_type_qualifier(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)[0:4]

    # to str
    r = f.metadata("centre:s")
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("centre:str")
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("level:s")
    assert r == ["1000", "1000", "1000", "850"]
    r = f.metadata("level:str")
    assert r == ["1000", "1000", "1000", "850"]

    # to int
    r = f.metadata("centre:l")
    assert r == [98, 98, 98, 98]
    r = f.metadata("centre:int")
    assert r == [98, 98, 98, 98]
    r = f.metadata("level:d")
    assert r == [1000, 1000, 1000, 850]
    r = f.metadata("level:int")
    assert r == [1000, 1000, 1000, 850]

    # to float
    r = f.metadata("centre:d")
    assert np.allclose(np.array(r), np.array([98.0, 98.0, 98.0, 98.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.metadata("centre:float")
    assert np.allclose(np.array(r), np.array([98.0, 98.0, 98.0, 98.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.metadata("level:d")
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.metadata("level:float")
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_metadata_astype(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)[0:4]

    # to str
    r = f.metadata("centre", astype=None)
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("centre", astype=str)
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("level", astype=str)
    assert r == ["1000", "1000", "1000", "850"]

    # to int
    r = f.metadata("centre", astype=int)
    assert r == [98, 98, 98, 98]
    r = f.metadata("level", astype=int)
    assert r == [1000, 1000, 1000, 850]

    # to float
    r = f.metadata("level", astype=float)
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)

    # multi
    r = f.metadata(["level", "cfVarName"], astype=(int, None))
    assert r == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    r = f.metadata(["level", "cfVarName"], astype=str)
    assert r == [["1000", "t"], ["1000", "u"], ["1000", "v"], ["850", "t"]]

    # non matching astype
    with pytest.raises(ValueError):
        f.metadata(["level", "cfVarName", "centre"], astype=(int, None))


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_metadata_generic(mode):
    f_full = load_file_or_numpy_fs("tuv_pl.grib", mode)

    f = f_full[0:4]

    sn = f.metadata("shortName")
    assert sn == ["t", "u", "v", "t"]
    sn = f.metadata(["shortName"])
    assert sn == [["t"], ["u"], ["v"], ["t"]]
    lg = f.metadata("level", "cfVarName")
    assert lg == [(1000, "t"), (1000, "u"), (1000, "v"), (850, "t")]
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    lg = f.metadata("level", "cfVarName")
    assert lg == [(1000, "t"), (1000, "u"), (1000, "v"), (850, "t")]

    # single fieldlist
    f = f_full
    f = f.sel(param="t", level=1000)
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [[1000, "t"]]

    # single field
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))[0]
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [1000, "t"]


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_metadata_missing_value(mode):
    f = load_file_or_numpy_fs("ml_data.grib", mode, folder="data")

    with pytest.raises(KeyError):
        f[0].metadata("scaleFactorOfSecondFixedSurface")

    v = f[0].metadata("scaleFactorOfSecondFixedSurface", default=None)
    assert v is None


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_metadata_missing_key(mode):
    f = load_file_or_numpy_fs("test.grib", mode)

    with pytest.raises(KeyError):
        f[0].metadata("_badkey_")

    v = f[0].metadata("__badkey__", default=0)
    assert v == 0


@pytest.mark.parametrize("mode", ["file"])
def test_grib_metadata_namespace(mode):
    f = load_file_or_numpy_fs("test6.grib", mode)

    r = f[0].metadata(namespace="vertical")
    ref = {"level": 1000, "typeOfLevel": "isobaricInhPa"}
    assert r == ref

    r = f[0].metadata(namespace=["vertical", "time"])
    ref = {
        "vertical": {"typeOfLevel": "isobaricInhPa", "level": 1000},
        "time": {
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
    }
    assert r == ref

    # The number/order of metadata keys can vary with the ecCodes version.
    # The same is true for the namespaces.

    r = f[0].metadata(namespace=None)
    assert isinstance(r, dict)
    md_num = len(r)
    assert md_num > 100
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    r = f[0].metadata(namespace=[None])
    assert isinstance(r, dict)
    assert len(r) == md_num
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    r = f[0].metadata(namespace="")
    assert isinstance(r, dict)
    assert len(r) == md_num
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    r = f[0].metadata(namespace=[""])
    assert isinstance(r, dict)
    assert len(r) == md_num
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    ref = {
        "geography",
        "statistics",
        "vertical",
        "time",
        "parameter",
        "mars",
        "ls",
        "default",
    }
    r = f[0].metadata(namespace=all)
    assert isinstance(r, dict)
    assert set(r.keys()) == ref

    r = f[0].metadata(namespace=[all])
    assert isinstance(r, dict)
    assert set(r.keys()) == ref

    with pytest.raises(ValueError) as excinfo:
        r = f[0].metadata("level", namespace=["vertical", "time"])
    assert "must be a str when key specified" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        r = f[0].metadata("level", namespace=["vertical", "time"])
    assert "must be a str when key specified" in str(excinfo.value)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_datetime(mode):
    s = load_file_or_numpy_fs("test.grib", mode)

    ref = {
        "base_time": [datetime.datetime(2020, 5, 13, 12)],
        "valid_time": [datetime.datetime(2020, 5, 13, 12)],
    }
    assert s.datetime() == ref

    s = from_source(
        "dummy-source",
        kind="grib",
        paramId=[129, 130],
        date=[19900101, 19900102],
        level=[1000, 500],
    )
    ref = {
        "base_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
    }
    assert s.datetime() == ref


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_valid_datetime(mode):
    ds = load_file_or_numpy_fs("t_time_series.grib", mode, folder="data")
    f = ds[4]

    assert f.metadata("valid_datetime") == datetime.datetime(2020, 12, 21, 18)


@pytest.mark.parametrize("mode", ["file"])
def test_message(mode):
    f = load_file_or_numpy_fs("test.grib", mode)
    v = f[0].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"
    v = f[1].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
