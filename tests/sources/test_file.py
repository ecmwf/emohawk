#!/usr/bin/env python3

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

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import make_tgz
from earthkit.data.testing import preserve_cwd
from earthkit.data.testing import write_to_file

LOG = logging.getLogger(__name__)


def test_file_source_grib():
    from earthkit.data.readers.grib.file import GRIBReader

    s = from_source("file", earthkit_examples_file("test.grib"))

    assert isinstance(s, GRIBReader), s
    assert len(s) == 2


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_source_grib_save(write_method):
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.grib")))
    with temp_directory() as tmpdir:
        # Check file save to assigned filename
        f_tmp = os.path.join(tmpdir, "test2.grib")
        write_to_file(write_method, f_tmp, ds)
        assert os.path.isfile(f_tmp)
        # Check file can be saved in current dir with detected filename:
        with preserve_cwd():
            os.chdir(tmpdir)
            write_to_file(write_method, f_tmp, ds)
            ds.save()
            assert os.path.isfile("test.grib")


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_source_grib_no_overwrite(write_method):
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.grib")))
    with temp_directory() as tmpdir:
        with preserve_cwd():
            os.chdir(tmpdir)
            # Save the file locally
            write_to_file(write_method, "test.grib", ds)
            # Open the local file
            ds1 = from_source("file", "test.grib")
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite the file we are currently reading",
            ):
                write_to_file(write_method, "test.grib", ds1)
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite the file we are currently reading",
            ):
                ds1.save()


def test_file_source_netcdf():
    s = from_source("file", earthkit_examples_file("test.nc"))
    assert len(s) == 2


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_source_netcdf_save(write_method):
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.nc")))
    with temp_directory() as tmpdir:
        # Check file save to assigned filename
        f_tmp = os.path.join(tmpdir, "test2.nc")
        write_to_file(write_method, f_tmp, ds)
        assert os.path.isfile(f_tmp)
        # Check file can be saved in current dir with detected filename:
        with preserve_cwd():
            os.chdir(tmpdir)
            ds.save()
            assert os.path.isfile("test.nc")


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_source_netcdf_no_overwrite(write_method):
    ds = from_source("file", os.path.abspath(earthkit_examples_file("test.nc")))
    with temp_directory() as tmpdir:
        with preserve_cwd():
            os.chdir(tmpdir)
            # Save the file locally
            write_to_file(write_method, "test.nc", ds)
            # Open the local file
            ds1 = from_source("file", "test.nc")
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite the file we are currently reading",
            ):
                write_to_file(write_method, "test.nc", ds1)
            with pytest.warns(
                UserWarning,
                match="Earthkit refusing to overwrite the file we are currently reading",
            ):
                ds1.save()


def test_file_source_odb():
    s = from_source("file", earthkit_examples_file("test.odb"))
    assert s.path == earthkit_examples_file("test.odb")


# def test_user_1():
#     s = from_source("file", earthkit_file("docs/examples/test.grib"))
#     home_file = os.path.expanduser("~/.earthkit_data/test.grib")
#     try:
#         s.save(home_file)
#         # Test expand user
#         s = from_source("file", "~/.earthkit_data/test.grib")
#         assert len(s) == 2
#     finally:
#         try:
#             os.unlink(home_file)
#         except OSError:
#             LOG.exception("unlink(%s)", home_file)


# @pytest.mark.skipif(
#     sys.platform == "win32", reason="Cannot (yet) use expandvars on Windows"
# )
# def test_user_2():
#     s = from_source("file", earthkit_file("docs/examples/test.grib"))
#     home_file = os.path.expanduser("~/.earthkit_data/test.grib")
#     try:
#         s.save(home_file)
#         # Test expand vars
#         s = from_source("file", "$HOME/.earthkit_data/test.grib", expand_vars=True)
#         assert len(s) == 2
#     finally:
#         try:
#             os.unlink(home_file)
#         except OSError:
#             LOG.exception("unlink(%s)", home_file)


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_glob(write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    with temp_directory() as tmpdir:
        write_to_file(write_method, os.path.join(tmpdir, "a.grib"), ds)
        write_to_file(write_method, os.path.join(tmpdir, "b.grib"), ds)

        ds = from_source("file", os.path.join(tmpdir, "*.grib"))
        assert len(ds) == 4, len(ds)

        ds = from_source("file", tmpdir)
        assert len(ds) == 4, len(ds)


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_single_directory(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        write_to_file(write_method, os.path.join(tmpdir, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir, "b.grib"), s2)

        ds = from_source("file", tmpdir)
        assert len(ds) == 6, len(ds)

        ref = [
            ("2t", 0),
            ("msl", 0),
            ("t", 500),
            ("z", 500),
            ("t", 850),
            ("z", 850),
        ]
        assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_multi_directory(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        write_to_file(write_method, os.path.join(tmpdir1, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir1, "b.grib"), s2)

        with temp_directory() as tmpdir2:
            write_to_file(write_method, os.path.join(tmpdir2, "a.grib"), s1)
            write_to_file(write_method, os.path.join(tmpdir2, "b.grib"), s3)

            ds = from_source("file", [tmpdir1, tmpdir2])
            assert len(ds) == 14, len(ds)

            ref = [
                ("2t", 0),
                ("msl", 0),
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
            ]

            assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize("filter_kwarg", [(lambda x: "b.grib" in x), ("*b.grib")])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_single_directory_filter(filter_kwarg, write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    with temp_directory() as tmpdir:
        write_to_file(write_method, os.path.join(tmpdir, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir, "b.grib"), s2)

        ds = from_source("file", tmpdir, filter=filter_kwarg)
        assert len(ds) == 4, len(ds)

        ref = [
            ("t", 500),
            ("z", 500),
            ("t", 850),
            ("z", 850),
        ]
        assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize("filter_kwarg", [(lambda x: "b.grib" in x), ("*b.grib")])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_multi_directory_filter(filter_kwarg, write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        write_to_file(write_method, os.path.join(tmpdir1, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir1, "b.grib"), s2)

        with temp_directory() as tmpdir2:
            write_to_file(write_method, os.path.join(tmpdir2, "a.grib"), s1)
            write_to_file(write_method, os.path.join(tmpdir2, "b.grib"), s3)

            ds = from_source("file", [tmpdir1, tmpdir2], filter=filter_kwarg)
            assert len(ds) == 10, len(ds)

            ref = [
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
            ]

            assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_file_multi_directory_with_tar(write_method):
    s1 = from_source("file", earthkit_examples_file("test.grib"))
    s2 = from_source("file", earthkit_examples_file("test4.grib"))
    s3 = from_source("file", earthkit_examples_file("test6.grib"))
    with temp_directory() as tmpdir1:
        write_to_file(write_method, os.path.join(tmpdir1, "a.grib"), s1)
        write_to_file(write_method, os.path.join(tmpdir1, "b.grib"), s2)

        with temp_directory() as tmpdir2:
            write_to_file(write_method, os.path.join(tmpdir2, "a.grib"), s1)
            write_to_file(write_method, os.path.join(tmpdir2, "b.grib"), s3)

            paths = [os.path.join(tmpdir2, f) for f in ["a.grib", "b.grib"]]
            make_tgz(tmpdir2, "test.tar.gz", paths)

            ds = from_source("file", [tmpdir1, tmpdir2])
            assert len(ds) == 22, len(ds)

            ref = [
                ("2t", 0),
                ("msl", 0),
                ("t", 500),
                ("z", 500),
                ("t", 850),
                ("z", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
                ("2t", 0),
                ("msl", 0),
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
            ]

            assert ds.metadata(("param", "level")) == ref


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
