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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

all_params = [
    "latitude",
    "sin_latitude",
    "cos_latitude",
    "longitude",
    "sin_longitude",
    "cos_longitude",
    "local_time",
    "sin_local_time",
    "cos_local_time",
    "julian_day",
    "sin_julian_day",
    "cos_julian_day",
    "ecef_x",
    "ecef_y",
    "ecef_z",
    "toa_incident_solar_radiation",
    "cos_solar_zenith_angle",
]


def load_constants_fs(params=None, first_step=6, last_step=72):
    sample = from_source("file", earthkit_examples_file("test.grib"))

    if params is None:
        params = [
            "sin_latitude",
            "cos_latitude",
            "longitude",
            "sin_longitude",
            "cos_longitude",
            "local_time",
            "sin_local_time",
            "cos_local_time",
        ]

    start = sample[0].datetime()["valid_time"]
    step_increment = 6
    dates = []
    for step in range(first_step, last_step + step_increment, step_increment):
        dates.append(start + datetime.timedelta(hours=step))

    ds = from_source(
        "constants",
        sample,
        date=dates,
        param=params,
    )
    assert len(ds) == len(dates) * len(params)

    md = [[d.isoformat(), p] for d, p in itertools.product(dates, params)]
    return ds, md
