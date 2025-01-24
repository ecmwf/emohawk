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
import re
from functools import lru_cache
from io import IOBase

import deprecation

from earthkit.data.decorators import normalize
from earthkit.data.decorators import normalize_grib_keys
from earthkit.data.utils.humanize import list_to_human

LOG = logging.getLogger(__name__)

NOT_IN_EDITION_1 = (
    "productDefinitionTemplateNumber",
    "typeOfGeneratingProcess",
)

CACHE = {}


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


class GribCoder:
    def __init__(self, template=None, **kwargs):
        self.template = template
        self._bbox = {}
        self.kwargs = kwargs

    @normalize_grib_keys
    @normalize("date", "date")
    def _normalize_kwargs_names(self, **kwargs):
        return kwargs

    def encode(
        self,
        values,
        check_nans=False,
        metadata={},
        template=None,
        return_bytes=False,
        missing_value=9999,
        **kwargs,
    ):
        # Make a copy as we may modify it
        md = self._normalize_kwargs_names(**self.kwargs)
        md.update(self._normalize_kwargs_names(**metadata))
        md.update(self._normalize_kwargs_names(**kwargs))

        metadata = md

        compulsory = (("date", "referenceDate"), ("param", "paramId", "shortName"))

        if template is None:
            template = self.template

        if template is None:
            handle = self.handle_from_metadata(values, metadata, compulsory)
        else:
            handle = template.handle.clone()
            self.update_metadata_from_template(metadata, template, handle)

        self.update_metadata(handle, metadata, compulsory)

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

        # TODO: revisit that logic
        if "generatingProcessIdentifier" not in metadata:
            metadata["generatingProcessIdentifier"] = 255
        else:
            # kee
            if metadata["generatingProcessIdentifier"] is None:
                metadata.pop("generatingProcessIdentifier")

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

        if return_bytes:
            return handle.get_message()

        return handle

    def update_metadata(self, handle, metadata, compulsory):
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

        if "time" not in metadata and "date" in metadata:
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

    def handle_from_metadata(self, values, metadata, compulsory):
        from .codes import GribCodesHandle  # Lazy loading of eccodes

        if len(values.shape) == 1:
            sample = self._gg_field(values, metadata)
        elif len(values.shape) == 2:
            sample = self._ll_field(values, metadata)
        else:
            raise ValueError(f"Invalid shape {values.shape} for GRIB, must be 1 or 2 dimension ")

        # assert False, sample
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


class GribOutput:
    def __init__(self, file, split_output=False, template=None, **kwargs):
        self._files = {}
        self.fileobj = None
        self.filename = None

        if isinstance(file, IOBase):
            self.fileobj = file
            split_output = False
        else:
            self.filename = file

        if split_output:
            self.split_output = re.findall(r"\{(.*?)\}", self.filename)
        else:
            self.split_output = None

        self._coder = GribCoder(template=template, **kwargs)

    def close(self):
        for f in self._files.values():
            f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.close()

    def write(
        self,
        values,
        check_nans=False,
        metadata={},
        template=None,
        **kwargs,
    ):
        handle = self._coder.encode(
            values,
            check_nans=check_nans,
            metadata=metadata,
            template=template,
            **kwargs,
        )

        file, path = self.f(handle)
        handle.write(file)

        return handle, path

    def f(self, handle):
        if self.fileobj:
            return self.fileobj, None

        if self.split_output:
            path = self.filename.format(**{k: handle.get(k) for k in self.split_output})
        else:
            path = self.filename

        if path not in self._files:
            self._files[path] = open(path, "wb")
        return self._files[path], path


@deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use get_target() instead")
def new_grib_output(*args, **kwargs):
    return GribOutput(*args, **kwargs)


@deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use get_encoder() instead")
def new_grib_coder(*args, **kwargs):
    return GribCoder(*args, **kwargs)
