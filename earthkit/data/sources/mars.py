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
import subprocess

import ecmwfapi

from earthkit.data.core.settings import SETTINGS
from earthkit.data.core.temporary import temp_file

from .ecmwf_api import ECMWFApi, MARSAPIKeyPrompt

LOG = logging.getLogger(__name__)


class StandaloneMarsClient:
    EXE = "/usr/local/bin/mars"

    def execute(self, request, target):
        req = ["retrieve,"]

        for k, v in request.items():
            if isinstance(v, (list, tuple)):
                v = "/".join([str(x) for x in v])
            req += [f"{k}={v},"]

        req += [f'target="{target}"']
        req_str = "\n".join(req)
        with temp_file() as filename:
            with open(filename, "w") as f:
                f.write(req_str + "\n")
            LOG.debug(f"Sending Mars request: '{req_str}'")

            subprocess.run(
                [self.EXE, filename],
                env=dict(os.environ, MARS_AUTO_SPLIT_BY_DATES="1"),
                check=True,
            )


class MarsRetriever(ECMWFApi):
    def service(self):
        if SETTINGS.get("use-standalone-mars-client-when-available"):
            if os.path.exists(StandaloneMarsClient.EXE):
                return StandaloneMarsClient()

        if self.prompt:
            prompt = MARSAPIKeyPrompt()
            prompt.check()

            try:
                return ecmwfapi.ECMWFService("mars")
            except Exception as e:
                if ".ecmwfapirc" in str(e) or not prompt.env_configured():
                    LOG.warning(e)
                    LOG.exception(f"Could not load ecmwf api (mars) client. {e}")
                    prompt.ask_user_and_save()
                    return ecmwfapi.ECMWFService("mars")

                raise
        else:
            return ecmwfapi.ECMWFService("mars")


source = MarsRetriever
