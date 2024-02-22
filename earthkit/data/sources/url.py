# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

from multiurl import Downloader

from earthkit.data.core.caching import cache_file
from earthkit.data.core.settings import SETTINGS
from earthkit.data.core.statistics import record_statistics
from earthkit.data.utils import progress_bar
from earthkit.data.utils.parts import PathAndParts

from .file import FileSource

LOG = logging.getLogger(__name__)


def _ignore(*args, **kwargs):
    pass


def download_and_cache(
    url,
    *,
    owner="url",
    parts=None,
    verify=True,
    force=None,
    chunk_size=1024 * 1024,
    range_method="auto",
    http_headers=None,
    update_if_out_of_date=False,
    fake_headers=None,  # When HEAD is not allowed but you know the size
    **kwargs,
):
    # TODO: re-enable this feature
    extension = None

    LOG.debug("URL %s", url)

    downloader = Downloader(
        url,
        chunk_size=chunk_size,
        timeout=SETTINGS.get("url-download-timeout"),
        verify=verify,
        parts=parts,
        range_method=range_method,
        http_headers=http_headers,
        fake_headers=fake_headers,
        statistics_gatherer=record_statistics,
        progress_bar=progress_bar,
        resume_transfers=True,
        override_target_file=False,
        download_file_extension=".download",
    )

    if extension and extension[0] != ".":
        extension = "." + extension

    if extension is None:
        extension = downloader.extension()

    path = downloader.local_path()
    if path is not None:
        return

    def out_of_date(url, path, cache_data):
        if SETTINGS.get("check-out-of-date-urls") is False:
            return False

        if downloader.out_of_date(path, cache_data):
            if SETTINGS.get("download-out-of-date-urls") or update_if_out_of_date:
                LOG.warning(
                    "Invalidating cache version and re-downloading %s",
                    url,
                )
                return True
            else:
                LOG.warning(
                    "To enable automatic downloading of updated URLs set the 'download-out-of-date-urls'"
                    " setting to True",
                )
        return False

    if force is None:
        force = out_of_date

    def download(target, _):
        downloader.download(target)
        return downloader.cache_data()

    path = cache_file(
        owner,
        download,
        dict(url=url, parts=parts),
        extension=extension,
        force=force,
    )

    return path


class UrlSourcePathAndParts(PathAndParts):
    compress = True


class UrlBase(FileSource):
    def __init__(
        self,
        url,
        chunk_size=1024 * 1024,
        parts=None,
        filter=None,
        merger=None,
        verify=True,
        range_method="auto",
        http_headers=None,
        fake_headers=None,  # When HEAD is not allowed but you know the size
        stream=False,
        auth=None,
        **kwargs,
    ):
        super().__init__(filter=filter, merger=merger)

        self._url_and_parts = UrlSourcePathAndParts(url, parts)
        self.chunk_size = chunk_size
        self.http_headers = http_headers
        self.auth = auth
        self.verify = verify
        self.range_method = range_method
        self.fake_headers = fake_headers
        self.stream = stream
        self._kwargs = kwargs
        LOG.debug(
            f"url={self.url} url_parts={self.url_parts} auth={self.auth} _kwargs={self._kwargs}"
        )

    def connect_to_mirror(self, mirror):
        return mirror.connection_for_url(self, self.url, self.url_parts)

    def prepare_headers(self, url):
        headers = {}
        if self.http_headers is not None:
            headers = dict(self.http_headers)

        if self.auth is not None:
            headers.update(self.auth.auth_header(url))

        if not headers:
            headers = None

        return headers

    @property
    def url(self):
        return self._url_and_parts.path

    @property
    def url_parts(self):
        return self._url_and_parts.parts

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.url})"


class Url(UrlBase):
    """Represent a URL source.

    Parameters
    ----------
    url: str, list, tuple
        Single url or a list/tuple of urls. A url item can be:

        * a str
        * a list/tuple of two items. The first item is the url as a str, while the second
          item defines the parts for the given url. In this case the ``parts`` kwargs
          cannot be used.

        When ``url`` is a list/tuple these two formats cannot be mixed so either all the url
        items are str or a list/tuple of url and parts.

    """

    def __init__(
        self,
        url,
        *,
        update_if_out_of_date=False,
        force=None,
        **kwargs,
    ):
        super().__init__(url, **kwargs)

        # TODO: re-enable this feature
        extension = None

        if not self.stream:
            self.update_if_out_of_date = update_if_out_of_date

            LOG.debug(
                (
                    f"url={self.url} url_parts={self.url_parts} auth={self.auth}) "
                    f"http_headers={self.http_headers}"
                    f" _kwargs={self._kwargs}"
                )
            )
            self.downloader = Downloader(
                self._url_and_parts.zipped(),
                chunk_size=self.chunk_size,
                timeout=SETTINGS.get("url-download-timeout"),
                verify=self.verify,
                range_method=self.range_method,
                http_headers=self.prepare_headers(self.url),
                fake_headers=self.fake_headers,
                statistics_gatherer=record_statistics,
                progress_bar=progress_bar,
                resume_transfers=True,
                override_target_file=False,
                download_file_extension=".download",
            )

            if extension and extension[0] != ".":
                extension = "." + extension

            if extension is None:
                extension = self.downloader.extension()

            self.path = self.downloader.local_path()
            if self.path is not None:
                return

            if force is None:
                force = self.out_of_date

            def download(target, _):
                self.downloader.download(target)
                return self.downloader.cache_data()

            self.path = self.cache_file(
                download,
                dict(url=self.url, parts=self.url_parts),
                extension=extension,
                force=force,
            )

            # cache data may contain the result of the http HEAD request
            h = self.downloader.cache_data()
            if isinstance(h, dict):
                self.content_type = h.get("content-type")

    def mutate(self):
        if self.stream:
            # # create one stream source per url
            s = []
            for url, parts in self._url_and_parts:
                s.append(
                    SingleUrlStream(
                        url,
                        parts=parts,
                        verify=True,
                        range_method="auto",
                        http_headers=self.prepare_headers(url),
                        fake_headers=None,
                        auth=self.auth,
                    )
                )

            from .stream import _from_source

            return _from_source(s, **self._kwargs)
        else:
            return super().mutate()

    def out_of_date(self, url, path, cache_data):
        if SETTINGS.get("check-out-of-date-urls") is False:
            return False

        if self.downloader.out_of_date(path, cache_data):
            if SETTINGS.get("download-out-of-date-urls") or self.update_if_out_of_date:
                LOG.warning(
                    "Invalidating cache version and re-downloading %s",
                    self.url,
                )
                return True
            else:
                LOG.warning(
                    "To enable automatic downloading of updated URLs set the 'download-out-of-date-urls'"
                    " setting to True",
                )
        return False


class RequestIterStreamer:
    """Expose fixed chunk-based stream reader used in mutiurl as a
    stream supporting a generic read method.
    """

    def __init__(self, iter_content):
        from collections import deque

        self.iter_content = iter_content
        self.content = deque()
        self.position = 0
        self.total = 0
        self.consumed = False

    def _ensure_content(self, size):
        while self.total < size:
            try:
                self.content.append(next(self.iter_content))
                self.total += len(self.content[-1])
            except StopIteration:
                break

    def _read(self, size):
        assert len(self.content) > 0

        start = self.position
        length = min(len(self.content[0]) - start, size)
        end = start + length
        data = self.content[0][start:end]
        last = 0
        size -= length

        if size > 0:
            d = [data]
            for i in range(1, len(self.content)):
                start = 0
                length = min(len(self.content[i]) - start, size)
                end = start + length
                d.append(self.content[i][start:end])
                last = i
                size -= length
                if size <= 0:
                    break
            data = data = b"".join(d)

        return data, last, end, size

    def read(self, size=-1):
        if size < -1 or size == 0 or self.consumed:
            return bytes()

        if size == -1:
            return self.readall()

        self._ensure_content(size)
        if len(self.content) == 0 or self.total == 0:
            self.close()
            return bytes()

        data, last, self.position, missing_size = self._read(size)
        # LOG.debug(f"{size=} {last=} pos={self.position} {missing_size=}")
        if missing_size > 0:
            self.close()
        else:
            if self.position == len(self.content[last]):
                last += 1
                self.position = 0

            if last > 0:
                for _ in range(0, last):
                    self.content.popleft()

            self.total = sum(len(x) for x in self.content)
            self.total -= self.position

        return data

    def readall(self):
        if self.consumed:
            return bytes()

        first = self.read(self.total)
        if len(first) == 0:
            first = next(self.iter_content)
        res = [first]

        for d in self.iter_content:
            res.append(d)

        self.close()

        if len(res) == 1:
            return res[0]
        else:
            return b"".join(res)

    def peek(self, size):
        if size <= 0 or self.consumed:
            return bytes()

        self._ensure_content(size)
        data, _, _, _ = self._read(size)
        return data

    def close(self):
        if not self.closed:
            self._clear()

    @property
    def closed(self):
        return self.consumed

    def _clear(self):
        self.iter_content = None
        self.content.clear()
        self.position = 0
        self.consumed = True


class SingleUrlStream(UrlBase):
    def __init__(
        self,
        url,
        **kwargs,
    ):
        super().__init__(url, **kwargs)

        if isinstance(self.url, (list, tuple)):
            raise TypeError("Only a single url is supported")

        from urllib.parse import urlparse

        o = urlparse(self.url)
        if o.scheme not in ("http", "https"):
            raise NotImplementedError(f"Streams are not supported for {o.scheme} urls")

    def mutate(self):
        from .stream import _from_source

        return _from_source(self, **self._kwargs)

    def to_stream(self):
        downloader = Downloader(
            self.url,
            chunk_size=self.chunk_size,
            parts=self.url_parts,
            timeout=SETTINGS.get("url-download-timeout"),
            verify=self.verify,
            range_method=self.range_method,
            http_headers=self.prepare_headers(self.url),
            fake_headers=self.fake_headers,
            statistics_gatherer=_ignore,
            progress_bar=progress_bar,
            resume_transfers=False,
            override_target_file=False,
        )

        size, mode, skip, trust_size = downloader.estimate_size(None)

        # cache data may contain the result of the http HEAD request
        h = downloader.cache_data()
        if isinstance(h, dict):
            self.content_type = h.get("content-type")

        stream = downloader.make_stream()
        return RequestIterStreamer(stream(chunk_size=self.chunk_size))


source = Url
