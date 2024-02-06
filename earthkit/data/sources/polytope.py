# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import Source
from .multi_url import MultiUrl
from .prompt import APIKeyPrompt
from .url import Url

LOG = logging.getLogger(__name__)


class PolytopeWebKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = ("",)
    retrieve_api_key_url = ("",)
    prompts = [
        dict(
            name="user_email",
            title="Your email",
        ),
        dict(
            name="user_key",
            example="b295aad8af30332fad2fa8c963ab7900",
            title="API key",
            hidden=True,
            validate="[0-9a-z]{32}",
        ),
    ]

    rcfile = "~/.polytopeapirc"


class Polytope(Source):
    """
    Retrieve data using the Polytope Web API.
    See polytope-client.readthedocs.io for more information.

    Parameters
    ----------
    dataset : str
        The name of the dataset to query.
    request: dict[str, str]
        A collection of key : value pairs specifying the dataset.

    Examples
    --------
    >>> src = earthkit.data.from_source("polytope", "ecmwf-mars", request)
    >>> src.to_pandas()  # if tabular data
    >>> src.to_xarray()  # if datacube
    """

    def __init__(self, dataset, request, address=None, stream=True, **kwargs) -> None:
        try:
            import polytope
        except ImportError:
            raise ImportError(
                "Polytope Web Client must be installed with 'pip install polytope-client'"
            )

        super().__init__()
        assert isinstance(dataset, str)

        self._stream_kwargs = dict()
        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream

        self.request = dict(dataset=dataset, request=request)

        credentials = PolytopeWebKeyPrompt().check(load=True)

        client_kwargs = {}
        if address is not None:
            client_kwargs = {"address": address}
        self.client = polytope.api.Client(**credentials, **client_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.request['dataset']}, {self.request['request']})"

    def mutate(self) -> Source:
        pointers = self.client.retrieve(
            self.request["dataset"],
            self.request["request"],
            pointer=True,
            asynchronous=False,
        )

        urls = [p["location"] for p in pointers]
        LOG.debug(f"{urls=}")

        if self.stream:
            return Url(
                urls,
                stream=True,
                **self._stream_kwargs,
            )
        else:
            return MultiUrl(urls)


source = Polytope
