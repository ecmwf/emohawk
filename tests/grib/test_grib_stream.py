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


def test_grib_from_stream_invalid_args():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, order_by="level")

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by=1)

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by=["level", 1])

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by="level", batch_size=1)

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(ValueError):
            from_source("stream", stream, batch_size=-1)


@pytest.mark.parametrize("group_by", ["level", ["level", "gridType"]])
def test_grib_from_stream_group_by(group_by):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, group_by=group_by)

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


def test_grib_from_stream_single_batch():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream)

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


def test_grib_from_stream_multi_batch():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=2)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = [["t", "u"], ["v", "t"], ["u", "v"]]
        for i, f in enumerate(fs):
            assert len(f) == 2
            f.metadata("param") == ref[i]

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


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
