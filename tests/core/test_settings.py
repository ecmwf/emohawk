#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import settings
from earthkit.data.core.temporary import temp_directory


def read_settings_yaml(path="~/.earthkit-data/settings.yaml"):
    try:
        with open(path) as f:
            import yaml

            s = yaml.load(f, Loader=yaml.SafeLoader)
            if not isinstance(s, dict):
                s = {}
            return s
    except Exception:
        return {}


@pytest.mark.parametrize(
    "param,default_value,new_value",
    [
        ("number-of-download-threads", 5, 2),
    ],
)
def test_settings_params_set_reset(param, default_value, new_value):
    ori_value = settings.get(param)

    with settings.temporary():
        settings.reset()

        assert settings.get(param) == default_value
        settings.set(param, new_value)
        assert settings.get(param) == new_value
        settings.reset()
        assert settings.get(param) == default_value

    assert settings.get(param) == ori_value


def test_settings_invalid():
    # invalid param
    with pytest.raises(KeyError):
        settings.get("_invalid_")

    with pytest.raises(KeyError):
        settings.set("_invalid_", 1)

    # invalid value
    with pytest.raises(ValueError):
        settings.set("number-of-download-threads", "A")


@pytest.mark.parametrize(
    "param,set_value,stored_value,raise_error",
    [
        ("number-of-download-threads", "A", "A", ValueError),
        ("url-download-timeout", 30, 30, None),
        ("url-download-timeout", "30", 30, None),
        ("url-download-timeout", "2m", 120, None),
        ("url-download-timeout", "10h", 36000, None),
        ("url-download-timeout", "7d", 7 * 24 * 3600, None),
        ("url-download-timeout", "1x", None, ValueError),
        ("url-download-timeout", "1M", 60, ValueError),
        ("reader-type-check-bytes", 8, 8, None),
        ("reader-type-check-bytes", 1, 1, ValueError),
        ("reader-type-check-bytes", 4097, 4097, ValueError),
    ],
)
def test_settings_set_numbers(param, set_value, stored_value, raise_error):
    with settings.temporary():
        if raise_error is None:
            settings.set(param, set_value)
            assert settings.get(param) == stored_value
        else:
            with pytest.raises(raise_error):
                settings.set(param, set_value)


def test_settings_set_cache_numbers():
    with temp_directory() as tmpdir:
        with settings.temporary(
            {"cache-policy": "user", "user-cache-directory": tmpdir}
        ):
            data = [
                ("maximum-cache-size", "1", 1, None),
                ("maximum-cache-size", "1k", 1024, None),
                ("maximum-cache-size", "1kb", 1024, None),
                ("maximum-cache-size", "1k", 1024, None),
                ("maximum-cache-size", "1kb", 1024, None),
                ("maximum-cache-size", "1K", 1024, None),
                ("maximum-cache-size", "1M", 1024 * 1024, None),
                ("maximum-cache-size", "1G", 1024 * 1024 * 1024, None),
                ("maximum-cache-size", "1T", 1024 * 1024 * 1024 * 1024, None),
                ("maximum-cache-size", "1P", 1024 * 1024 * 1024 * 1024 * 1024, None),
                ("maximum-cache-size", None, None, None),
                ("maximum-cache-size", "-1", None, ValueError),
                ("maximum-cache-disk-usage", "2%", 2, None),
                ("maximum-cache-disk-usage", None, None, None),
                ("maximum-cache-disk-usage", "-2%", None, ValueError),
                ("maximum-cache-disk-usage", "102%", 102, None),
                ("maximum-cache-disk-usage", "0%", 0, None),
            ]

            for param, set_value, stored_value, raise_error in data:
                if raise_error is None:
                    settings.set(param, set_value)
                    if stored_value is not None:
                        assert settings.get(param) == stored_value
                    else:
                        assert settings.get(param) is None
                else:
                    with pytest.raises(raise_error):
                        settings.set(param, set_value)


def test_settings_set_multi():
    with settings.temporary():
        settings.set("number-of-download-threads", 7)
        assert settings.get("number-of-download-threads") == 7

        settings.set({"number-of-download-threads": 2, "url-download-timeout": 21})
        assert settings.get("number-of-download-threads") == 2
        assert settings.get("url-download-timeout") == 21

        settings.set(number_of_download_threads=3, url_download_timeout=11)
        assert settings.get("number-of-download-threads") == 3
        assert settings.get("url-download-timeout") == 11

        with pytest.raises(KeyError):
            settings.set({"number-of-download-threads": 2, "-invalid-": 21})

        with pytest.raises(KeyError):
            settings.set(number_of_download_threads=3, __invalid__=11)


def test_settings_temporary_single():
    with settings.temporary("number-of-download-threads", 7):
        assert settings.get("number-of-download-threads") == 7

    with settings.temporary({"number-of-download-threads": 7}):
        assert settings.get("number-of-download-threads") == 7

    with settings.temporary(number_of_download_threads=7):
        assert settings.get("number-of-download-threads") == 7


def test_settings_temporary_multi():
    with settings.temporary(
        {"number-of-download-threads": 2, "url-download-timeout": 21}
    ):
        assert settings.get("number-of-download-threads") == 2
        assert settings.get("url-download-timeout") == 21

    with settings.temporary(number_of_download_threads=3, url_download_timeout=11):
        assert settings.get("number-of-download-threads") == 3
        assert settings.get("url-download-timeout") == 11


def test_settings_temporary_nested():
    with settings.temporary("number-of-download-threads", 7):
        assert settings.get("number-of-download-threads") == 7
        with settings.temporary("number-of-download-threads", 10):
            assert settings.get("number-of-download-threads") == 10
        assert settings.get("number-of-download-threads") == 7


@pytest.mark.parametrize("autosave", [True, False])
def test_settings_temporary_autosave(autosave):
    v_ori = settings.auto_save_settings
    s = read_settings_yaml()
    if s:
        with settings.temporary():
            settings.auto_save_settings = autosave
            v = settings.get("number-of-download-threads")
            settings.set("number-of-download-threads", v + 10)
            assert s["number-of-download-threads"] == v
        assert settings.auto_save_settings == autosave
    settings.auto_save_settings = v_ori


def test_settings_auto_save():
    v_ori = settings.auto_save_settings
    settings.auto_save_settings = False
    s = read_settings_yaml()
    if s:
        v = settings.get("number-of-download-threads")
        settings.set("number-of-download-threads", v + 10)
        assert s["number-of-download-threads"] == v
    settings.auto_save_settings = v_ori


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
