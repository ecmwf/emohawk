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
import itertools
import os
import sys

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from constants_fixtures import all_params  # noqa: E402


def test_constant_source_1():
    sample = from_source("file", earthkit_examples_file("test.grib"))

    start = sample[0].datetime()["valid_time"]
    first_step = 6
    last_step = 240
    step_increment = 6
    dates = []
    for step in range(first_step, last_step + step_increment, step_increment):
        dates.append(start + datetime.timedelta(hours=step))

    params = all_params

    ds = from_source(
        "constants",
        sample,
        date=dates,
        param=all_params,
    )

    num = len(params) * len(dates)
    assert len(ds) == num

    ref = [(d, p) for d, p in itertools.product(dates, params)]
    assert len(ds) == len(ref)
    for f, r in zip(ds, ref):
        assert f.metadata("valid_datetime") == r[0].isoformat()
        assert f.metadata("param") == r[1]


def test_constant_2():
    sample = from_source("file", earthkit_examples_file("test.grib"))

    start = sample[0].datetime()["valid_time"]
    start = datetime.datetime(start.year, start.month, start.day)
    first_step = 1
    last_step = 10
    step_increment = 1
    dates = []
    for step in range(first_step, last_step + step_increment, step_increment):
        dates.append(start + datetime.timedelta(days=step))

    params = all_params

    ntimes = 4
    ds = from_source(
        "constants",
        sample,
        date=dates,
        time=f"0/to/18/by/{24//ntimes}",
        param=params,
    )

    num = len(params) * len(dates) * 4
    assert len(ds) == num

    ref = [(d, p) for d, p in itertools.product(ds.dates, params)]
    assert len(ds) == len(ref)
    for f, r in zip(ds, ref):
        assert f.metadata("valid_datetime") == r[0].isoformat()
        assert f.metadata("param") == r[1]


def test_constant_3():
    sample = from_source("file", earthkit_test_data_file("t_time_series.grib"))

    dates = [
        datetime.datetime(2020, 12, 21, 12, 0),
        datetime.datetime(2020, 12, 21, 15, 0),
        datetime.datetime(2020, 12, 21, 18, 0),
        datetime.datetime(2020, 12, 21, 21, 0),
        datetime.datetime(2020, 12, 23, 12, 0),
    ]

    params = all_params

    ds = from_source(
        "constants",
        sample,
        param=params,
    )

    num = len(dates) * len(params)
    assert len(ds) == num

    ref = [(d, p) for d, p in itertools.product(dates, params)]
    assert len(ds) == len(ref)
    for f, r in zip(ds, ref):
        assert f.metadata("valid_datetime") == r[0].isoformat()
        assert f.metadata("param") == r[1]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
