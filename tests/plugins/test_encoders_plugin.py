#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import numpy as np
import pytest

from earthkit.data.core.temporary import temp_file
from earthkit.data.encoders import get_encoder
from earthkit.data.targets import to_target

NO_DEMO_ENCODER = True


@pytest.mark.skipif(NO_DEMO_ENCODER, reason="demo-encoder plugin not available")
@pytest.mark.plugin
def test_demo_encoder_plugin_1():
    with temp_file() as tmp:
        d = np.random.normal(0, 1, (10, 15))

        encoder = get_encoder("demo-encoder")
        assert encoder is not None

        d = encoder.encode(values=d)
        assert d is not None

        with open(tmp, "wb") as out:
            d.to_file(out)
        assert os.path.getsize(tmp) > 100


@pytest.mark.skipif(NO_DEMO_ENCODER, reason="demo-encoder plugin not available")
@pytest.mark.plugin
def test_demo_encoder_plugin_2():
    with temp_file() as tmp:
        d = np.random.normal(0, 1, (10, 15))
        to_target("file", tmp, values=d, encoder="demo-encoder")
        assert os.path.getsize(tmp) > 100


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
