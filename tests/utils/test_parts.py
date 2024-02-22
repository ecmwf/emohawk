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

from earthkit.data.sources.file import FileSourcePathAndParts
from earthkit.data.sources.url import UrlSourcePathAndParts
from earthkit.data.utils.parts import SimplePart


@pytest.mark.parametrize(
    "paths,parts,expected_paths,expected_parts",
    [
        ("a.grib", None, "a.grib", None),
        (["a.grib"], [None], "a.grib", None),
        ("a.grib", [None], "a.grib", None),
        (["a.grib", None], None, "a.grib", None),
        (["a.grib", [(0, 150)]], None, "a.grib", (SimplePart(0, 150),)),
        (["a.grib", (0, 150)], None, "a.grib", (SimplePart(0, 150),)),
        ("a.grib", [(0, 150)], "a.grib", (SimplePart(0, 150),)),
        ("a.grib", [(0, 150), (150, 100)], "a.grib", (SimplePart(0, 250),)),
        (
            "a.grib",
            [(0, 150), (160, 100)],
            "a.grib",
            (SimplePart(0, 150), SimplePart(160, 100)),
        ),
        (
            "a.grib",
            [(150, 100), (0, 150)],
            ("a.grib", "a.grib"),
            ((SimplePart(150, 100),), (SimplePart(0, 150),)),
        ),
        (["a.grib", "b.grib"], None, ["a.grib", "b.grib"], [None, None]),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150),), (SimplePart(0, 150),)),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], "b.grib"],
            None,
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150), SimplePart(200, 20)), None),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", (0, 100)]],
            None,
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150), SimplePart(200, 20)), ((SimplePart(0, 100),))),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100)]]],
            None,
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150), SimplePart(200, 20)), ((SimplePart(0, 100),))),
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100), (120, 50)]]],
            None,
            ("a.grib", "b.grib"),
            (
                (SimplePart(0, 150), SimplePart(200, 20)),
                ((SimplePart(0, 100), SimplePart(120, 50))),
            ),
        ),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            ("a.grib", "b.grib"),
            ((SimplePart(0, 150),), (SimplePart(0, 150),)),
        ),
    ],
)
def test_file_parts_prepare(paths, parts, expected_paths, expected_parts):
    p = FileSourcePathAndParts(paths, parts)
    res_paths, res_parts = p.path, p.parts
    assert res_paths == expected_paths
    assert res_parts == expected_parts


def test_file_parts_update_1():
    p = FileSourcePathAndParts("", None)
    assert p.path == ""
    assert p.parts is None

    p.update("a.grib")
    assert p.path == "a.grib"
    assert p.parts is None

    p.update(["a.grib", "b.grib"])
    assert p.path == ["a.grib", "b.grib"]
    assert p.parts == [None, None]


def test_file_parts_update_2():
    p = FileSourcePathAndParts("", None)
    assert p.path == ""
    assert p.parts is None

    p.update(["a.grib"])
    assert p.path == ["a.grib"]
    assert p.parts == [None]

    p.update("a.grib")
    assert p.path == "a.grib"
    assert p.parts is None


def test_file_parts_iter_1():
    p = FileSourcePathAndParts("a.grib", None)
    assert p.path == "a.grib"
    assert p.parts is None

    for pt, pr in p:
        pt == "a.grib"
        pr is None


def test_file_parts_iter_2():
    p = FileSourcePathAndParts(["a.grib", "b.grib"], None)
    assert p.path == ["a.grib", "b.grib"]
    assert p.parts == [None, None]

    ref_path = ["a.grib", "b.grib"]
    ref_parts = [None, None]

    i = 0
    for pt, pr in p:
        pt == ref_path[i]
        pr is ref_parts[i]
        i += 1


def test_file_parts_zipped_1():
    p = FileSourcePathAndParts("a.grib", None)
    assert p.path == "a.grib"
    assert p.parts is None
    assert p.zipped() == [("a.grib", None)]


def test_file_parts_zipped_2():
    p = FileSourcePathAndParts(["a.grib", "b.grib"], None)
    assert p.path == ["a.grib", "b.grib"]
    assert p.parts == [None, None]
    assert p.zipped() == [("a.grib", None), ("b.grib", None)]


@pytest.mark.parametrize(
    "urls,parts,expected_values",
    [
        ("a.grib", None, [("a.grib", None)]),
        (["a.grib", None], None, [("a.grib", None)]),
        (["a.grib", [(0, 150)]], None, [("a.grib", (SimplePart(0, 150),))]),
        (["a.grib", (0, 150)], None, [("a.grib", (SimplePart(0, 150),))]),
        ("a.grib", [(0, 150)], [("a.grib", (SimplePart(0, 150),))]),
        ("a.grib", [(0, 150), (150, 100)], [("a.grib", (SimplePart(0, 250),))]),
        (
            "a.grib",
            [(0, 150), (160, 100)],
            [("a.grib", (SimplePart(0, 150), SimplePart(160, 100)))],
        ),
        (
            "a.grib",
            [(150, 100), (0, 150)],
            [
                ("a.grib", ((SimplePart(150, 100),))),
                ("a.grib", ((SimplePart(0, 150),))),
            ],
        ),
        (["a.grib", "b.grib"], None, [("a.grib", None), ("b.grib", None)]),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            [("a.grib", (SimplePart(0, 150),)), ("b.grib", (SimplePart(0, 150),))],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], "b.grib"],
            None,
            [("a.grib", (SimplePart(0, 150), SimplePart(200, 20))), ("b.grib", None)],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", (0, 100)]],
            None,
            [
                ("a.grib", (SimplePart(0, 150), SimplePart(200, 20))),
                ("b.grib", (SimplePart(0, 100),)),
            ],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100)]]],
            None,
            [
                ("a.grib", (SimplePart(0, 150), SimplePart(200, 20))),
                ("b.grib", (SimplePart(0, 100),)),
            ],
        ),
        (
            [["a.grib", [(0, 150), (200, 20)]], ["b.grib", [(0, 100), (120, 50)]]],
            None,
            [
                ("a.grib", (SimplePart(0, 150), SimplePart(200, 20))),
                ("b.grib", (SimplePart(0, 100), SimplePart(120, 50))),
            ],
        ),
        (
            ["a.grib", "b.grib"],
            (0, 150),
            [
                ("a.grib", (SimplePart(0, 150),)),
                ("b.grib", (SimplePart(0, 150),)),
            ],
        ),
    ],
)
def test_url_parts_prepare(urls, parts, expected_values):
    p = UrlSourcePathAndParts(urls, parts)
    res = p.zipped()
    assert res == expected_values


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
