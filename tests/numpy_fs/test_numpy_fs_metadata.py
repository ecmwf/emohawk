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
from numpy_fs_fixtures import load_numpy_fs, load_numpy_fs_file  # noqa: E402

# Note: Almost all grib metadata tests are also run for numpyfs.
# See grib/test_grib_metadata.py


def test_numpy_fs_values_metadata():
    ds, _ = load_numpy_fs(1)

    # values metadata
    keys = [
        "min",
        "max",
        "avg",
        "ds",
        "skew",
        "kurt",
        "isConstant",
        "const",
        "bitmapPresent",
        "numberOfMissing",
        "values",
    ]
    for k in keys:
        assert ds[0].metadata(k, default=None) is None, k
        with pytest.raises(KeyError):
            ds[0].metadata(k)


def test_numpy_fs_values_metadata_internal():
    ds, _ = load_numpy_fs(1)

    keys = {
        "shortName": "2t",
        "grib.shortName": "2t",
    }

    for k, v in keys.items():
        assert ds[0].metadata(k) == v, k


def test_numpy_fs_metadata_keys():
    ds, _ = load_numpy_fs(1)

    # The number/order of metadata keys can vary with the ecCodes version.
    # The same is true for the namespaces.

    md = ds[0].metadata()
    md_num = len(md)
    assert md_num > 100

    keys = md.keys()
    assert len(keys) == md_num

    for k in md.keys():
        assert isinstance(k, str)
        assert k != ""
        break

    items = md.items()
    assert len(items) == md_num

    for k, v in md.items():
        assert isinstance(k, str)
        assert k != ""
        assert v is not None
        break

    assert "max" not in md
    assert "maximum" not in md
    assert "statistics.max" not in md
    assert "validityDate" in md


def test_numpy_fs_metadata_namespace():
    f, _ = load_numpy_fs_file("tuv_pl.grib")

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


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
