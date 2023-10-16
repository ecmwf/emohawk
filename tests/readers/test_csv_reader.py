#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import mimetypes

import pytest

from earthkit.data import from_source


def test_csv_1():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        lines=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )

    df = s.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ["a", "b", "c"]

    ds = s.to_xarray()
    assert len(ds) == 3
    assert list(ds.variables) == ["index", "a", "b", "c"]


def test_csv_2():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        lines=[
            [1, None, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )

    df = s.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ["a", "b", "c"]


def test_csv_3():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        lines=[
            [1, "x", 3],
            [4, "y", 6],
            [7, "z", 9],
        ],
    )

    df = s.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ["a", "b", "c"]


def test_csv_4():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        quote_strings=True,
        lines=[
            [1, "x", 3],
            [4, "y", 6],
            [7, "z", 9],
        ],
    )

    df = s.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ["a", "b", "c"]


def test_csv_5():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        quote_strings=True,
        lines=[
            [1, "x", 3],
            [4, "y", 6],
            [7, "z", 9],
        ],
    )

    df = s.to_pandas(pandas_read_csv_kwargs={"index_col": "a"})
    assert df.index.name == "a"


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_csv_icoads():
    r = {
        "class": "e2",
        "date": "1662-10-01/to/1663-12-31",
        "dataset": "icoads",
        "expver": "1608",
        "groupid": "17",
        "reportype": "16008",
        "format": "ascii",
        "stream": "oper",
        "time": "all",
        "type": "ofb",
    }

    source = from_source("mars", **r)
    print(source)


def test_csv_text_file():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        quote_strings=True,
        lines=[
            [1, "x", 3],
            [4, "y", 6],
            [7, "z", 9],
        ],
        extension=".txt",
    )

    df = s.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ["a", "b", "c"]


def test_csv_with_comment():
    s = from_source(
        "dummy-source",
        "csv",
        headers=["a", "b", "c"],
        quote_strings=True,
        lines=[
            [1, "x", 3],
            [4, "y", 6],
            [7, "z", 9],
        ],
        comment_line="This is a comment",
    )

    df = s.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ["a", "b", "c"]

    ds = s.to_xarray()
    assert len(ds) == 3
    assert list(ds.variables) == ["index", "a", "b", "c"]


def test_csv_mimetypes():
    assert mimetypes.guess_type("x.csv") == ("text/csv", None)
    assert mimetypes.guess_type("x.csv.gz") == ("text/csv", "gzip")
    assert mimetypes.guess_type("x.csv.bz2") == ("text/csv", "bzip2")


# TODO test compression

if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
