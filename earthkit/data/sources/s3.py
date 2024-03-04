# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.sources.multi_url import MultiUrl
from earthkit.data.sources.url import Url
from earthkit.data.utils.url import HttpAuthenticator

from .file import FileSource

LOG = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "s3.amazonaws.com"


def request_to_resource(requests):
    def _make_part(offset, length):
        if offset is not None:
            offset = int(offset)

        if length is not None:
            length = int(length)

        if offset is not None or length is not None:
            return [(offset, length)]

    resources = []
    for r in requests:
        bucket = r["bucket"]
        endpoint = r.get("endpoint", DEFAULT_ENDPOINT)
        for obj in r["objects"]:
            key = obj["object"]
            part = _make_part(obj.get("start"), obj.get("range"))
            resources.append(S3Resource(endpoint, bucket, key, part=part))
    return resources


class S3Authenticator:
    @staticmethod
    def _host(url):
        from urllib.parse import urlparse

        return urlparse(url).netloc

    def __call__(self, r):
        from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

        host = self._host(r.url)
        auth = BotoAWSRequestsAuth(
            aws_host=host,
            aws_region="eu-west-2",
            aws_service="s3",
        )
        return auth(r)


class S3Resource:
    def __init__(self, endpoint, bucket, key, part=None):
        self.endpoint = endpoint
        self.bucket = bucket
        self.key = key
        self.part = part

    @property
    def url(self):
        if "amazonaws" in self.endpoint:
            return f"https://{self.bucket}.{self.endpoint}/{self.key}"
        else:
            return f"https://{self.endpoint}/{self.bucket}/{self.key}"

    def host(self):
        if "amazonaws" in self.endpoint:
            return f"{self.bucket}.{self.endpoint}"
        else:
            return f"{self.endpoint}"

    def __repr__(self):
        return f"{self.__class__.__name__}(url={self.url}, part={self.part})"


class S3Source(FileSource):
    """Represent an AWS S3 bucket source"""

    def __init__(self, *args, anon=True, stream=True, **kwargs) -> None:
        super().__init__()

        self.anon = anon

        self._stream_kwargs = dict()
        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream

        self.request = {}
        for a in args:
            self.request.update(a)
        self.request.update(kwargs)

        if not isinstance(self.request, list):
            self.request = [self.request]

        self.resources = request_to_resource(self.request)

    def mutate(self):
        urls = []
        has_parts = any(r.part is not None for r in self.resources)
        if has_parts:
            for r in self.resources:
                urls.append([r.url, r.part])
        else:
            for r in self.resources:
                urls.append(r.url)

        if not self.anon and has_parts:
            fake_headers = {"accept-ranges": "bytes"}
        else:
            fake_headers = None

        auth = self.make_auth(len(urls))

        if self.stream:
            return Url(
                urls,
                auth=auth,
                fake_headers=fake_headers,
                stream=True,
                **self._stream_kwargs,
            )

        else:
            return MultiUrl(urls, fake_headers=fake_headers, auth=auth)

    def make_auth(self, urls):
        return S3Authenticator() if not self.anon else None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


source = S3Source
