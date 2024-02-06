# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
from collections import defaultdict, namedtuple

SimplePart = namedtuple("SimplePart", ["offset", "length"])


class Part:
    """Represent a file part."""

    def __init__(self, path, offset, length):
        assert path is not None
        self.path = path
        self.offset = offset
        self.length = length

    def __eq__(self, other):
        return (
            self.path == other.path
            and self.offset == other.offset
            and self.length == other.length
        )

    @classmethod
    def resolve(cls, parts, directory=None):
        paths = defaultdict(list)
        for i, part in enumerate(parts):
            paths[part.path].append(part)

        for path, bits in paths.items():
            if (
                path.startswith("http://")
                or path.startswith("https://")
                or path.startswith("ftp://")
            ):
                # newpath = download_and_cache(
                #     path, parts=[(p.offset, p.length) for p in bits]
                # )
                # newoffset = 0
                # for p in bits:
                #     p.path = newpath
                #     p.offset = newoffset
                #     newoffset += p.length
                raise ValueError("Part: url based paths are not supported")

            elif directory and not os.path.isabs(path):
                for p in bits:
                    p.path = os.path.join(directory, path)

        return parts

    def __repr__(self):
        return f"Part[{self.path},{self.offset},{self.length}]"


def check_urls_and_parts(urls, parts):
    """Check if urls and parts are compatible

    When any of the ``urls`` contain a part ``parts`` must be None.
    """
    if not isinstance(urls, (list, tuple)):
        urls = [urls]

    # a single url as [url, parts] is not allowed
    if (
        len(urls) == 2
        and isinstance(urls[0], str)
        and (urls[1] is None or isinstance(urls[1], (list, tuple)))
    ):
        if parts is not None:
            raise ValueError("Cannot specify parts both as arg and kwarg")
        urls = [urls]

    if any(not isinstance(u, str) for u in urls):
        if parts is not None:
            raise ValueError("Cannot specify parts both as arg and kwarg")

    return urls


def _ensure_parts(parts):
    if parts is None:
        return None
    if len(parts) == 2 and isinstance(parts[0], int) and isinstance(parts[1], int):
        parts = [parts]
    parts = [SimplePart(offset, length) for offset, length in parts]
    if len(parts) == 0:
        return None
    return parts


def ensure_urls_and_parts(urls, parts, compress=True):
    if not isinstance(urls, (list, tuple)):
        urls = [urls]

    parts = _ensure_parts(parts)
    result = []
    for v in urls:
        if isinstance(v, (list, tuple)):
            u, p = v
            result.append((u, _ensure_parts(p)))
        else:
            result.append((v, parts))

    urls_and_parts = []
    # Break into ascending order if needed
    for url, parts in result:
        if parts is None:
            urls_and_parts.append((url, None))
            continue

        last = 0
        newparts = []
        for p in parts:
            if p.offset < last:
                if newparts:
                    urls_and_parts.append((url, compress_parts(newparts)))
                    newparts = []
            newparts.append(p)
            last = p.offset
        urls_and_parts.append((url, compress_parts(newparts)))

    return urls_and_parts


def compress_parts(parts):
    last = -1
    result = []
    # Compress and check
    for offset, length in parts:
        assert offset >= 0 and length > 0
        if offset < last:
            raise Exception(
                f"Offsets and lengths must be in order, and not overlapping:"
                f" offset={offset}, end of previous part={last}"
            )
        if offset == last:
            # Compress
            offset, prev_length = result.pop()
            length += prev_length

        result.append((offset, length))
        last = offset + length
    return tuple(SimplePart(offset, length) for offset, length in result)
