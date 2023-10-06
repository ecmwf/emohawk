#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from constants_fixtures import load_constants_fs  # noqa: E402


def test_constants_datetime():
    ds, _ = load_constants_fs(last_step=12)

    ref = {
        "base_time": [None],
        "valid_time": [
            datetime.datetime(2020, 5, 13, 18),
            datetime.datetime(2020, 5, 14, 0),
        ],
    }

    assert ds.datetime() == ref


def test_constants_valid_datetime():
    ds, _ = load_constants_fs(last_step=12)
    f = ds[4]

    assert f.metadata("valid_datetime") == "2020-05-13T18:00:00"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
