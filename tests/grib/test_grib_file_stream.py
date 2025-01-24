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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_file
from earthkit.data.sources.stream import StreamFieldList
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import make_tgz
from earthkit.data.testing import write_to_file


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


def test_grib_file_stream_iter():
    ds = from_source(
        "file",
        earthkit_examples_file("test6.grib"),
        stream=True,
    )

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
    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == ref[i], i
        cnt += 1

    assert cnt == len(ref)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"n": 1}, [["t"], ["u"], ["v"], ["t"], ["u"], ["v"]]),
        ({"n": 3}, [["t", "u", "v"], ["t", "u", "v"]]),
        ({"n": 4}, [["t", "u", "v", "t"], ["u", "v"]]),
    ],
)
def test_grib_file_stream_batched(_kwargs, expected_meta):
    ds = from_source(
        "file",
        earthkit_examples_file("test6.grib"),
        stream=True,
    )

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


@pytest.mark.parametrize("group", ["level", ["level", "gridType"]])
def test_grib_file_stream_group_by(group):
    ds = from_source("file", earthkit_examples_file("test6.grib"), stream=True)

    # no methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    ref = [
        [("t", 1000), ("u", 1000), ("v", 1000)],
        [("t", 850), ("u", 850), ("v", 850)],
    ]
    cnt = 0
    for i, f in enumerate(ds.group_by(group)):
        assert len(f) == 3
        assert f.metadata(("param", "level")) == ref[i]
        assert f.to_fieldlist(array_backend="numpy") is not f
        cnt += 1

    assert cnt == len(ref)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_grib_file_stream_in_memory():
    ds = from_source(
        "file",
        earthkit_examples_file("test6.grib"),
        stream=True,
        read_all=True,
    )

    assert len(ds) == 6

    expected_shape = (6, 7, 12)
    ref = ["t", "u", "v", "t", "u", "v"]

    # iteration
    val = [f.metadata(("param")) for f in ds]
    assert val == ref, "iteration"

    # metadata
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


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_save_when_loaded_from_file_stream(write_method):
    ds = from_source(
        "file",
        earthkit_examples_file("test6.grib"),
        stream=True,
        read_all=True,
    )
    assert len(ds) == 6
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert len(ds) == len(ds_saved)


# @pytest.mark.parametrize(
#     "_kwargs",
#     [
#         {},
#         {"batch_size": 1},
#     ],
# )
def test_grib_file_stream_multi_file_iter():
    ds = from_source(
        "file",
        [
            earthkit_examples_file("test.grib"),
            earthkit_examples_file("test4.grib"),
        ],
        stream=True,
    )

    assert isinstance(ds, StreamFieldList)
    assert len(ds._source.sources) == 2

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
    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == ref[i], i
        cnt += 1

    assert cnt == len(ref)

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
def test_grib_file_stream_multi_file_batched(_kwargs, expected_meta):
    ds = from_source(
        "file",
        [
            earthkit_examples_file("test.grib"),
            earthkit_examples_file("test4.grib"),
        ],
        stream=True,
    )

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


def test_grib_file_stream_multi_file_memory():
    ds = from_source(
        "file",
        [
            earthkit_examples_file("test.grib"),
            earthkit_examples_file("test4.grib"),
        ],
        stream=True,
        read_all=True,
    )

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


@pytest.mark.cache
@pytest.mark.parametrize(
    "path,parts,expected_meta,remote",
    [
        ("test6.grib", [(0, 150)], [("t", 1000)], False),
        ("test6.grib", [(240, 150)], [("u", 1000)], False),
        ("test6.grib", [(240, 480)], [("u", 1000), ("v", 1000)], False),
        ("test-data/karl_850.grib", [(0, 1683960)], [("t", 850)], True),
        ("test-data/karl_850.grib", [(0, 3367920)], [("t", 850), ("r", 850)], True),
        ("test6.grib", [(240, 240), (720, 240)], [("u", 1000), ("t", 850)], False),
        ("test-data/karl_850.grib", [(0, 1683960), (3367920, 1683960)], [("t", 850), ("z", 850)], True),
    ],
)
def test_grib_file_stream_single_file_parts_core(path, parts, expected_meta, remote):
    if remote:
        ds0 = from_source(
            "url",
            earthkit_remote_test_data_file(path),
        )
        path = ds0.path

    ds = from_source(
        "file",
        earthkit_examples_file(path),
        parts=parts,
        stream=True,
    )

    # no fieldlist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ([(0, 150)], [("t", 1000)]),
        (
            None,
            [("t", 1000), ("u", 1000), ("v", 1000), ("t", 850), ("u", 850), ("v", 850)],
        ),
    ],
)
def test_grib_file_stream_single_file_parts_as_arg_valid(parts, expected_meta):
    ds = from_source(
        "file",
        [earthkit_examples_file("test6.grib"), parts],
        stream=True,
    )

    # no fieldlist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_grib_file_stream_single_file_parts_as_arg_invalid():
    with pytest.raises(ValueError):
        from_source(
            "file",
            [earthkit_examples_file("test6.grib"), [(0, 150)]],
            parts=[(0, 160)],
            stream=True,
        )


@pytest.mark.parametrize(
    "parts1,parts2,expected_meta",
    [
        (
            [(240, 150)],
            None,
            [("u", 1000), ("2t", 0), ("msl", 0)],
        ),
        (
            None,
            [(0, 526)],
            [
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
                ("2t", 0),
            ],
        ),
        (
            [(240, 150)],
            [(0, 526)],
            [("u", 1000), ("2t", 0)],
        ),
        (
            [(240, 150), (720, 150)],
            [(0, 526)],
            [("u", 1000), ("t", 850), ("2t", 0)],
        ),
    ],
)
def test_grib_file_stream_multi_file_parts(parts1, parts2, expected_meta):
    ds = from_source(
        "file",
        [
            [earthkit_examples_file("test6.grib"), parts1],
            [earthkit_examples_file("test.grib"), parts2],
        ],
        stream=True,
    )

    # no fieldlist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_file_stream_glob(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        write_to_file(write_method, os.path.join(tmpdir, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir, "b.grib"), s2)

        ds = from_source("file", os.path.join(tmpdir, "*a.grib"), stream=True)

        # no fieldlist methods are available
        with pytest.raises((TypeError, NotImplementedError)):
            len(ds)

        ref = [
            ("2t", 0),
            ("msl", 0),
        ]
        cnt = 0
        for i, f in enumerate(ds):
            assert f.metadata(("param", "level")) == ref[i], i
            cnt += 1

        assert cnt == len(ref)

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_file_stream_single_directory(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        write_to_file(write_method, os.path.join(tmpdir, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir, "b.grib"), s2)

        ds = from_source("file", tmpdir, stream=True)

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
        cnt = 0
        for i, f in enumerate(ds):
            assert f.metadata(("param", "level")) == ref[i], i
            cnt += 1

        assert cnt == len(ref)

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_file_stream_multi_directory(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        write_to_file(write_method, os.path.join(tmpdir1, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir1, "b.grib"), s2)

        with temp_directory() as tmpdir2:
            write_to_file(write_method, os.path.join(tmpdir2, "a.grib"), s1)
            write_to_file(write_method, os.path.join(tmpdir2, "b.grib"), s3)

            ds = from_source("file", [tmpdir1, tmpdir2], stream=True)

            ref = [
                ("2t", 0),
                ("msl", 0),
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("2t", 0),
                ("msl", 0),
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


@pytest.mark.parametrize("filter_kwarg", [(lambda x: "b.grib" in x), ("*b.grib")])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_file_stream_single_directory_filter(filter_kwarg, write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        write_to_file(write_method, os.path.join(tmpdir, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir, "b.grib"), s2)

        ds = from_source("file", tmpdir, filter=filter_kwarg, stream=True)

        ref = [
            ("t", 500),
            ("z", 500),
            ("t", 850),
            ("z", 850),
        ]

        cnt = 0
        for i, f in enumerate(ds):
            assert f.metadata(("param", "level")) == ref[i], i
            cnt += 1

        assert cnt == len(ref)

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("filter_kwarg", [(lambda x: "b.grib" in x), ("*b.grib")])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_file_stream_multi_directory_filter(filter_kwarg, write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        write_to_file(write_method, os.path.join(tmpdir1, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir1, "b.grib"), s2)

        with temp_directory() as tmpdir2:
            write_to_file(write_method, os.path.join(tmpdir2, "a.grib"), s1)
            write_to_file(write_method, os.path.join(tmpdir2, "b.grib"), s3)

            ds = from_source("file", [tmpdir1, tmpdir2], filter=filter_kwarg, stream=True)

            ref = [
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


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_file_stream_multi_directory_with_tar(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        write_to_file(write_method, os.path.join(tmpdir1, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir1, "b.grib"), s2)

        with temp_directory() as tmpdir2:
            write_to_file(write_method, os.path.join(tmpdir2, "a.grib"), s1)
            write_to_file(write_method, os.path.join(tmpdir2, "b.grib"), s3)

            paths = [os.path.join(tmpdir2, f) for f in ["a.grib", "b.grib"]]
            make_tgz(tmpdir2, "test.tar.gz", paths)

            ds = from_source("file", [tmpdir1, tmpdir2], stream=True)

            ref = [
                ("2t", 0),
                ("msl", 0),
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
                ("2t", 0),
                ("msl", 0),
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


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
