#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

from earthkit.data import from_object, from_source
from earthkit.data.testing import earthkit_examples_file

try:
    from earthkit.data.metadata import Metadata
except ImportError:
    Metadata = None

try:
    from earthkit.data.metadata import RawMetadata
except ImportError:
    RawMetadata = None

try:
    from earthkit.data.readers.grib.metadata import GribMetadata
except ImportError:
    GribMetadata = None


def test_abstract_metadata():
    # Metadata properties:
    # * immutable
    # * behaves like a dict
    # * can be updated (creating a new object, either a copy or a view)
    # Updates can be made with compatible subclasses, e.g. update a GribMetadata with a RawMetadata
    assert Metadata is not None


def test_raw_metadata():
    assert RawMetadata is not None
    assert issubclass(RawMetadata, Metadata)

    md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})
    assert md["shortName"] == "2t"
    assert md["perturbationNumber"] == 5
    assert md.get("shortName") == "2t"
    with pytest.raises(KeyError):
        md["nonExistentKey"]
    assert md.get("nonExistentKey", 12) == 12

    md2 = md.update({"centre": "ecmf", "perturbationNumber": 8})
    sentinel = object()
    assert md.get("centre", sentinel) is sentinel
    assert md["perturbationNumber"] == 5
    assert md2["shortName"] == "2t"
    assert md2["perturbationNumber"] == 8
    assert md2["centre"] == "ecmf"

    md3 = RawMetadata({"step": 24, "centre": "unknown"}).update(md2)
    assert md3["step"] == 24
    assert md3["centre"] == "ecmf"
    assert md3["shortName"] == "2t"


def test_grib_metadata():
    assert GribMetadata is not None
    assert issubclass(GribMetadata, Metadata)

    with pytest.raises(TypeError):
        GribMetadata({"shortName": "u", "typeOfLevel": "pl", "levelist": 1000})

    f = from_source("file", earthkit_examples_file("test_single.grib"))
    md = f[0].metadata()

    assert isinstance(md, GribMetadata)

    assert str(md["dataDate"]) == "20170427"
    assert md["shortName"] == "2t"

    extra = RawMetadata({"shortName": "2ta"})
    with pytest.raises(TypeError):
        extra.update(md)

    updated = md.update(extra)
    assert md["shortName"] == "2t"
    assert updated["shortName"] == "2ta"
    # When we write the GribMetadata, the GRIB keys should be set in the correct
    # order to produce the expected result


def test_build_from_object():
    arr = np.linspace(290.0, 300.0, 11)
    md = RawMetadata(
        {
            "date": 20200812,
            "time": 1200,
            "step": 0,
            "typeOfLevel": "surface",
            "shortName": "2t",
        }
    )
    f = from_object(arr, metadata=md)
    assert f.metadata()["date"] == 20200812
