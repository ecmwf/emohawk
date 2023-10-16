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
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file


@pytest.mark.parametrize(
    "params",
    [
        {"shortName": "2t", "perturbationNumber": 5},
        [("shortName", "2t"), ("perturbationNumber", 5)],
        RawMetadata({"shortName": "2t", "perturbationNumber": 5}),
    ],
)
def test_raw_metadata_create(params):
    md = RawMetadata(params)
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5


def test_raw_metadata_create_with_kwarg():
    md = RawMetadata(shortName="2t", perturbationNumber=5)
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5


def test_raw_metadata_get():
    md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})

    assert len(md) == 2
    assert list(md.keys()) == ["shortName", "perturbationNumber"]
    assert [k for k in md] == ["shortName", "perturbationNumber"]
    assert {k: v for k, v in md.items()} == {"shortName": "2t", "perturbationNumber": 5}

    assert "shortName" in md
    assert "nonExistentKey" not in md

    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("shortName") == "2t"
    with pytest.raises(KeyError):
        md["nonExistentKey"]

    assert md.get("nonExistentKey") is None
    assert md.get("nonExistentKey", None) is None
    assert md.get("nonExistentKey", 12) == 12
    with pytest.raises(TypeError):
        md.get("centre", "shortName", "step")


@pytest.mark.parametrize(
    "params",
    [
        {"centre": "ecmf", "perturbationNumber": 8},
        [("centre", "ecmf"), ("perturbationNumber", 8)],
        RawMetadata({"centre": "ecmf", "perturbationNumber": 8}),
    ],
)
def test_raw_metadata_override(params):
    md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("centre", None) is None

    md2 = md.override(params)
    assert id(md2) != id(md)
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("centre", None) is None
    assert md2["shortName"] == "2t"
    assert md2["perturbationNumber"] == 8
    assert md2["centre"] == "ecmf"


def test_raw_metadata_override_with_kwarg():
    md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("centre", None) is None

    md2 = md.override(centre="ecmf", perturbationNumber=8)
    assert id(md2) != id(md)
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("centre", None) is None
    assert md2["shortName"] == "2t"
    assert md2["perturbationNumber"] == 8
    assert md2["centre"] == "ecmf"


def test_grib_metadata_create():
    f = from_source("file", earthkit_examples_file("test.grib"))
    md = f[0].metadata()
    assert isinstance(md, GribMetadata)

    # cannot create from dict
    with pytest.raises(TypeError):
        GribMetadata({"shortName": "u", "typeOfLevel": "pl", "levelist": 1000})

    # cannot create from raw metadata
    raw_md = RawMetadata({"shortName": "u", "typeOfLevel": "pl", "levelist": 1000})
    with pytest.raises(TypeError):
        GribMetadata(raw_md)


def test_grib_metadata_get():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds[0].metadata()

    # the number/order of metadata keys can vary with the ecCodes version
    md_num = len(md)
    assert md_num > 100

    keys = list(md.keys())
    assert len(keys) == md_num
    assert "shortName" in keys
    assert "maximum" in keys

    keys = [k for k in md]
    assert len(keys) == md_num
    assert "shortName" in keys
    assert "maximum" in keys

    items = {k: v for k, v in md.items()}
    assert len(items) == md_num
    assert items["shortName"] == "2t"
    assert items["typeOfLevel"] == "surface"

    assert "shortName" in md
    assert "nonExistentKey" not in md

    assert md["shortName"] == "2t"
    assert md["typeOfLevel"] == "surface"
    assert md.get("shortName") == "2t"

    with pytest.raises(KeyError):
        md["nonExistentKey"]

    assert md.get("nonExistentKey") is None
    assert md.get("nonExistentKey", None) is None
    assert md.get("nonExistentKey", 12) == 12

    sentinel = object()
    assert md.get("nonExistentKey", sentinel) is sentinel

    with pytest.raises(TypeError):
        md.get("centre", "shortName", "step")


def test_grib_grib_metadata_valid_datetime():
    ds = from_source("file", earthkit_test_data_file("t_time_series.grib"))
    md = ds[4].metadata()

    assert md["valid_datetime"] == datetime.datetime(2020, 12, 21, 18)


def test_grib_metadata_override():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds[0].metadata()

    md2 = md.override({"perturbationNumber": 5})
    assert id(md2) != id(md)
    assert md["perturbationNumber"] == 0
    assert md2["perturbationNumber"] == 5

    md2 = md.override({"shortName": "2d"})
    assert md["shortName"] == "2t"
    assert md2["shortName"] == "2d"

    md2 = md.override({"perturbationNumber": 5, "shortName": "2d"})
    assert md["perturbationNumber"] == 0
    assert md["shortName"] == "2t"
    assert md2["perturbationNumber"] == 5
    assert md2["shortName"] == "2d"

    md3 = md2.override({"step": 24})
    assert md["step"] == 0
    assert md2["step"] == 0
    assert md3["step"] == 24

    # all the handles should exist and be different
    assert md._handle._handle is not None
    assert md2._handle._handle is not None
    assert md3._handle._handle is not None
    assert md._handle._handle != md2._handle._handle
    assert md2._handle._handle != md3._handle._handle
    assert md._handle._handle != md3._handle._handle

    md = None
    assert md2._handle._handle is not None
    assert md3._handle._handle is not None


@pytest.mark.parametrize(
    "params",
    [
        {"perturbationNumber": 5, "shortName": "2d"},
        [("perturbationNumber", 5), ("shortName", "2d")],
        RawMetadata({"perturbationNumber": 5, "shortName": "2d"}),
    ],
)
def test_grib_metadata_override_1(params):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds[0].metadata()
    assert md["perturbationNumber"] == 0
    assert md["shortName"] == "2t"

    md2 = md.override(params)
    assert id(md2) != id(md)
    assert md["perturbationNumber"] == 0
    assert md["shortName"] == "2t"
    assert md2["perturbationNumber"] == 5
    assert md2["shortName"] == "2d"


def test_grib_metadata_override_with_kwarg():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds[0].metadata()
    assert md["perturbationNumber"] == 0
    assert md["shortName"] == "2t"

    md2 = md.override(perturbationNumber=5, shortName="2d")
    assert id(md2) != id(md)
    assert md["perturbationNumber"] == 0
    assert md["shortName"] == "2t"
    assert md2["perturbationNumber"] == 5
    assert md2["shortName"] == "2d"


def test_grib_metadata_override_invalid():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds[0].metadata()

    # invalid key
    with pytest.raises(Exception) as e:
        md.override({"__invalidkey": 5})
    assert "KeyValueNotFoundError" in e.typename

    # invalid value
    with pytest.raises(Exception) as e:
        md.override({"level": -100})
    assert "EncodingError" in e.typename


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
