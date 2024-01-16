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
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ([(0, 150)], [("t", 1000)]),
        ([(240, 150)], [("u", 1000)]),
        ([(240, 480)], [("u", 1000), ("v", 1000)]),
    ],
)
def test_grib_single_url_parts(parts, expected_meta):
    ds = from_source(
        "url", earthkit_remote_test_data_file("examples/test6.grib"), parts=parts
    )

    assert len(ds) == len(expected_meta)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)


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
    ],
)
def test_grib_multi_url_parts(parts1, parts2, expected_meta):
    ds = from_source(
        "url",
        [
            [earthkit_remote_test_data_file("examples/test6.grib"), parts1],
            [earthkit_remote_test_data_file("examples/test.grib"), parts2],
        ],
    )

    assert len(ds) == len(expected_meta)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
