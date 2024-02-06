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
        ((0, 1596), ["02836"]),  # message length
        ([(0, 1596)], ["02836"]),  # message length
        ([(0, 1601)], ["02836"]),  # message length + extra bytes
        ([(2904, 1166)], ["01415"]),
        ([(0, 1596)], ["02836"]),  # shorter than message
        ([(2904, 2442)], ["01415", "01001"]),
        ([(2904, 1166), (5346, 1216)], ["01415", "01152"]),
        ([(2904, 1166), (5346, 121)], ["01415"]),  # second part shorter than message
    ],
)
def test_bufr_single_file_parts(parts, expected_meta):
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"), parts=parts)

    assert len(ds) == len(expected_meta)
    if len(ds) > 0:
        assert ds.metadata(("ident")) == expected_meta


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
