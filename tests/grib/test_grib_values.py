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

import numpy as np
import pytest

from earthkit.data.testing import (
    ARRAY_BACKENDS,
    check_array_type,
    get_array,
    get_array_namespace,
)

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES, load_grib_data  # noqa: E402


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
def test_grib_values_1(fl_type, backend):
    f = load_grib_data("test_single.grib", fl_type, backend, folder="data")
    eps = 1e-5

    # whole file
    v = f.values
    check_array_type(v, backend, dtype="float64")
    assert v.shape == (1, 84)
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )

    # field
    v1 = f[0].values

    check_array_type(v1, backend)
    assert v1.shape == (84,)
    assert np.allclose(v, v1, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
def test_grib_values_18(fl_type, backend):
    f = load_grib_data("tuv_pl.grib", fl_type, backend)
    eps = 1e-5

    # whole file
    v = f.values
    check_array_type(v, backend, dtype="float64")
    assert v.shape == (18, 84)
    vf = v[0].flatten()
    check_array(
        vf,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf = v[15].flatten()
    check_array(
        vf,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
def test_grib_to_numpy_1(fl_type, backend):
    f = load_grib_data("test_single.grib", fl_type, backend, folder="data")

    eps = 1e-5
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
@pytest.mark.parametrize(
    "first,options, expected_shape",
    [
        (False, {}, (1, 7, 12)),
        (False, {"flatten": True}, (1, 84)),
        (False, {"flatten": False}, (1, 7, 12)),
        (True, {}, (7, 12)),
        (True, {"flatten": True}, (84,)),
        (True, {"flatten": False}, (7, 12)),
    ],
)
def test_grib_to_numpy_1_shape(fl_type, backend, first, options, expected_shape):
    f = load_grib_data("test_single.grib", fl_type, backend, folder="data")

    v_ref = f[0].to_numpy().flatten()
    eps = 1e-5

    data = f[0] if first else f
    v1 = data.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.dtype == np.float64
    assert v1.shape == expected_shape
    v1 = v1.flatten()
    assert np.allclose(v_ref, v1, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
def test_grib_to_numpy_18(fl_type, backend):
    f = load_grib_data("tuv_pl.grib", fl_type, backend)

    eps = 1e-5

    # whole file
    v = f.to_numpy(flatten=True)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (18, 84)
    vf0 = v[0].flatten()
    check_array(
        vf0,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf15 = v[15].flatten()
    check_array(
        vf15,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
@pytest.mark.parametrize(
    "options, expected_shape",
    [
        (
            {},
            (
                18,
                7,
                12,
            ),
        ),
        (
            {"flatten": True},
            (
                18,
                84,
            ),
        ),
        ({"flatten": False}, (18, 7, 12)),
    ],
)
def test_grib_to_numpy_18_shape(fl_type, backend, options, expected_shape):
    f = load_grib_data("tuv_pl.grib", fl_type, backend)

    eps = 1e-5

    # whole file
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (18, 7, 12)
    vf0 = f[0].to_numpy().flatten()
    assert vf0.shape == (84,)
    vf15 = f[15].to_numpy().flatten()
    assert vf15.shape == (84,)

    v1 = f.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.dtype == np.float64
    assert v1.shape == expected_shape
    vr = v1[0].flatten()
    assert np.allclose(vf0, vr, eps)
    vr = v1[15].flatten()
    assert np.allclose(vf15, vr, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ["numpy"])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_numpy_1_dtype(fl_type, backend, dtype):
    f = load_grib_data("test_single.grib", fl_type, backend, folder="data")

    v = f[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = f.to_numpy(dtype=dtype)
    assert v.dtype == dtype


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ["numpy"])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_numpy_18_dtype(fl_type, backend, dtype):
    f = load_grib_data("tuv_pl.grib", fl_type, backend)

    v = f[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = f.to_numpy(dtype=dtype)
    assert v.dtype == dtype


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ["numpy"])
@pytest.mark.parametrize(
    "kwarg,expected_shape,expected_dtype",
    [
        ({}, (11, 19), np.float64),
        ({"flatten": True}, (209,), np.float64),
        ({"flatten": True, "dtype": np.float32}, (209,), np.float32),
        ({"flatten": True, "dtype": np.float64}, (209,), np.float64),
        ({"flatten": False}, (11, 19), np.float64),
        ({"flatten": False, "dtype": np.float32}, (11, 19), np.float32),
        ({"flatten": False, "dtype": np.float64}, (11, 19), np.float64),
    ],
)
def test_grib_field_data(fl_type, backend, kwarg, expected_shape, expected_dtype):
    ds = load_grib_data("test.grib", fl_type, backend)

    latlon = ds[0].to_latlon(**kwarg)
    v = ds[0].to_numpy(**kwarg)

    d = ds[0].data(**kwarg)
    assert isinstance(d, np.ndarray)
    assert d.dtype == expected_dtype
    assert len(d) == 3
    assert d[0].shape == expected_shape
    assert np.allclose(d[0], latlon["lat"])
    assert np.allclose(d[1], latlon["lon"])
    assert np.allclose(d[2], v)

    d = ds[0].data(keys="lat", **kwarg)
    assert d.shape == expected_shape
    assert d.dtype == expected_dtype
    assert np.allclose(d, latlon["lat"])

    d = ds[0].data(keys="lon", **kwarg)
    assert d.shape == expected_shape
    assert d.dtype == expected_dtype
    assert np.allclose(d, latlon["lon"])

    d = ds[0].data(keys="value", **kwarg)
    assert d.shape == expected_shape
    assert d.dtype == expected_dtype
    assert np.allclose(d, v)

    d = ds[0].data(keys=("value", "lon"), **kwarg)
    assert isinstance(d, np.ndarray)
    assert d.dtype == expected_dtype
    assert len(d) == 2
    assert np.allclose(d[0], v)
    assert np.allclose(d[1], latlon["lon"])


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ["numpy"])
@pytest.mark.parametrize(
    "kwarg,expected_shape,expected_dtype",
    [
        ({}, (11, 19), np.float64),
        ({"flatten": True}, (209,), np.float64),
        ({"flatten": True, "dtype": np.float32}, (209,), np.float32),
        ({"flatten": True, "dtype": np.float64}, (209,), np.float64),
        ({"flatten": False}, (11, 19), np.float64),
        ({"flatten": False, "dtype": np.float32}, (11, 19), np.float32),
        ({"flatten": False, "dtype": np.float64}, (11, 19), np.float64),
    ],
)
def test_grib_fieldlist_data(fl_type, backend, kwarg, expected_shape, expected_dtype):
    ds = load_grib_data("test.grib", fl_type, backend)

    latlon = ds.to_latlon(**kwarg)
    v = ds.to_numpy(**kwarg)

    d = ds.data(**kwarg)
    assert isinstance(d, np.ndarray)
    assert d.shape == tuple([4, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], latlon["lat"])
    assert np.allclose(d[1], latlon["lon"])
    assert np.allclose(d[2], v[0])
    assert np.allclose(d[3], v[1])

    d = ds.data(keys="lat", **kwarg)
    assert d.shape == tuple([1, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], latlon["lat"])

    d = ds.data(keys="lon", **kwarg)
    assert d.shape == tuple([1, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], latlon["lon"])

    d = ds.data(keys="value", **kwarg)
    assert d.shape == tuple([2, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d, v)

    d = ds.data(keys=("value", "lon"), **kwarg)
    assert isinstance(d, np.ndarray)
    assert d.shape == tuple([3, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], v[0])
    assert np.allclose(d[1], v[1])
    assert np.allclose(d[2], latlon["lon"])


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("backend", ARRAY_BACKENDS)
def test_grib_values_with_missing(fl_type, backend):
    f = load_grib_data("test_single_with_missing.grib", fl_type, backend, folder="data")

    v = f[0].values
    check_array_type(v, backend)
    assert v.shape == (84,)
    eps = 0.001

    ns = get_array_namespace(backend)

    assert ns.count_nonzero(ns.isnan(v)) == 38
    mask = get_array([12, 14, 15, 24, 25, 26] + list(range(28, 60)), backend)
    assert np.isclose(v[0], 260.4356, eps)
    assert np.isclose(v[11], 260.4356, eps)
    assert np.isclose(v[-1], 227.1856, eps)
    m = v[mask]
    assert len(m) == 38
    assert ns.count_nonzero(ns.isnan(m)) == 38


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
