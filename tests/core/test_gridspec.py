#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from earthkit.data.paths import earthkit_conf_file

with open(earthkit_conf_file("gridspec_schema.json"), "r") as f:
    schema = json.load(f)


@pytest.mark.parametrize(
    "gridspec",
    [
        {"grid": [2, 2]},
        {"area": [90, -180, -90, 180]},
        {"area": [90, -180, -90, 180], "grid": [2, 2]},
        {"grid": 48},
        {"grid": "F48"},
        {"grid": "N48"},
        {"grid": "O48"},
        {"type": "regular_ll", "grid": [1, 2]},
        {"type": "regular_ll", "area": [90, -180, -90, 180]},
        {"type": "reduced_ll", "grid": 12},
        {"type": "regular_gg", "grid": 48},
        {"type": "regular_gg", "grid": "48"},
        {"type": "regular_gg", "grid": "F48"},
        {"type": "regular_gg", "grid": "F048"},
        {"type": "reduced_gg", "grid": "N48"},
        {"type": "reduced_gg", "grid": "N048"},
        {"type": "reduced_gg", "grid": "O48"},
        {"type": "reduced_gg", "grid": "O048"},
        {
            "type": "mercator",
            "area": [31.173058, 262.036499, 14.736453, 284.975281],
            "grid": [45000.0, 45000.0],
            "lad": 14.0,
            "nx": 56,
            "ny": 44,
            "orientation": 0.0,
        },
    ],
)
def test_gridspec_schema_valid(gridspec):
    validate(instance=gridspec, schema=schema)


@pytest.mark.parametrize(
    "gridspec",
    [
        {"type": "latlon", "grid": [2, 2]},
        {"type": "reduced_latlon", "grid": 2},
        {"grid": "B48"},
        {"type": "regular_ll", "grid": 48},
        {"type": "regular_ll", "grid": "F48"},
        {"type": "regular_ll", "grid": "a"},
        {"type": "regular_ll", "grid": ["a", "b"]},
        {"type": "regular_ll", "grid": [1]},
        {"type": "regular_ll", "grid": [1, 2, 3]},
        {"type": "regular_gg", "grid": "a"},
        {"type": "regular_gg", "grid": "N48"},
        {"type": "regular_gg", "grid": "O48"},
        {"type": "reduced_gg"},
        {"type": "reduced_gg", "grid": 48},
        {"type": "reduced_gg", "grid": "48"},
        {"type": "reduced_gg", "grid": "F048"},
        {"type": "reduced_gg", "grid": "N"},
    ],
)
def test_gridspec_schema_invalid(gridspec):
    with pytest.raises(ValidationError):
        validate(instance=gridspec, schema=schema)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
