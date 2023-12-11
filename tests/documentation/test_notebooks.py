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
import re
import sys

import pytest

from earthkit.data.testing import MISSING, earthkit_file

# See https://www.blog.pythonlibrary.org/2018/10/16/testing-jupyter-notebooks/


EXAMPLES = earthkit_file("docs", "examples")

SKIP = [
    "fdb.ipynb",
    "mars.ipynb",
    "cds.ipynb",
    "ads.ipynb",
    "wekeo.ipynb",
    "polytope.ipynb",
    "grib_fdb_write.ipynb",
    "demo_source_plugin.ipynb",
]


def notebooks_list():
    notebooks = []
    for path in os.listdir(EXAMPLES):
        if re.match(r".+\.ipynb$", path):
            # if re.match(r"^\d\d-.*\.ipynb$", path):
            if "Copy" not in path:
                notebooks.append(path)

    return sorted(notebooks)


@pytest.mark.notebook
@pytest.mark.skipif(
    MISSING("nbformat", "nbconvert", "ipykernel"),
    reason="python package nbformat not installed",
)
# @pytest.mark.skipif(not IN_GITHUB, reason="Not on GITHUB")
@pytest.mark.skipif(
    sys.platform == "win32", reason="Cannot execute notebooks on Windows"
)
@pytest.mark.parametrize("path", notebooks_list())
def test_notebook(path):
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    if path in SKIP:
        pytest.skip("Notebook marked as 'skip'")

    with open(os.path.join(EXAMPLES, path)) as f:
        nb = nbformat.read(f, as_version=4)

    proc = ExecutePreprocessor(timeout=60 * 60 * 5, kernel_name="python3")
    proc.preprocess(nb, {"metadata": {"path": EXAMPLES}})


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
