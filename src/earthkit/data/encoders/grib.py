# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging
from functools import lru_cache

from earthkit.data.decorators import normalize
from earthkit.data.decorators import normalize_grib_keys
from earthkit.data.utils.humanize import list_to_human

from . import EncodedData
from . import Encoder

LOG = logging.getLogger(__name__)

NOT_IN_EDITION_1 = (
    "productDefinitionTemplateNumber",
    "typeOfGeneratingProcess",
)

COMPULSORY = (("date", "referenceDate"), ("param", "paramId", "shortName"))


class GribEncodedData(EncodedData):
    def __init__(self, handle):
        self.handle = handle

    def to_bytes(self):
        return self.handle.get_buffer()

    def to_file(self, f):
        self.handle.write(f)

    def metadata(self, key=None):
        if key:
            return self.handle.get(key)
        else:
            raise NotImplementedError

    def to_field(self):
        from earthkit.data.readers.grib.memory import GribFieldInMemory

        return GribFieldInMemory.from_buffer(self.to_bytes())


class Combined:
    def __init__(self, handle, metadata):
        self.handle = handle
        self.metadata = metadata

    def __contains__(self, key):
        # return key in self.metadata or key in self.handle
        raise NotImplementedError()

    def __getitem__(self, key):
        if key in self.metadata:
            return self.metadata[key]
        return self.handle.get(key, default=None)


@lru_cache(maxsize=None)
def _gg_pl(N):
    import eccodes

    sample = None
    result = {}
    try:
        sample = eccodes.codes_new_from_samples(
            f"reduced_gg_pl_{N}_grib2",
            eccodes.CODES_PRODUCT_GRIB,
        )

        for key in ("N", "Ni", "Nj"):
            result[key] = eccodes.codes_get(sample, key)

        for key in (
            "latitudeOfFirstGridPointInDegrees",
            "longitudeOfFirstGridPointInDegrees",
            "latitudeOfLastGridPointInDegrees",
            "longitudeOfLastGridPointInDegrees",
            "iDirectionIncrementInDegrees",
        ):
            result[key] = eccodes.codes_get_double(sample, key)

        pl = eccodes.codes_get_long_array(sample, "pl")
        result["pl"] = pl.tolist()
        result["gridType"] = "reduced_gg"

        return result

    finally:
        if sample is not None:
            eccodes.codes_release(sample)


class GribHandleMaker:
    """Create a new GribCodesHandle from a template, field or metadata"""

    def __init__(self, template=None):
        self.template = template
        self._bbox = {}

    def make(self, field=None, values=None, metadata=None, template=None):
        """Create a new GribCodesHandle from a template, field or metadata
        May modify existing metadata

        Parameters
        ----------
        field: Field
            The field to encode
        values: numpy.ndarray
            The values to encode
        metadata: dict
            Metadata to encode
        template: GribCoder
            A template to use for encoding
        """
        handle = self.handle_from_template(template)
        if handle is not None:
            self.update_metadata_from_template(metadata, template, handle)

        if handle is None and field is not None:
            handle = self.handle_from_field(field)
            if handle is not None:
                self.update_metadata_from_template(metadata, field, handle)

        if handle is None:
            if values is None:
                raise ValueError("No values to encode")
            handle = self.handle_from_metadata(values, metadata, COMPULSORY)

        return handle

    def handle_from_template(self, template):
        handle = None
        if template is None:
            template = self.template
        if template is not None:
            handle = template.handle.clone()
        return handle

    def handle_from_field(self, field):
        if hasattr(field, "handle"):
            return field.handle.clone()

    def handle_from_metadata(self, values, metadata, compulsory):
        from earthkit.data.readers.grib.codes import GribCodesHandle  # Lazy loading of eccodes

        if len(values.shape) == 1:
            sample = self._gg_field(values, metadata)
        elif len(values.shape) == 2:
            sample = self._ll_field(values, metadata)
        else:
            raise ValueError(f"Invalid shape {values.shape} for GRIB, must be 1 or 2 dimension ")

        metadata.setdefault("bitsPerValue", 16)
        metadata["scanningMode"] = 0

        if "class" in metadata or "type" in metadata or "stream" in metadata or "expver" in metadata:
            # MARS labelling
            metadata["setLocalDefinition"] = 1
            # metadata['grib2LocalSectionNumber'] = 1

        for check in compulsory:
            if not isinstance(check, tuple):
                check = [check]

            if not any(c in metadata for c in check):
                choices = list_to_human([f"'{c}'" for c in check], "or")
                raise ValueError(f"Please provide a value for {choices}.")

        LOG.debug("GribCodesHandle.from_sample(%s)", sample)
        return GribCodesHandle.from_sample(sample)

    def update_metadata_from_template(self, metadata, template, handle):
        # the template can contain extra metadata that is not encoded in the handle
        bpv = None
        if hasattr(template, "metadata"):
            template_md = template.metadata()
            from earthkit.data.core.metadata import WrappedMetadata

            if isinstance(template_md, WrappedMetadata):
                for k in template_md.extra.keys():
                    if k != "bitsPerValue" and k not in metadata:
                        metadata[k] = template_md.get(k)

            if "bitsPerValue" not in metadata:
                bpv = template.metadata("bitsPerValue", default=None)

        # Either the handle has valid bitsPerValue or has to be extracted
        # from the template and added to the metadata to be encoded
        if "bitsPerValue" not in metadata:
            if bpv is None:
                try:
                    bpv = template.handle.get("bitsPerValue", None)
                except Exception:
                    bpv = None

            if bpv is not None and bpv > 0:
                bpv_h = handle.get("bitsPerValue", None)
                if bpv != bpv_h:
                    metadata["bitsPerValue"] = bpv

    def _ll_field(self, values, metadata):
        Nj, Ni = values.shape
        metadata["Nj"] = Nj
        metadata["Ni"] = Ni

        # We assume the scanning mode north->south, west->east
        west_east = 360 / Ni

        if Nj % 2 == 0:
            north_south = 180 / Nj
            adjust = north_south / 2
        else:
            north_south = 181 / Nj
            adjust = 0

        north = 90 - adjust
        south = -90 + adjust
        west = 0
        east = 360 - west_east

        metadata["iDirectionIncrementInDegrees"] = west_east
        metadata["jDirectionIncrementInDegrees"] = north_south

        metadata["latitudeOfFirstGridPointInDegrees"] = north
        metadata["latitudeOfLastGridPointInDegrees"] = south
        metadata["longitudeOfFirstGridPointInDegrees"] = west
        metadata["longitudeOfLastGridPointInDegrees"] = east

        edition = metadata.get("edition", 2)
        levtype = metadata.get("levtype")
        if levtype is None:
            if "levelist" in metadata:
                levtype = "pl"
            else:
                levtype = "sfc"

        return f"regular_ll_{levtype}_grib{edition}"

    def _gg_field(self, values, metadata):
        GAUSSIAN = {
            6114: (32, False),
            13280: (48, False),
            24572: (64, False),
            35718: (80, False),
            40320: (96, True),
            50662: (96, False),
            88838: (128, False),
            108160: (160, True),
            138346: (160, False),
            213988: (200, False),
            348528: (256, False),
            542080: (320, False),
            843490: (400, False),
            1373624: (512, False),
            2140702: (640, False),
            5447118: (1024, False),
            6599680: (1280, True),
            8505906: (1280, False),
            20696844: (2000, False),
        }

        n = len(values)
        if n not in GAUSSIAN:
            raise ValueError(f"Unsupported GAUSSIAN grid. Number of grid points {n:,}")
        N, octahedral = GAUSSIAN[n]

        if N not in self._bbox:
            import eccodes

            self._bbox[N] = max(eccodes.codes_get_gaussian_latitudes(N))

        metadata["latitudeOfFirstGridPointInDegrees"] = self._bbox[N]
        metadata["latitudeOfLastGridPointInDegrees"] = -self._bbox[N]
        metadata["longitudeOfFirstGridPointInDegrees"] = 0

        metadata["N"] = N
        if octahedral:
            half = list(range(20, 20 + N * 4, 4))
            pl = half + list(reversed(half))
            assert len(pl) == 2 * N, (len(pl), 2 * N)
            metadata["pl"] = pl
            metadata["longitudeOfLastGridPointInDegrees"] = 360 - max(pl) / 360
            metadata["Nj"] = len(pl)
        else:
            # We just want the PL
            metadata.update(_gg_pl(N))

        edition = metadata.get("edition", 2)
        levtype = metadata.get("levtype")
        if levtype is None:
            if "levelist" in metadata:
                levtype = "pl"
            else:
                levtype = "sfc"

        if octahedral or levtype == "sfc":
            return f"reduced_gg_{levtype}_grib{edition}"
        else:

            return f"reduced_gg_{levtype}_{N}_grib{edition}"


class GribEncoder(Encoder):
    """Encode GRIB data"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bbox = {}

    @normalize_grib_keys
    @normalize("date", "date")
    def _normalize_kwargs_names(self, **kwargs):
        return kwargs

    def _get_handle(self, **kwargs):
        return GribHandleMaker(template=self.template).make(**kwargs)

    def encode(
        self,
        data=None,
        values=None,
        check_nans=True,
        metadata=None,
        template=None,
        missing_value=9999,
        **kwargs,
    ):
        """
        Parameters
        ----------

        data: Field
            The data to encode
        values: numpy.ndarray
            The values to encode
        check_nans: bool
            Check for NaNs in the values and replace them with missing_value
        metadata: dict
            Metadata to encode
        template: GribCoder
            A template to use for encoding
        return_bytes: bool
            Return the encoded message as bytes
        missing_value: float
            The value to use for NaNs
        kwargs: dict
            Additional metadata to encode
        """
        if template is None:
            template = self.template

        if data is not None and values is not None and template:
            raise ValueError("Cannot provide data, values and template together")

        metadata = metadata if metadata is not None else {}
        md = self._normalize_kwargs_names(**self.metadata)
        md.update(self._normalize_kwargs_names(**metadata))
        md.update(self._normalize_kwargs_names(**kwargs))

        # when the input date a datetime object time can be inferred from it
        can_infer_time = (
            "date" in md
            and isinstance(md["date"], datetime.datetime)
            and not self._has_standard_date_input([self.metadata, metadata, kwargs])
        )

        metadata = md

        kwargs = dict()
        kwargs["values"] = values
        kwargs["check_nans"] = check_nans
        kwargs["metadata"] = metadata
        kwargs["missing_value"] = missing_value
        kwargs["can_infer_time"] = can_infer_time

        if data is not None:
            return data._encode(self, template=template, **kwargs)
        else:
            handle = self._get_handle(template=template, values=values, metadata=metadata)
            return self._make_message(handle, **kwargs)

    def _has_standard_date_input(self, d):
        for v in d:
            date = v.get("date", None)
            if isinstance(date, int):
                return True
            if isinstance(date, str) and len(date) == 8:
                return True

        return False

    def _encode(self, data, **kwargs):
        raise NotImplementedError

    def _encode_field(self, field, values=None, template=None, metadata=None, **kwargs):
        # check if the field is already encoded in the desired format

        if values is None and template is None and not metadata:
            return GribEncodedData(field.handle)

        if values is None and template:
            values = field.values

        handle = self._get_handle(field=field, values=values, metadata=metadata, template=template)
        return self._make_message(handle, values=values, metadata=metadata, **kwargs)

    def _encode_fieldlist(self, fs, **kwargs):
        for f in fs:
            yield f._encode(self, **kwargs)

    def _make_message(
        self, handle, values=None, check_nans=True, metadata=None, missing_value=9999, can_infer_time=False
    ):
        if handle is None:
            raise ValueError("No handle to encode")

        # Make a copy as we may modify it
        if metadata is None:
            metadata = {}

        compulsory = COMPULSORY

        self._update_metadata(handle, metadata, compulsory, can_infer_time)

        if check_nans and values is not None:
            import numpy as np

            if np.isnan(values).any():
                # missing_value = np.finfo(values.dtype).max
                missing_value = missing_value
                values = np.nan_to_num(values, nan=missing_value)
                metadata["missingValue"] = missing_value
                metadata["bitmapPresent"] = 1

        if str(metadata.get("edition")) == "1":
            for k in NOT_IN_EDITION_1:
                metadata.pop(k, None)

        if int(metadata.get("deleteLocalDefinition", 0)):
            for k in ("class", "type", "stream", "expver", "setLocalDefinition"):
                metadata.pop(k, None)

        # keep the original generatingProcessIdentifier if not set
        if "generatingProcessIdentifier" in metadata:
            if metadata["generatingProcessIdentifier"] is None:
                metadata.pop("generatingProcessIdentifier")

        # # TODO: revisit that logic
        # if "generatingProcessIdentifier" not in metadata:
        #     metadata["generatingProcessIdentifier"] = 255
        # else:
        #     # kee
        #     if metadata["generatingProcessIdentifier"] is None:
        #         metadata.pop("generatingProcessIdentifier")

        LOG.debug("GribOutput.metadata %s", metadata)

        single = {}
        multiple = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float, str, bool)):
                single[k] = v
            else:
                multiple[k] = v

        try:
            # Try to set all metadata at once
            # This is needed when we set multiple keys that are interdependent
            handle.set_multiple(single)
        except Exception as e:
            LOG.error("Failed to set metadata at once: %s", e)
            # Try again, but one by one
            for k, v in single.items():
                handle.set(k, v)

        for k, v in multiple.items():
            handle.set(k, v)

        if values is not None:
            handle.set_values(values)

        return GribEncodedData(handle)

    def _update_metadata(self, handle, metadata, compulsory, can_infer_time):
        # TODO: revisit that logic
        combined = Combined(handle, metadata)

        if "step" in metadata or "endStep" in metadata:
            if combined["type"] == "an":
                metadata["type"] = "fc"

        if "time" in metadata:  # TODO, use a normalizer
            try:
                time = int(metadata["time"])
                if time < 100:
                    metadata["time"] = time * 100
            except ValueError:
                pass

        if "time" not in metadata and "date" in metadata and can_infer_time:
            if isinstance(metadata["date"], datetime.datetime):
                date = metadata["date"]
                metadata["time"] = date.hour * 100 + date.minute

        if "date" in metadata:
            if isinstance(metadata["date"], datetime.datetime):
                date = metadata["date"]
                metadata["date"] = date.year * 10000 + date.month * 100 + date.day
            else:
                metadata["date"] = int(metadata["date"])

        if "stream" not in metadata:
            if "number" in metadata:
                metadata["stream"] = "enfo"
                metadata.setdefault("type", "pf")

        if "number" in metadata:
            compulsory += ("numberOfForecastsInEnsemble",)
            metadata.setdefault("productDefinitionTemplateNumber", 1)  # 11 for accumulations

        if metadata.get("type") in ("pf", "cf"):
            metadata.setdefault("typeOfGeneratingProcess", 4)

        if "levelist" in metadata:
            metadata.setdefault("levtype", "pl")

        if "param" in metadata:
            param = metadata.pop("param")
            try:
                metadata["paramId"] = int(param)
            except ValueError:
                metadata["shortName"] = param

        # levtype is a readOnly key in ecCodes >= 2.33.0
        levtype_remap = {
            "pl": "isobaricInhPa",
            "ml": "hybrid",
            "pt": "theta",
            "pv": "potentialVorticity",
            "sfc": "surface",
        }
        if "levtype" in metadata:
            v = metadata.pop("levtype")
            metadata["typeOfLevel"] = levtype_remap[v]


encoder = GribEncoder
