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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ((0, 150), [("t", 1000)]),  # message length
        ([(0, 150)], [("t", 1000)]),  # message length
        ([(0, 154)], [("t", 1000)]),  # message length + extra bytes
        ([(0, 240)], [("t", 1000)]),  # message length + padding
        (
            [(0, 240)],
            [("t", 1000)],
        ),  # message length + padding + bytes from next message
        ([(0, 15)], []),  # shorter than message
        ([(240, 150)], [("u", 1000)]),
        ([(240, 480)], [("u", 1000), ("v", 1000)]),
        ([(240, 240), (720, 240)], [("u", 1000), ("t", 850)]),
        ([(240, 240), (720, 243)], [("u", 1000), ("t", 850)]),
        ([(240, 240), (720, 16)], [("u", 1000)]),  # second part shorter than message
    ],
)
def test_grib_single_file_parts(parts, expected_meta):
    ds = from_source("file", earthkit_examples_file("test6.grib"), parts=parts)

    assert len(ds) == len(expected_meta)
    if len(ds) > 0:
        assert ds.metadata(("param", "level")) == expected_meta


@pytest.mark.parametrize(
    "parts1,parts2,expected_meta",
    [
        (
            [(240, 150)],
            None,
            [("u", 1000), ("2t", 0), ("msl", 0)],
        ),
        (
            (240, 150),
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
    ],
)
def test_grib_multi_file_parts(parts1, parts2, expected_meta):
    ds = from_source(
        "file",
        [
            [earthkit_examples_file("test6.grib"), parts1],
            [earthkit_examples_file("test.grib"), parts2],
        ],
    )

    assert len(ds) == len(expected_meta)
    if len(ds) > 0:
        assert ds.metadata(("param", "level")) == expected_meta


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
