#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from datetime import timedelta

import pytest

from earthkit.data.utils.dates import step_to_delta


@pytest.mark.parametrize(
    "step,expected_delta,error",
    [
        (12, timedelta(hours=12), None),
        ("12h", timedelta(hours=12), None),
        ("12s", timedelta(seconds=12), None),
        ("12m", timedelta(minutes=12), None),
        ("1m", timedelta(minutes=1), None),
        ("", None, ValueError),
        ("m", None, ValueError),
        ("1Z", None, ValueError),
        ("m1", None, ValueError),
        ("-1", None, ValueError),
        ("-1s", None, ValueError),
        ("1.1s", None, ValueError),
    ],
)
def test_step_to_delta(step, expected_delta, error):
    if error is None:
        assert step_to_delta(step) == expected_delta
    else:
        with pytest.raises(error):
            step_to_delta(step)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
