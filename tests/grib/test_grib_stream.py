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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


@pytest.mark.parametrize(
    "_kwargs,error",
    [
        (dict(order_by="level"), TypeError),
        (dict(group_by=1), TypeError),
        (dict(group_by=["level", 1]), TypeError),
        # (dict(group_by="level", batch_size=1), TypeError),
        (dict(batch_size=-1), ValueError),
    ],
)
def test_grib_from_stream_invalid_args(_kwargs, error):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(error):
            from_source("stream", stream, **_kwargs)


@pytest.mark.parametrize(
    "_kwargs",
    [
        {"group_by": "level"},
        {"group_by": "level", "batch_size": 0},
        {"group_by": "level", "batch_size": 1},
        {"group_by": ["level", "gridType"]},
    ],
)
def test_grib_from_stream_group_by(_kwargs):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, **_kwargs)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = [
            [("t", 1000), ("u", 1000), ("v", 1000)],
            [("t", 850), ("u", 850), ("v", 850)],
        ]
        for i, f in enumerate(fs):
            assert len(f) == 3
            assert f.metadata(("param", "level")) == ref[i]
            assert f.to_fieldlist("numpy") is not f

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


@pytest.mark.parametrize(
    "convert_kwargs,expected_shape",
    [
        ({}, (3, 7, 12)),
        (None, (3, 7, 12)),
        (None, (3, 7, 12)),
        ({"flatten": False}, (3, 7, 12)),
        ({"flatten": True}, (3, 84)),
    ],
)
def test_grib_from_stream_group_by_convert_to_numpy(convert_kwargs, expected_shape):
    group_by = "level"
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream, group_by=group_by)

        # no fieldlist methods are available on a StreamSource
        with pytest.raises(TypeError):
            len(ds)

        ref = [
            [("t", 1000), ("u", 1000), ("v", 1000)],
            [("t", 850), ("u", 850), ("v", 850)],
        ]

        if convert_kwargs is None:
            convert_kwargs = {}

        for i, f in enumerate(ds):
            df = f.to_fieldlist("numpy", **convert_kwargs)
            assert len(df) == 3
            assert df.metadata(("param", "level")) == ref[i]
            assert df._array.shape == expected_shape
            assert df.to_numpy(**convert_kwargs).shape == expected_shape
            assert df.to_fieldlist("numpy", **convert_kwargs) is df

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "_kwargs",
    [
        {},
        {"batch_size": 1},
    ],
)
def test_grib_from_stream_single_batch(_kwargs):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream, **_kwargs)

        # no fieldlist methods are available
        with pytest.raises(TypeError):
            len(ds)

        ref = [
            ("t", 1000),
            ("u", 1000),
            ("v", 1000),
            ("t", 850),
            ("u", 850),
            ("v", 850),
        ]

        for i, f in enumerate(ds):
            assert f.metadata(("param", "level")) == ref[i], i

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"batch_size": 3}, [["t", "u", "v"], ["t", "u", "v"]]),
        ({"batch_size": 4}, [["t", "u", "v", "t"], ["u", "v"]]),
    ],
)
def test_grib_from_stream_multi_batch(_kwargs, expected_meta):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream, **_kwargs)

        # no methods are available
        with pytest.raises(TypeError):
            len(ds)

        for i, f in enumerate(ds):
            assert len(f) == len(expected_meta[i])
            f.metadata("param") == expected_meta[i]

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "convert_kwargs,expected_shape",
    [
        ({}, (2, 7, 12)),
        (None, (2, 7, 12)),
        (None, (2, 7, 12)),
        ({"flatten": False}, (2, 7, 12)),
        (
            {"flatten": True},
            (
                2,
                84,
            ),
        ),
    ],
)
def test_grib_from_stream_multi_batch_convert_to_numpy(convert_kwargs, expected_shape):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream, batch_size=2)

        ref = [
            [("t", 1000), ("u", 1000)],
            [("v", 1000), ("t", 850)],
            [("u", 850), ("v", 850)],
        ]

        if convert_kwargs is None:
            convert_kwargs = {}

        for i, f in enumerate(ds):
            df = f.to_fieldlist("numpy", **convert_kwargs)
            assert df.metadata(("param", "level")) == ref[i], i
            assert df._array.shape == expected_shape, i
            assert df.to_numpy(**convert_kwargs).shape == expected_shape, i
            assert df.to_fieldlist("numpy", **convert_kwargs) is df, i

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


def test_grib_from_stream_in_memory():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source(
            "stream",
            stream,
            batch_size=0,
        )

        assert len(ds) == 6

        expected_shape = (6, 7, 12)
        md_ref = [
            ("t", 1000),
            ("u", 1000),
            ("v", 1000),
            ("t", 850),
            ("u", 850),
            ("v", 850),
        ]
        val = []

        # iteration
        for f in ds:
            v = f.metadata(("param", "level"))
            val.append(v)

        assert val == md_ref, "iteration"

        # metadata
        val = []
        val = ds.metadata(("param", "level"))
        assert val == md_ref, "method"

        # data
        assert ds.to_numpy().shape == expected_shape

        ref = np.array(
            [
                272.56417847,
                -6.28688049,
                7.83348083,
                272.53916931,
                -4.89837646,
                8.66096497,
            ]
        )

        vals = ds.to_numpy()[:, 0, 0]
        assert np.allclose(vals, ref)

        # slicing
        r = ds[0:3]
        assert len(r) == 3
        val = r.metadata(("param", "level"))
        assert val == md_ref[0:3]

        r = ds[-2:]
        assert len(r) == 2
        val = r.metadata(("param", "level"))
        assert val == md_ref[-2:]

        r = ds.sel(param="t")
        assert len(r) == 2
        val = r.metadata(("param", "level"))
        assert val == [
            ("t", 1000),
            ("t", 850),
        ]


@pytest.mark.parametrize(
    "convert_kwargs,expected_shape",
    [
        ({}, (6, 7, 12)),
        ({"flatten": False}, (6, 7, 12)),
        ({"flatten": True}, (6, 84)),
    ],
)
def test_grib_from_stream_in_memory_convert_to_numpy(convert_kwargs, expected_shape):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds_s = from_source(
            "stream",
            stream,
            batch_size=0,
        )

        ds = ds_s.to_fieldlist("numpy", **convert_kwargs)

        assert len(ds) == 6

        ref = ["t", "u", "v", "t", "u", "v"]
        val = []

        # iteration
        for f in ds:
            v = f.metadata("param")
            val.append(v)

        assert val == ref, "iteration"

        # metadata
        val = []
        val = ds.metadata("param")
        assert val == ref, "method"

        # data
        assert ds.to_numpy(**convert_kwargs).shape == expected_shape

        ref = np.array(
            [
                272.56417847,
                -6.28688049,
                7.83348083,
                272.53916931,
                -4.89837646,
                8.66096497,
            ]
        )

        if len(expected_shape) == 3:
            vals = ds.to_numpy(**convert_kwargs)[:, 0, 0]
        else:
            vals = ds.to_numpy(**convert_kwargs)[:, 0]

        assert np.allclose(vals, ref)
        assert ds._array.shape == expected_shape
        assert ds.to_fieldlist("numpy", **convert_kwargs) is ds


def test_grib_save_when_loaded_from_stream():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=0)
        assert len(fs) == 6
        with temp_file() as tmp:
            fs.save(tmp)
            fs_saved = from_source("file", tmp)
            assert len(fs) == len(fs_saved)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
