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

from earthkit.data.geo import haversine_distance, nearest_point_haversine


def test_haversine_distance_single_point():
    p_ref = (48.0, 20)
    d_ref = 5675597.92279149
    p = (0, 0)
    d = haversine_distance(p_ref, p)
    assert np.isclose(d, d_ref)


@pytest.mark.parametrize("dlon_ref", [-720, -360, 0, 360, 720])
@pytest.mark.parametrize("dlon_p", [-720, -360, 0, 360, 720])
@pytest.mark.parametrize(
    "p_ref,d_ref",
    [
        (
            (0, 0),
            [
                0.0,
                10007903.11036912,
                10007903.11036912,
                20015806.22073824,
                10007903.11036912,
                10007903.11036912,
                5675597.92279149,
                5675597.92279149,
                5675597.92279149,
                5675597.92279149,
                np.nan,
            ],
        ),
        (
            (-90, 0),
            [
                10007903.11036912,
                10007903.11036912,
                10007903.11036912,
                10007903.11036912,
                20015806.22073824,
                0.0,
                15345451.43589932,
                15345451.43589932,
                4670354.78483892,
                4670354.78483892,
                np.nan,
            ],
        ),
        (
            (48.0, 20),
            [
                5675597.92279149,
                8536770.52794796,
                11479035.69279028,
                14340208.29794676,
                4670354.78483892,
                15345451.43589932,
                0.0,
                2942265.16484232,
                11351195.84558298,
                10675096.6510604,
                np.nan,
            ],
        ),
    ],
)
def test_haversine_distance(dlon_ref, dlon_p, p_ref, d_ref):
    lats = np.array([0.0, 0, 0, 0, 90, -90, 48, 48, -48, -48, np.nan])
    lons = np.array([0, 90, -90, 180, 0, 0, 20, -20, -20, 20, 1.0]) + dlon_p
    p_ref = (p_ref[0], p_ref[1] + dlon_ref)
    d_ref = np.array(d_ref)

    d = haversine_distance(p_ref, (lats, lons))
    assert np.allclose(
        d[:-1], d_ref[:-1]
    ), f"p_ref={p_ref},dlon_ref={dlon_ref},dlon_p={dlon_p}"


# lat is out of range
@pytest.mark.parametrize("p_ref", [((90.00001, 0)), (((-90.00001, 0)))])
def test_haversine_distance_invalid(p_ref):
    p = (-48, 12)
    d = haversine_distance(p_ref, p)
    assert np.isnan(d)


@pytest.mark.parametrize(
    "p_ref,index_ref",
    [
        ((0, 0), 0),
        ((15, 22), 0),
        ((44, 10), 6),
        ((44, -10), 7),
        ((89, -120), 4),
        ((-50, -18), 8),
        ((-50, 18), 9),
    ],
)
def test_haversine_nearest(p_ref, index_ref):
    lats = np.array([0.0, 0, 0, 0, 90, -90, 48, 48, -48, -48, np.nan])
    lons = np.array([0, 90, -90, 180, 0, 0, 20, -20, -20, 20, 1.0])

    index = nearest_point_haversine(p_ref, (lats, lons))
    assert index == index_ref, p_ref


def test_haversine_nearest_invalid():
    # p_ref must be a single point
    p_ref = ([15, 21], [22, 7])
    p = ([0.0, 0], [0, 90])

    with pytest.raises(ValueError):
        nearest_point_haversine(p_ref, p)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
