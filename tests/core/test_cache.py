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

import pytest

from earthkit.data import cache, from_source, settings
from earthkit.data.core.caching import cache_file
from earthkit.data.core.temporary import temp_directory
from earthkit.data.testing import earthkit_examples_file


def check_cache_files(dir_path):
    def touch(target, args):
        assert args["foo"] in (1, 2)
        with open(target, "w"):
            pass

        path1 = cache_file(
            "test_cache",
            touch,
            {"foo": 1},
            extension=".test",
        )

        path2 = cache_file(
            "test_cache",
            touch,
            {"foo": 2},
            extension=".test",
        )

        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert os.path.dirname(path1) == dir_path
        assert os.path.dirname(path1) == dir_path
        assert path1 != path2

        cnt = 0
        for f in cache.cache_entries():
            if f["owner"] == "test_cache":
                cnt += 1

        assert cnt == 2


def test_cache_1():
    with settings.temporary():
        settings.set("maximum-cache-disk-usage", "99%")
        cache.purge_cache(matcher=lambda e: ["owner"] == "test_cache")
        check_cache_files(settings.get("user-cache-directory"))


# 1GB ram disk on MacOS (blocks of 512 bytes)
# diskutil erasevolume HFS+ "RAMDisk" `hdiutil attach -nomount ram://2097152`
@pytest.mark.skipif(not os.path.exists("/Volumes/RAMDisk"), reason="No RAM disk")
def test_cache_4():
    with settings.temporary():
        settings.set("cache-directory", "/Volumes/RAMDisk/earthkit_data")
        settings.set("maximum-cache-disk-usage", "90%")
        for n in range(10):
            from_source("dummy-source", "zeros", size=100 * 1024 * 1024, n=n)


def test_cache_policy():
    with temp_directory() as user_dir:
        # cache = user dir
        with settings.temporary():
            settings.set({"cache-policy": "user", "user-cache-directory": user_dir})
            assert settings.get("cache-policy") == "user"
            assert settings.get("user-cache-directory") == user_dir
            assert cache.policy.has_cache() is True
            cache_dir = cache.policy.cache_directory()
            assert cache_dir == user_dir
            assert os.path.exists(cache_dir)
            check_cache_files(cache_dir)

            # cache = temporary with auto generated path
            with settings.temporary(
                {"cache-policy": "temporary", "temporary-cache-directory-root": None}
            ):
                assert settings.get("cache-policy") == "temporary"
                assert settings.get("temporary-cache-directory-root") is None
                assert cache.policy.has_cache() is True
                cache_dir = cache.policy.cache_directory()
                assert os.path.exists(cache_dir)
                check_cache_files(cache_dir)

            # cache = user dir (again)
            assert settings.get("cache-policy") == "user"
            assert settings.get("user-cache-directory") == user_dir
            assert cache.policy.has_cache() is True
            cache_dir = cache.policy.cache_directory()
            assert cache_dir == user_dir
            assert os.path.exists(cache_dir)
            check_cache_files(cache_dir)

            # cache = temporary with user defined root path
            with temp_directory() as root_dir:
                with settings.temporary(
                    {
                        "cache-policy": "temporary",
                        "temporary-cache-directory-root": root_dir,
                    }
                ):
                    assert settings.get("cache-policy") == "temporary"
                    assert settings.get("temporary-cache-directory-root") == root_dir
                    assert cache.policy.has_cache() is True
                    cache_dir = cache.policy.cache_directory()
                    assert os.path.exists(cache_dir)
                    os.path.dirname(cache_dir) == root_dir
                    check_cache_files(cache_dir)

            # cache = off
            with settings.temporary("cache-policy", "off"):
                assert settings.get("cache-policy") == "off"
                assert settings.get("user-cache-directory") == user_dir
                assert cache.policy.has_cache() is False
                assert cache.policy.cache_directory() is None

                with pytest.raises(RuntimeError):
                    cache_file(
                        "dummy_test_cache",
                        None,
                        {"foo": 1},
                        extension=".test",
                    )

            # cache = user dir (again)
            assert settings.get("cache-policy") == "user"
            assert settings.get("user-cache-directory") == user_dir
            assert cache.policy.has_cache() is True
            cache_dir = cache.policy.cache_directory()
            assert cache_dir == user_dir
            assert os.path.exists(cache_dir)
            check_cache_files(cache_dir)


def test_url_source_no_cache():
    with settings.temporary("cache-policy", "off"):
        with pytest.raises(RuntimeError):
            from_source(
                "url",
                "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test.grib",
            )


def test_grib_no_cache():
    with settings.temporary("cache-policy", "off"):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        f = ds[3]
        assert f.metadata("param") == "t"


@pytest.mark.parametrize("index_cache", [True, False])
def test_grib_offset_index_cache(index_cache):
    s = {"cache-policy": "temporary", "use-message-position-index-cache": index_cache}
    with settings.temporary(s):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        f = ds[3]
        assert f.metadata("param") == "t", f"index-cache={index_cache}"


# See github #155. This test can hang so we must set a timeout.
@pytest.mark.no_cache_init
@pytest.mark.timeout(20)
def test_cache_with_log_debug(caplog):
    import logging

    # the cache must not be initialised at this point
    assert cache._policy is None
    assert cache._manager is None

    caplog.set_level(logging.DEBUG)
    LOG = logging.getLogger(__name__)

    class A:
        def __repr__(self):
            d = cache.cache_directory()
            return d

    a = A()
    LOG.debug(f"dir {a}")
    # NOTE: if we use "%s" formatting e.g. "LOG.debug("dir %s", a)"
    # the problem still occurs!


def test_cache_zip_file_overwritten_1():
    with temp_directory() as tmp_dir:
        import shutil
        import zipfile

        # copy input data to work dir
        grb1_path = os.path.join(tmp_dir, "test.grib")
        shutil.copyfile(earthkit_examples_file("test.grib"), grb1_path)

        grb2_path = os.path.join(tmp_dir, "test6.grib")
        shutil.copyfile(earthkit_examples_file("test6.grib"), grb2_path)

        # first pass
        zip_path = os.path.join(tmp_dir, "test.zip")
        with zipfile.ZipFile(zip_path, "w") as zip_object:
            zip_object.write(grb1_path)

        ds = from_source("file", zip_path)
        assert len(ds) == 2
        ds_path = ds.path

        # second pass - same zip file, the grib should be read
        #  from the cache
        ds1 = from_source("file", zip_path)
        assert len(ds1) == 2
        assert ds1.path == ds_path

        # third pass - same zipfile path with different contents
        with zipfile.ZipFile(zip_path, "w") as zip_object:
            zip_object.write(grb2_path)

        ds2 = from_source("file", zip_path)
        assert len(ds2) == 6
        assert ds2.path != ds_path


def test_cache_zip_file_changed_modtime():
    with temp_directory() as tmp_dir:
        import shutil
        import zipfile

        # copy input data to work dir
        grb1_path = os.path.join(tmp_dir, "test.grib")
        shutil.copyfile(earthkit_examples_file("test.grib"), grb1_path)

        # first pass
        zip_path = os.path.join(tmp_dir, "test.zip")
        with zipfile.ZipFile(zip_path, "w") as zip_object:
            zip_object.write(grb1_path)

        ds = from_source("file", zip_path)
        assert len(ds) == 2
        ds_path = ds.path

        # second pass - changed modtime
        # TODO: here we have to assume more than 1 ns passed since the
        # zip file was created.
        os.utime(zip_path, None)
        ds2 = from_source("file", zip_path)
        assert len(ds2) == 2
        assert ds2.path != ds_path


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
