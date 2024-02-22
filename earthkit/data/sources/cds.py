# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging
import sys
from functools import cached_property

import cdsapi
import yaml

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.decorators import normalize
from earthkit.data.utils import ensure_iterable, tqdm

from .file import FileSource
from .prompt import APIKeyPrompt

if sys.version_info >= (3, 12):
    from itertools import batched
else:

    def batched(iterable, n):
        # batched('ABCDEFG', 3) --> ABC DEF G
        if n < 1:
            raise ValueError("n must be at least one")
        it = iter(iterable)
        while batch := tuple(itertools.islice(it, n)):
            yield batch


LOG = logging.getLogger(__name__)


class CDSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://cds.climate.copernicus.eu/"
    retrieve_api_key_url = "https://cds.climate.copernicus.eu/api-how-to"

    prompts = [
        dict(
            name="url",
            default="https://cds.climate.copernicus.eu/api/v2",
            title="API url",
            validate=r"http.?://.*",
        ),
        dict(
            name="key",
            example="123:abcdef01-0000-1111-2222-0123456789ab",
            title="API key",
            hidden=True,
            validate=r"\d+:[\-0-9a-f]+",
        ),
    ]

    rcfile = "~/.cdsapirc"
    rcfile_env = "CDSAPI_RC"
    config_env = ("CDSAPI_URL", "CDSAPI_KEY")

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


def client(use_prompt):
    if use_prompt:
        prompt = CDSAPIKeyPrompt()
        prompt.check()

        try:
            return cdsapi.Client()
        except Exception as e:
            if ".cdsapirc" in str(e) or not prompt.has_config_env():
                LOG.warning(e)
                LOG.exception(f"Could not load cds api client. {e}")
                prompt.ask_user_and_save()
                return cdsapi.Client()

            raise
    else:
        return cdsapi.Client()


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class CdsRetriever(FileSource):
    sphinxdoc = """
    CdsRetriever
    """

    def __init__(self, dataset, *args, prompt=True, **kwargs):
        super().__init__()

        self.prompt = prompt

        assert isinstance(dataset, str)
        if args and kwargs:
            raise TypeError(
                "CdsRetriever: cannot specify request using both args and kwargs"
            )

        if not args:
            args = (kwargs,)
        assert all(isinstance(request, dict) for request in args)
        self._args = args

        self.client()  # Trigger password prompt before threading

        nthreads = min(self.settings("number-of-download-threads"), len(self.requests))

        if nthreads < 2:
            self.path = [self._retrieve(dataset, r) for r in self.requests]
        else:
            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [
                    pool.submit(self._retrieve, dataset, r) for r in self.requests
                ]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(self.requests)))

    def _retrieve(self, dataset, request):
        def retrieve(target, args):
            print(f"RETRIEVE={args}")
            cds_result = self.client().retrieve(args[0], args[1])
            self.source_filename = cds_result.location.split("/")[-1]
            cds_result.download(target=target)

        return_object = self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )
        return return_object

    @staticmethod
    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def _normalize_request(**kwargs):
        return kwargs

    @cached_property
    def requests(self):
        requests = []
        for arg in self._args:
            request = self._normalize_request(**arg)
            split_on = request.pop("split_on", None)
            if split_on is None:
                requests.append(request)
                continue

            if not isinstance(split_on, dict):
                split_on = {k: 1 for k in ensure_iterable(split_on)}
            for values in itertools.product(
                *[batched(ensure_iterable(request[k]), v) for k, v in split_on.items()]
            ):
                subrequest = dict(zip(split_on, values))
                requests.append(request | subrequest)
        return requests

    def client(self):
        return client(self.prompt)


source = CdsRetriever
