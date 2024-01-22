# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import json
import logging
import os
import threading
import time

import eccodes
import numpy as np

from earthkit.data.core.caching import CACHE, auxiliary_cache_file

LOG = logging.getLogger(__name__)

os.environ["ECCODES_GRIB_SHOW_HOUR_STEPUNIT"] = "1"

# For some reason, cffi can get stuck in the GC if that function
# needs to be called defined for the first time in a GC thread.
try:
    _h = eccodes.codes_new_from_samples(
        "regular_ll_pl_grib1", eccodes.CODES_PRODUCT_GRIB
    )
    eccodes.codes_release(_h)
except Exception:
    pass


class EccodesFeatures:
    def __init__(self):
        v = eccodes.codes_get_version_info()
        try:
            self._version = tuple([int(x) for x in v["eccodes"].split(".")])
        except Exception:
            self._version = (0, 0, 0)

        try:
            self._py_version = tuple([int(x) for x in v["bindings"].split(".")])
        except Exception:
            self._py_version = (0, 0, 0)

        LOG.debug(f"ecCodes versions: {self.versions}")

    def check_clone_kwargs(self, **kwargs):
        if not (self._py_version >= (1, 7, 0) and self._version >= (2, 34, 0)):
            kwargs = dict(**kwargs)
            kwargs.pop("headers_only", None)
        return kwargs

    @property
    def versions(self):
        return f"ecCodes: {self._version} eccodes-python: {self._py_version}"


ECC_FEATURES = EccodesFeatures()


def check_clone_kwargs(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        kwargs = ECC_FEATURES.check_clone_kwargs(**kwargs)
        return func(*args, **kwargs)

    return wrapped


class CodesMessagePositionIndex:
    VERSION = 1

    def __init__(self, path):
        self.path = path
        self.offsets = None
        self.lengths = None
        self._cache_file = None
        self._load()

    def __len__(self):
        return len(self.offsets)

    def _get_message_positions(self, path):
        raise NotImplementedError

    def _build(self):
        offsets = []
        lengths = []

        for offset, length in self._get_message_positions(self.path):
            offsets.append(offset)
            lengths.append(length)

        self.offsets = offsets
        self.lengths = lengths

    def _load(self):
        if CACHE.policy.use_message_position_index_cache():
            self._cache_file = auxiliary_cache_file(
                "message-index",
                self.path,
                content="null",
                extension=".json",
            )
            if not self._load_cache():
                self._build()
                self._save_cache()
        else:
            self._build()

    def _save_cache(self):
        if CACHE.policy.use_message_position_index_cache():
            try:
                with open(self._cache_file, "w") as f:
                    json.dump(
                        dict(
                            version=self.VERSION,
                            offsets=self.offsets,
                            lengths=self.lengths,
                        ),
                        f,
                    )
            except Exception:
                LOG.exception("Write to cache failed %s", self._cache_file)

    def _load_cache(self):
        if CACHE.policy.use_message_position_index_cache():
            try:
                with open(self._cache_file) as f:
                    c = json.load(f)
                    if not isinstance(c, dict):
                        return False

                    assert c["version"] == self.VERSION
                    self.offsets = c["offsets"]
                    self.lengths = c["lengths"]
                    return True
            except Exception:
                LOG.exception("Load from cache failed %s", self._cache_file)

        return False


class CodesHandle(eccodes.Message):
    MISSING_VALUE = np.finfo(np.float32).max
    KEY_TYPES = {"s": str, "l": int, "d": float}
    PRODUCT_ID = None

    def __init__(self, handle, path, offset):
        super().__init__(handle)
        self.path = path
        self.offset = offset

    @classmethod
    def from_sample(cls, name):
        return cls(eccodes.codes_new_from_samples(name, cls.PRODUCT_ID), None, None)

    @classmethod
    def _from_raw_handle(cls, handle):
        return cls(handle, None, None)

    # TODO: just a wrapper around the base class implementation to handle the
    # s,l,d qualifiers. Once these are implemented in the base class this method can
    # be removed. md5GridSection is also handled!
    def get(self, name, ktype=None, **kwargs):
        if ktype is None:
            key_name, _, key_type_str = name.partition(":")
            if key_type_str in CodesHandle.KEY_TYPES:
                name = key_name
                ktype = CodesHandle.KEY_TYPES[key_type_str]

        if "default" in kwargs:
            return super().get(name, ktype=ktype, **kwargs)
        else:
            # this will throw if name is not available
            return super()._get(name, ktype=ktype)

    def get_string(self, name):
        return self.get(name, ktype=str)

    def get_long(self, name):
        return self.get(name, ktype=int)

    @check_clone_kwargs
    def clone(self, **kwargs):
        return self._from_raw_handle(eccodes.codes_clone(self._handle, **kwargs))

    def set_multiple(self, values):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_key_vals(self._handle, values)
        except Exception as e:
            LOG.error(f"Error setting: {values}")
            LOG.exception(e)
            raise

    def set_long(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_long(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)
            raise

    def set_double(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_double(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)
            raise

    def set_string(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_string(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)
            raise

    def set(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"

            if isinstance(value, list):
                return eccodes.codes_set_array(self._handle, name, value)

            return eccodes.codes_set(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)
            raise

    def write(self, f):
        eccodes.codes_write(self._handle, f)

    def save(self, path):
        with open(path, "wb") as f:
            self.write_to(f)
            self.path = path
            self.offset = 0

    def read_bytes(self, offset, length):
        if self.path is not None:
            with open(self.path, "rb") as f:
                f.seek(offset)
                return f.read(length)


class ReaderLRUCache(dict):
    def __init__(self, size):
        self.readers = dict()
        self.lock = threading.Lock()
        self.size = size

    def __getitem__(self, path_and_cls):
        path = path_and_cls[0]
        cls = path_and_cls[1]
        key = (path, os.getpid())
        with self.lock:
            try:
                return super().__getitem__(key)
            except KeyError:
                pass

            c = self[key] = cls(path)
            while len(self) >= self.size:
                _, oldest = min((v.last, k) for k, v in self.items())
                del self[oldest]

            return c


cache = ReaderLRUCache(32)  # TODO: Add to config


class CodesReader:
    PRODUCT_ID = None
    HANDLE_TYPE = None

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        # print("OPEN", self.path)
        self.file = open(self.path, "rb")
        self.last = time.time()

    def __del__(self):
        try:
            # print("CLOSE", self.path)
            self.file.close()
        except Exception:
            pass

    @classmethod
    def from_cache(cls, path):
        return cache[(path, cls)]

    def at_offset(self, offset):
        with self.lock:
            self.last = time.time()
            self.file.seek(offset, 0)
            handle = eccodes.codes_new_from_file(
                self.file,
                self.PRODUCT_ID,
            )
            assert handle is not None
            return self.HANDLE_TYPE(handle, self.path, offset)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path}"
