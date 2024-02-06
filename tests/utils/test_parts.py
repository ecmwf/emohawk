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

from earthkit.data.sources.file import FileSource
from earthkit.data.sources.url import Url
from earthkit.data.utils.parts import SimplePart


@pytest.mark.parametrize(
    "paths,parts,expected_paths,expected_parts",
    [
        ("a.grib", None, "a.grib", None),
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
def test_prepare_file_parts(paths, parts, expected_paths, expected_parts):
    res_paths, res_parts = FileSource._paths_and_parts(paths, parts)
    assert res_paths == expected_paths
    assert res_parts == expected_parts


@pytest.mark.parametrize(
    "urls,parts,expected_values",
    [
        ("a.grib", None, [["a.grib", None]]),
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
def test_prepare_url_parts(urls, parts, expected_values):
    res = Url._urls_and_parts(urls, parts)
    assert res == expected_values


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
