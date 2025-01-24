#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file


def test_odb_to_pandas():
    ds = from_source("file", earthkit_examples_file("test.odb"))
    df = ds.to_pandas()
    assert len(df) == 717
    cols = [
        "lat",
        "lon",
        "fg_dep",
        "an_dep",
    ]
    assert list(df.columns) == cols
    assert np.allclose(df["lat"][0:2], [38.808998, 73.6931])
    assert np.allclose(df["lon"][0:2], [4.2926, -3.4167])
    assert np.allclose(df["fg_dep"][0:2], [0.514543, -0.098977])


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
