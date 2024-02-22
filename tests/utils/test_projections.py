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

from earthkit.data.utils import projections

NO_CARTOPY = False
try:
    import cartopy.crs as ccrs
except ImportError:
    NO_CARTOPY = True


def test_from_proj_string_laea():
    proj_string = "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs"
    projection = projections.Projection.from_proj_string(proj_string)
    assert isinstance(projection, projections.LambertAzimuthalEqualArea)
    assert projection.parameters == {
        "central_latitude": 52.0,
        "central_longitude": 10.0,
        "false_northing": 3210000.0,
        "false_easting": 4321000.0,
    }
    assert projection.globe == {
        "ellipse": "GRS80",
    }


def test_from_proj_string_lcc():
    proj_string = "+proj=lcc +lon_0=-90 +lat_1=33 +lat_2=45"
    projection = projections.Projection.from_proj_string(proj_string)
    assert isinstance(projection, projections.LambertConformal)
    assert projection.parameters == {
        "central_longitude": -90.0,
        "standard_parallels": (33.0, 45.0),
    }


def test_from_cf_grid_mapping_aea():
    grid_mapping = {
        "grid_mapping_name": "albers_conical_equal_area",
        "standard_parallel": 40,
        "longitude_of_central_meridian": 10,
    }
    projection = projections.Projection.from_cf_grid_mapping(**grid_mapping)
    assert isinstance(projection, projections.AlbersEqualArea)
    assert projection.parameters == {
        "central_longitude": 10,
        "standard_parallels": [40],
    }
    assert projection.globe == dict()


@pytest.mark.skipif(NO_CARTOPY, reason="cartopy is not installed")
def test_to_cartopy_crs_laea():
    proj_string = "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs"
    projection = projections.Projection.from_proj_string(proj_string)
    assert projection.to_cartopy_crs() == ccrs.LambertAzimuthalEqualArea(
        central_longitude=10.0,
        central_latitude=52.0,
        false_easting=4321000.0,
        false_northing=3210000.0,
        globe=ccrs.Globe(ellipse="GRS80"),
    )
