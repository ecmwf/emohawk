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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from constants_fixtures import load_constants_fs  # noqa: E402


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def test_contants_values():
    ds, md = load_constants_fs(last_step=12)
    eps = 1e-5
    num = len(ds)

    # whole file
    v = ds.values
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (num, 209)
    vf = v[0].flatten()
    check_array(
        vf,
        (209,),
        first=0.95630476,
        last=0.54463904,
        meanv=0.7793134730178092,
        eps=eps,
    )

    vf = v[num - 1].flatten()
    check_array(
        vf,
        (209,),
        first=0.89100652,
        last=0.70710678,
        meanv=0.917041819159978,
        eps=eps,
    )


def test_constants_to_numpy():
    ds, md = load_constants_fs(last_step=12)
    eps = 1e-5
    num = len(ds)

    # whole file
    v = ds.to_numpy(flatten=True)
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (num, 209)
    vf = v[0].flatten()
    check_array(
        vf,
        (209,),
        first=0.95630476,
        last=0.54463904,
        meanv=0.7793134730178092,
        eps=eps,
    )

    vf = v[num - 1].flatten()
    check_array(
        vf,
        (209,),
        first=0.89100652,
        last=0.70710678,
        meanv=0.917041819159978,
        eps=eps,
    )


@pytest.mark.parametrize(
    "options, expected_shape",
    [
        (
            {},
            (
                16,
                11,
                19,
            ),
        ),
        (
            {"flatten": True},
            (
                16,
                209,
            ),
        ),
        ({"flatten": False}, (16, 11, 19)),
    ],
)
def test_constants_to_numpy_shape(options, expected_shape):
    ds, _ = load_constants_fs(last_step=12)
    num = 16
    eps = 1e-5

    # whole file
    v = ds.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float64
    assert v.shape == (num, 11, 19)
    vf0 = ds[0].to_numpy().flatten()
    assert vf0.shape == (209,)
    vfm1 = ds[num - 1].to_numpy().flatten()
    assert vfm1.shape == (209,)

    v1 = ds.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.dtype == np.float64
    assert v1.shape == expected_shape
    vr = v1[0].flatten()
    assert np.allclose(vf0, vr, eps)
    vr = v1[num - 1].flatten()
    assert np.allclose(vfm1, vr, eps)


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_constants_to_numpy_dtype(dtype):
    ds, _ = load_constants_fs(last_step=12)

    v = ds[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = ds.to_numpy(dtype=dtype)
    assert v.dtype == dtype


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
def test_constants_field_data(kwarg, expected_shape, expected_dtype):
    ds, _ = load_constants_fs(params=["longitude"], last_step=12)

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
def test_constants_fieldlist_data(kwarg, expected_shape, expected_dtype):
    ds, _ = load_constants_fs(params=["longitude"], last_step=12)
    num = 2

    latlon = ds.to_latlon(**kwarg)
    v = ds.to_numpy(**kwarg)

    d = ds.data(**kwarg)
    assert isinstance(d, np.ndarray)
    assert d.shape == tuple([num + 2, *expected_shape])
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
    assert d.shape == tuple([num, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d, v)

    d = ds.data(keys=("value", "lon"), **kwarg)
    assert isinstance(d, np.ndarray)
    assert d.shape == tuple([num + 1, *expected_shape])
    assert d.dtype == expected_dtype
    assert np.allclose(d[0], v[0])
    assert np.allclose(d[1], v[1])
    assert np.allclose(d[2], latlon["lon"])


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
