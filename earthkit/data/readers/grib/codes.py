# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os

import eccodes
import numpy as np

from earthkit.data.core.fieldlist import Field
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.utils.message import (
    CodesHandle,
    CodesMessagePositionIndex,
    CodesReader,
)

LOG = logging.getLogger(__name__)

_GRIB_NAMESPACES = {"default": None}

for k in ("ls", "geography", "mars", "parameter", "statistics", "time", "vertical"):
    _GRIB_NAMESPACES[k] = k


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribCodesFloatArrayAccessor:
    HAS_FLOAT_SUPPORT = None
    KEY = None

    def __init__(self):
        if GribCodesFloatArrayAccessor.HAS_FLOAT_SUPPORT is None:
            GribCodesFloatArrayAccessor.HAS_FLOAT_SUPPORT = hasattr(
                eccodes, "codes_get_float_array"
            )

    def get(self, handle, dtype=None):
        v = eccodes.codes_get_array(handle, self.KEY)
        if dtype is not None:
            return v.astype(dtype)
        else:
            return v


class GribCodesValueAccessor(GribCodesFloatArrayAccessor):
    KEY = "values"

    def __init__(self):
        super().__init__()

    def get(self, handle, dtype=None):
        if dtype is np.float32 and self.HAS_FLOAT_SUPPORT:
            return eccodes.codes_get_array(handle, self.KEY, ktype=dtype)
        else:
            return super().get(handle, dtype=dtype)


class GribCodesLatitudeAccessor(GribCodesFloatArrayAccessor):
    KEY = "latitudes"

    def __init__(self):
        super().__init__()


class GribCodesLongitudeAccessor(GribCodesFloatArrayAccessor):
    KEY = "longitudes"

    def __init__(self):
        super().__init__()


VALUE_ACCESSOR = GribCodesValueAccessor()
LATITUDE_ACCESSOR = GribCodesLatitudeAccessor()
LONGITUDE_ACCESSOR = GribCodesLongitudeAccessor()


class GribCodesMessagePositionIndex(CodesMessagePositionIndex):
    # This does not belong here, should be in the C library
    def _get_message_positions(self, path):
        fd = os.open(path, os.O_RDONLY)
        try:

            def get(count):
                buf = os.read(fd, count)
                assert len(buf) == count
                return int.from_bytes(
                    buf,
                    byteorder="big",
                    signed=False,
                )

            offset = 0
            while True:
                code = os.read(fd, 4)
                if len(code) < 4:
                    break

                if code != b"GRIB":
                    offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                    continue

                length = get(3)
                edition = get(1)

                if edition == 1:
                    if length & 0x800000:
                        sec1len = get(3)
                        os.lseek(fd, 4, os.SEEK_CUR)
                        flags = get(1)
                        os.lseek(fd, sec1len - 8, os.SEEK_CUR)

                        if flags & (1 << 7):
                            sec2len = get(3)
                            os.lseek(fd, sec2len - 3, os.SEEK_CUR)

                        if flags & (1 << 6):
                            sec3len = get(3)
                            os.lseek(fd, sec3len - 3, os.SEEK_CUR)

                        sec4len = get(3)

                        if sec4len < 120:
                            length &= 0x7FFFFF
                            length *= 120
                            length -= sec4len
                            length += 4

                if edition == 2:
                    length = get(8)

                yield offset, length
                offset = os.lseek(fd, offset + length, os.SEEK_SET)

        finally:
            os.close(fd)


class GribCodesHandle(CodesHandle):
    PRODUCT_ID = eccodes.CODES_PRODUCT_GRIB

    # TODO: just a wrapper around the base class implementation to handle the
    # s,l,d qualifiers. Once these are implemented in the base class this method can
    # be removed. md5GridSection is also handled!
    def get(self, name, ktype=None, **kwargs):
        if name == "values":
            return self.get_values()
        elif name == "md5GridSection":
            return self.get_md5GridSection()

        return super().get(name, ktype, **kwargs)

    def get_md5GridSection(self):
        # Special case because:
        #
        # 1) eccodes is returning size > 1 for 'md5GridSection'
        # (size = 16 : it is the number of bytes of the value)
        # This is already fixed in eccodes 2.27.1
        #
        # 2) sometimes (see below), the value for "shapeOfTheEarth" is inconsistent.
        # This impacts the (computed on-the-fly) value of "md5GridSection".
        # ----------------
        # Example of data with inconsistent values:
        # S2S data, origin='ecmf', param='tp', step='24', number='0', date=['20201203','20200702']
        # the 'md5GridSection' are different
        # This is because one has "shapeOfTheEarth" set to 0, the other to 6.
        # This is only impacting the metadata.
        # Since this has no impact on the data itself,
        # this is unlikely to be fixed. Therefore this hacky patch.
        #
        # Obviously, the patch causes an inconsistency between the value of md5GridSection
        # read by this code, and the value read by another code without this patch.

        save = eccodes.codes_get_long(self._handle, "shapeOfTheEarth")
        eccodes.codes_set_long(self._handle, "shapeOfTheEarth", 255)
        result = eccodes.codes_get_string(self._handle, "md5GridSection")
        eccodes.codes_set_long(self._handle, "shapeOfTheEarth", save)
        return result

    def as_namespace(self, namespace, param="shortName"):
        r = {}
        ignore = {
            "distinctLatitudes",
            "distinctLongitudes",
            "distinctLatitudes",
            "latLonValues",
            "latitudes",
            "longitudes",
            "values",
        }
        for key in self.keys(namespace=namespace):
            if key not in ignore:
                r[key] = self.get(param if key == "param" else key)
        return r

    # TODO: once missing value handling is implemented in the base class this method
    # can be removed
    def get_values(self, dtype=None):
        eccodes.codes_set(self._handle, "missingValue", CodesHandle.MISSING_VALUE)
        vals = VALUE_ACCESSOR.get(self._handle, dtype=dtype)
        if self.get_long("bitmapPresent"):
            vals[vals == CodesHandle.MISSING_VALUE] = np.nan
        return vals

    def get_latitudes(self, dtype=None):
        return LATITUDE_ACCESSOR.get(self._handle, dtype=dtype)

    def get_longitudes(self, dtype=None):
        return LONGITUDE_ACCESSOR.get(self._handle, dtype=dtype)

    def get_data_points(self):
        return eccodes.codes_grib_get_data(self._handle)

    def set_values(self, values):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_values(self._handle, values.flatten())
        except Exception as e:
            LOG.error("Error setting values")
            LOG.exception(e)
            raise


class GribCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_GRIB
    HANDLE_TYPE = GribCodesHandle


class GribField(Field):
    r"""Represents a GRIB message in a GRIB file.

    Parameters
    ----------
    path: str
        Path to the GRIB file
    offset: number
        File offset of the message (in bytes)
    length: number
        Size of the message (in bytes)
    """

    def __init__(self, path, offset, length):
        super().__init__()
        self.path = path
        self._offset = offset
        self._length = length
        self._handle = None

    @property
    def handle(self):
        r""":class:`CodesHandle`: Gets an object providing access to the low level GRIB message structure."""
        if self._handle is None:
            assert self._offset is not None
            self._handle = GribCodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    def _values(self, dtype=None):
        return self.handle.get_values(dtype=dtype)

    @property
    def offset(self):
        r"""number: Gets the offset (in bytes) of the GRIB field within the GRIB file."""
        if self._offset is None:
            self._offset = int(self.handle.get("offset"))
        return self._offset

    def _make_metadata(self):
        return GribMetadata(self.handle)

    def __repr__(self):
        return "GribField(%s,%s,%s,%s,%s,%s)" % (
            self._metadata.get("shortName", None),
            self._metadata.get("levelist", None),
            self._metadata.get("date", None),
            self._metadata.get("time", None),
            self._metadata.get("step", None),
            self._metadata.get("number", None),
        )

    # def _get(self, name):
    #     """Private, for testing only"""
    #     # paramId is renamed as param to get rid of the
    #     # additional '.128' (in earthkit/data/scripts/grib.py)
    #     if name == "param":
    #         name = "paramId"
    #     return self.handle.get(name)

    def write(self, f):
        r"""Writes the message to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        """
        # assert isinstance(f, io.IOBase)
        self.handle.write_to(f)

    def message(self):
        r"""Returns a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()
