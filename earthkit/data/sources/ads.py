# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import cdsapi
import yaml

from .cds import CdsRetriever
from .prompt import APIKeyPrompt


class ADSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://ads.atmosphere.copernicus.eu/"
    retrieve_api_key_url = "https://ads.atmosphere.copernicus.eu/api-how-to"

    prompts = [
        dict(
            name="url",
            default="https://ads.atmosphere.copernicus.eu/api/v2",
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

    rcfile = "~/.adsapirc"

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


def client():
    prompt = ADSAPIKeyPrompt()
    rc = prompt.check(load=True)
    return cdsapi.Client(**rc)


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class AdsRetriever(CdsRetriever):
    sphinxdoc = """
    AdsRetriever
    """

    def client(self):
        return client()


source = AdsRetriever
