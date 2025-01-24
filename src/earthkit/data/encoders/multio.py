# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import EncodedData
from . import Encoder

LOG = logging.getLogger(__name__)


GEOGRAPHY_ALIASES: dict[str, list[str]] = {
    "north": ["latitudeOfFirstGridPointInDegrees"],
    "west": ["longitudeOfFirstGridPointInDegrees"],
    "south": ["latitudeOfLastGridPointInDegrees"],
    "east": ["longitudeOfLastGridPointInDegrees"],
    "west_east_increment": ["iDirectionIncrementInDegrees"],
    "south_north_increment": ["jDirectionIncrementInDegrees"],
    "Ni": ["Ni"],
    "N": ["N"],
    "Nj": ["Nj"],
    "gridType": ["gridType"],
    "pl": ["pl"],
}


def geography_translate(metadata):
    """Translate geography metadata from earthkit to multio"""
    geo_namespace = metadata.as_namespace("geography")

    multio_geo = {}

    for multio_key, earthkit_keys in GEOGRAPHY_ALIASES.items():
        if not any(key in geo_namespace for key in earthkit_keys):
            continue
        valid_key = [key for key in earthkit_keys if key in geo_namespace]
        if len(valid_key) > 1:
            raise ValueError(f"Multiple keys found for {multio_key}: {valid_key}")
        multio_geo[multio_key] = geo_namespace.pop(valid_key[0])

    multio_geo.update(geo_namespace)
    if "pl" in multio_geo:
        multio_geo["pl"] = ",".join(map(str, multio_geo["pl"].tolist()))
    return multio_geo


def earthkit_to_multio(metadata):
    """Convert earthkit metadata to Multio metadata"""
    metad = metadata.as_namespace("mars")
    metad.update(geography_translate(metadata))
    metad.pop("levtype", None)
    metad.pop("param", None)
    metad.pop("type", None)
    metad.pop("bitmapPresent", None)

    metad["paramId"] = metadata["paramId"]
    metad["typeOfLevel"] = metadata["typeOfLevel"]

    return metad


class MultioEncodedData(EncodedData):
    def __init__(self, values, metadata):
        self._values = values
        self._metadata = metadata

    def to_bytes(self):
        raise NotImplementedError

    def to_file(self, f):
        raise NotImplementedError

    def metadata(self, key=None):
        if key:
            return self._metadata.get(key)
        else:
            return self._metadata

    def to_array(self):
        return self._values


class MultioEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.wrappers import get_wrapper

            data = get_wrapper(data)
            return data._encode(self, **kwargs)
        else:
            raise ValueError("No data to encode")

    # def encode(
    #         self,
    #         data=None,
    #         values=None,
    #         min=None,
    #         max=None,
    #         check_nans=False,
    #         metadata={},
    #         template=None,
    #         # return_bytes=False,
    #         missing_value=9999,
    #         **kwargs,
    #     ):
    #         metadata = earthkit_to_multio(data.metadata())
    #         return MultioEncodedData(data.to_numpy(), metadata)

    def _encode(self, data, **kwargs):
        assert data is not None
        metadata = earthkit_to_multio(data.metadata())
        return MultioEncodedData(data.to_numpy(), metadata)

    def _encode_field(self, field, **kwargs):
        return self._encode(field, **kwargs)

    def _encode_fieldlist(self, data, **kwargs):
        for field in data:
            yield self._encode_field(field, **kwargs)


encoder = MultioEncoder
