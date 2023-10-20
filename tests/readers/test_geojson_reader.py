#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_file


def test_geojson():
    s = from_source("file", earthkit_file("tests/data/NUTS_RG_20M_2021_3035.geojson"))
    assert s
    for _s in s:
        assert _s is not None
        assert _s.geometry


@pytest.mark.with_proj
def test_geojson_bounding_box():
    s = from_source("file", earthkit_file("tests/data/NUTS_RG_20M_2021_3035.geojson"))
    bb = s.bounding_box()
    assert bb
    assert bb.south, bb.north == (-90.0, 90.0)
    assert bb.east, bb.west == (-180.0, 180.0)


# TODO test mimetypes
# def test_csv_mimetypes():
# assert mimetypes.guess_type("x.geojson") == ("application/geo+json", None)
# assert mimetypes.guess_type("x.geojson.gz") == ("application/geo+json", "gzip")
# assert mimetypes.guess_type("x.geojson.bz2") == ("application/geo+json", "bzip2")


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
