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
from earthkit.data.sources.stream import StreamFieldList
from earthkit.data.testing import ARRAY_BACKENDS
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import write_to_file


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


# @pytest.mark.parametrize(
#     "_kwargs,error",
#     [
#         # (dict(order_by="level"), TypeError),
#         (dict(group_by=1), TypeError),
#         (dict(group_by=["level", 1]), TypeError),
#         # (dict(group_by="level", batch_size=1), TypeError),
#         (dict(batch_size=-1), ValueError),
#     ],
# )
# def test_grib_from_stream_invalid_args(_kwargs, error):
#     with open(earthkit_examples_file("test6.grib"), "rb") as stream:
#         with pytest.raises(error):
#             from_source("stream", stream, **_kwargs)


def test_grib_from_stream_iter():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream)

        # no fieldlist methods are available
        with pytest.raises((TypeError, NotImplementedError)):
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


# @pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
# def test_grib_from_stream_fieldlist_backend(array_backend):
#     with open(earthkit_examples_file("test6.grib"), "rb") as stream:
#         ds = from_source("stream", stream, array_backend=array_backend)


#         assert isinstance(ds, StreamFieldList)

#         # assert ds.array_backend.name == array_backend
#         assert ds.to_array().shape == (6, 7, 12)

#         assert sum([1 for _ in ds]) == 0

#         with pytest.raises((RuntimeError, ValueError)):
#             ds.to_array()


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"n": 1}, [["t"], ["u"], ["v"], ["t"], ["u"], ["v"]]),
        ({"n": 3}, [["t", "u", "v"], ["t", "u", "v"]]),
        ({"n": 4}, [["t", "u", "v", "t"], ["u", "v"]]),
    ],
)
def test_grib_from_stream_batched(_kwargs, expected_meta):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream)

        # no methods are available
        with pytest.raises((TypeError, NotImplementedError)):
            len(ds)

        for i, f in enumerate(ds.batched(_kwargs["n"])):
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
def test_grib_from_stream_batched_convert_to_numpy(convert_kwargs, expected_shape):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream)

        ref = [
            [("t", 1000), ("u", 1000)],
            [("v", 1000), ("t", 850)],
            [("u", 850), ("v", 850)],
        ]

        if convert_kwargs is None:
            convert_kwargs = {}

        for i, f in enumerate(ds.batched(2)):
            df = f.to_fieldlist(array_backend="numpy", **convert_kwargs)
            assert df.metadata(("param", "level")) == ref[i], i
            assert df.to_numpy(**convert_kwargs).shape == expected_shape, i
            df1 = df.to_fieldlist(array_backend="numpy", **convert_kwargs)
            assert df1 is not df, i
            assert df1.metadata(("param", "level")) == ref[i], i
            assert df1.to_numpy(**convert_kwargs).shape == expected_shape, i

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("group", ["level", ["level", "gridType"]])
def test_grib_from_stream_group_by(array_backend, group):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream)

        # no methods are available
        with pytest.raises((TypeError, NotImplementedError)):
            len(ds)

        ref = [
            [("t", 1000), ("u", 1000), ("v", 1000)],
            [("t", 850), ("u", 850), ("v", 850)],
        ]
        for i, f in enumerate(ds.group_by(group)):
            assert len(f) == 3
            assert f.metadata(("param", "level")) == ref[i]
            afl = f.to_fieldlist(array_backend=array_backend)
            assert afl is not f
            assert len(afl) == 3

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


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
    group = "level"
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source("stream", stream)

        # no fieldlist methods are available on a StreamSource
        with pytest.raises((TypeError, NotImplementedError)):
            len(ds)

        ref = [
            [("t", 1000), ("u", 1000), ("v", 1000)],
            [("t", 850), ("u", 850), ("v", 850)],
        ]

        if convert_kwargs is None:
            convert_kwargs = {}

        for i, f in enumerate(ds.group_by(group)):
            df = f.to_fieldlist(array_backend="numpy", **convert_kwargs)
            assert len(df) == 3
            assert df.metadata(("param", "level")) == ref[i]
            assert df.to_numpy(**convert_kwargs).shape == expected_shape
            df1 = df.to_fieldlist(array_backend="numpy", **convert_kwargs)
            assert df1 is not df
            assert len(df1) == 3
            assert df1.metadata(("param", "level")) == ref[i]
            assert df1.to_numpy(**convert_kwargs).shape == expected_shape

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


def test_grib_from_stream_in_memory():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        ds = from_source(
            "stream",
            stream,
            read_all=True,
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

        # iteration
        val = [f.metadata(("param", "level")) for f in ds]
        assert val == md_ref, "iteration"

        # metadata
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
        ds_s = from_source("stream", stream, read_all=True)

        ds = ds_s.to_fieldlist(array_backend="numpy", **convert_kwargs)

        assert len(ds) == 6

        ref = ["t", "u", "v", "t", "u", "v"]

        # iteration
        val = [f.metadata("param") for f in ds]
        assert val == ref, "iteration"

        # metadata
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
        assert ds.to_numpy(**convert_kwargs).shape == expected_shape
        ds1 = ds.to_fieldlist(array_backend="numpy", **convert_kwargs)
        assert ds1 is not ds
        assert len(ds1) == 6
        assert ds1.to_numpy(**convert_kwargs).shape == expected_shape


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_save_when_loaded_from_stream(write_method):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, read_all=True)
        assert len(fs) == 6
        with temp_file() as tmp:
            write_to_file(write_method, tmp, fs)
            fs_saved = from_source("file", tmp)
            assert len(fs) == len(fs_saved)


def test_grib_multi_from_stream_iter():
    stream1 = open(earthkit_examples_file("test.grib"), "rb")
    stream2 = open(earthkit_examples_file("test4.grib"), "rb")
    ds = from_source("stream", [stream1, stream2])

    assert isinstance(ds, StreamFieldList)

    # no fieldlist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    ref = [
        ("2t", 0),
        ("msl", 0),
        ("t", 500),
        ("z", 500),
        ("t", 850),
        ("z", 850),
    ]

    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == ref[i], i

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"n": 1}, [["2t"], ["msl"], ["t"], ["z"], ["t"], ["z"]]),
        ({"n": 2}, [["2t", "msl"], ["t", "z"], ["t", "z"]]),
        ({"n": 3}, [["2t", "msl", "t"], ["z", "t", "z"]]),
        ({"n": 4}, [["2t", "msl", "t", "z"], ["t", "z"]]),
    ],
)
def test_grib_multi_grib_from_stream_batched(_kwargs, expected_meta):
    stream1 = open(earthkit_examples_file("test.grib"), "rb")
    stream2 = open(earthkit_examples_file("test4.grib"), "rb")
    ds = from_source("stream", [stream1, stream2])

    assert isinstance(ds, StreamFieldList)

    # no methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds.batched(_kwargs["n"])):
        assert len(f) == len(expected_meta[i])
        f.metadata("param") == expected_meta[i]
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_grib_multi_stream_memory():
    stream1 = open(earthkit_examples_file("test.grib"), "rb")
    stream2 = open(earthkit_examples_file("test4.grib"), "rb")
    ds = from_source("stream", [stream1, stream2], read_all=True)

    assert len(ds) == 6

    md_ref = [
        ("2t", 0),
        ("msl", 0),
        ("t", 500),
        ("z", 500),
        ("t", 850),
        ("z", 850),
    ]
    # iteration
    val = [f.metadata(("param", "level")) for f in ds]
    assert val == md_ref, "iteration"

    # metadata
    val = ds.metadata(("param", "level"))
    assert val == md_ref, "method"

    # data
    with pytest.raises(ValueError):
        ds.to_numpy().shape

    # first part
    expected_shape = (2, 11, 19)
    assert ds[0:2].to_numpy().shape == expected_shape

    ref = np.array([262.78027344, 101947.8125])

    vals = ds[0:2].to_numpy()[:, 0, 0]
    assert np.allclose(vals, ref)

    # second part
    expected_shape = (4, 181, 360)
    assert ds[2:].to_numpy().shape == expected_shape

    ref = np.array([228.04600525, 48126.859375, 246.61032104, 11786.1132812])

    vals = ds[2:].to_numpy()[:, 0, 0]
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
        ("t", 500),
        ("t", 850),
    ]


def test_grib_concat_stream():
    stream1 = open(earthkit_examples_file("test.grib"), "rb")
    ds1 = from_source("stream", stream1)
    ds2 = from_source("file", earthkit_examples_file("test4.grib"), stream=True)
    ds3 = from_source("url", earthkit_remote_test_data_file("examples/test6.grib"), stream=True)

    ds = ds1 + ds2 + ds3

    ref = [
        ("2t", 0),
        ("msl", 0),
        ("t", 500),
        ("z", 500),
        ("t", 850),
        ("z", 850),
        ("t", 1000),
        ("u", 1000),
        ("v", 1000),
        ("t", 850),
        ("u", 850),
        ("v", 850),
    ]
    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == ref[i], i
        cnt += 1

    assert cnt == len(ref)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_grib_concat_stream_memory():
    stream1 = open(earthkit_examples_file("test.grib"), "rb")
    ds1 = from_source("stream", stream1, read_all=True)
    ds2 = from_source("file", earthkit_examples_file("test4.grib"), stream=True, read_all=True)
    ds3 = from_source(
        "url", earthkit_remote_test_data_file("examples/test6.grib"), stream=True, read_all=True
    )

    ds = ds1 + ds2 + ds3

    ref = [
        ("2t", 0),
        ("msl", 0),
        ("t", 500),
        ("z", 500),
        ("t", 850),
        ("z", 850),
        ("t", 1000),
        ("u", 1000),
        ("v", 1000),
        ("t", 850),
        ("u", 850),
        ("v", 850),
    ]

    assert len(ds) == len(ref)
    assert ds.metadata(("param", "level")) == ref

    # repeat the test to check that data is still in memory
    assert len(ds) == len(ref)
    assert ds.metadata(("param", "level")) == ref


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
