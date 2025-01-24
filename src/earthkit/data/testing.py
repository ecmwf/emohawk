# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import pathlib
import shutil
from contextlib import contextmanager
from importlib import import_module
from unittest.mock import patch

from earthkit.data import from_object
from earthkit.data import from_source
from earthkit.data.readers.text import TextReader
from earthkit.data.sources.empty import EmptySource
from earthkit.data.sources.mars import StandaloneMarsClient

LOG = logging.getLogger(__name__)


class OfflineError(Exception):
    pass


_NETWORK_PATCHER = patch("socket.socket", side_effect=OfflineError)

_REMOTE_TEST_DATA_URL = "https://get.ecmwf.int/repository/test-data/earthkit-data/"

_ROOT_DIR = top = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if not os.path.exists(os.path.join(_ROOT_DIR, "tests", "data")):
    _ROOT_DIR = "./"


@contextmanager
def network_off():
    try:
        _NETWORK_PATCHER.start()
        yield None
    finally:
        _NETWORK_PATCHER.stop()


@contextmanager
def preserve_cwd():
    current_dir = os.getcwd()
    try:
        yield None
    finally:
        os.chdir(current_dir)


def earthkit_remote_test_data_file(*args):
    return os.path.join(_REMOTE_TEST_DATA_URL, *args)


def earthkit_file(*args):
    return os.path.join(_ROOT_DIR, *args)


def earthkit_examples_file(*args):
    return os.path.join(_ROOT_DIR, "docs", "examples", *args)


def earthkit_test_data_file(*args):
    return os.path.join(_ROOT_DIR, "tests", "data", *args)


def data_file(*args):
    return os.path.join(os.path.dirname(__file__), "data", *args)


def file_url(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def data_file_url(*args):
    return file_url(data_file(*args))


def modules_installed(*modules):
    for module in modules:
        try:
            import_module(module)
        except ImportError:
            return False
    return True


NO_MARS_DIRECT = not StandaloneMarsClient.enabled()
NO_MARS_API = not os.path.exists(os.path.expanduser("~/.ecmwfapirc"))
NO_MARS = NO_MARS_API and NO_MARS_DIRECT

NO_CDS = not os.path.exists(os.path.expanduser("~/.cdsapirc"))
NO_HDA = not os.path.exists(os.path.expanduser("~/.hdarc"))
IN_GITHUB = os.environ.get("GITHUB_WORKFLOW") is not None
try:
    import ecmwf.opendata  # noqa

    NO_EOD = False
except Exception:
    NO_EOD = True

try:
    import pyfdb  # noqa

    NO_FDB = False
except Exception:
    NO_FDB = True

NO_PROD_FDB = NO_FDB
if not NO_PROD_FDB:
    fdb_home = os.environ.get("FDB_HOME", None)
    NO_PROD_FDB = fdb_home is None


NO_POLYTOPE = not os.path.exists(os.path.expanduser("~/.polytopeapirc"))
NO_COVJSONKIT = not modules_installed("covjsonkit")
NO_PYTORCH = not modules_installed("torch")
NO_RIOXARRAY = not modules_installed("rioxarray")
NO_CUPY = not modules_installed("cupy")
NO_JAX = not modules_installed("jax")
if not NO_CUPY:
    try:
        import cupy as cp

        a = cp.ones(2)
    except Exception:
        NO_CUPY = True

NO_S3_AUTH = not modules_installed("aws_requests_auth")
NO_GEO = not modules_installed("earthkit-data")
try:
    NO_ECFS = not os.path.exists(shutil.which("ecp"))
except Exception:
    NO_ECFS = True


def MISSING(*modules):
    return not modules_installed(*modules)


UNSAFE_SAMPLES_URL = "https://github.com/jwilk/traversal-archives/releases/download/0"


def empty(ds):
    LOG.debug("%s", ds)
    assert isinstance(ds, EmptySource)
    assert len(ds) == 0


def text(ds):
    LOG.debug("%s", ds)
    assert isinstance(ds._reader, TextReader)


UNSAFE_SAMPLES = (
    ("absolute1", empty),
    ("absolute2", empty),
    ("relative0", empty),
    ("relative2", empty),
    ("symlink", text),
    ("dirsymlink", text),
    ("dirsymlink2a", text),
    ("dirsymlink2b", text),
)


def check_unsafe_archives(extension):
    for archive, check in UNSAFE_SAMPLES:
        LOG.debug("%s.%s", archive, extension)
        ds = from_source("url", f"{UNSAFE_SAMPLES_URL}/{archive}{extension}")
        check(ds)


def load_nc_or_xr_source(path, mode):
    if mode == "nc":
        return from_source("file", path)
    else:
        import xarray

        return from_object(xarray.open_dataset(path))


def check_array_type(array, expected_backend, dtype=None):
    from earthkit.data.utils.array import get_backend

    b1 = get_backend(array)
    b2 = get_backend(expected_backend)

    assert b1 == b2, f"{b1=}, {b2=}"

    expected_dtype = dtype
    if expected_dtype is not None:
        assert b2.match_dtype(array, expected_dtype), f"{array.dtype}, {expected_dtype=}"


def get_array_namespace(backend):
    if backend is None:
        backend = "numpy"

    from earthkit.data.utils.array import get_backend

    return get_backend(backend).namespace


ARRAY_BACKENDS = ["numpy"]
if not NO_PYTORCH:
    ARRAY_BACKENDS.append("pytorch")

if not NO_CUPY:
    ARRAY_BACKENDS.append("cupy")


def make_tgz(target_dir, target_name, paths):
    import tarfile

    tar = tarfile.open(os.path.join(target_dir, target_name), "w:gz")
    for p in paths:
        tar.add(p)
    tar.close()


WRITE_TO_FILE_METHODS = ["target", "save", "write"]


def write_to_file(mode, path, ds, **kwargs):
    if mode == "target":
        bits_per_value = kwargs.pop("bits_per_value", None)
        md = kwargs.get("metadata", {})
        if bits_per_value is not None:
            md.update({"bitsPerValue": bits_per_value})
            kwargs["metadata"] = md

        ds.to_target("file", path, **kwargs)
    elif mode == "save":
        ds.save(path, **kwargs)
    elif mode == "write":
        append = kwargs.pop("append", False)
        flag = "wb" if not append else "ab"
        with open(path, flag) as f:
            ds.write(f, **kwargs)
    else:
        raise ValueError(f"Invalid {mode=}")


def main(path):
    import sys

    import pytest

    # Parallel does not work on darwin, gets RuntimeError: context has already been set
    # because pytest-parallel changes the context from `spawn` to `fork`

    args = ["-p", "no:parallel", "-E", "release"]

    if len(sys.argv) > 1 and sys.argv[1] == "--no-debug":
        args += ["-o", "log_cli=False"]
    else:
        logging.basicConfig(level=logging.DEBUG)
        args += ["-o", "log_cli=True"]

    args += [path]

    sys.exit(pytest.main(args))
