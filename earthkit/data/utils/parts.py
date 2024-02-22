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
    if parts == [None]:
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


class PathAndParts:
    compress = None

    def __init__(self, path, parts):
        self.path, self.parts = self._parse(path, parts)

    def is_empty(self):
        return not (self.parts is not None and any(x is not None for x in self.parts))

    def update(self, path):
        if self.path != path:
            self.path, self.parts = self._parse(path, self.parts)

    def _parse(self, paths, parts):
        """Preprocess paths and parts.

        Parameters
        ----------
        paths: str or list/tuple
            The path(s). When it is a sequence either each
            item is a path (str), or a pair of a path and :ref:`parts <parts>`.
        parts: part,list/tuple of parts or None.
            The :ref:`parts <parts>`.

        Returns
        -------
        str or list of str
            The path or paths.
        SimplePart, list or tuple, None
            The parts (one for each path). A part can be a single
            SimplePart, a list/tuple of SimpleParts or None.

        """
        if parts is None:
            if isinstance(paths, str):
                return paths, None
            elif isinstance(paths, (list, tuple)) and all(
                isinstance(p, str) for p in paths
            ):
                return paths, [None] * len(paths)

        paths = check_urls_and_parts(paths, parts)
        paths_and_parts = ensure_urls_and_parts(paths, parts, compress=self.compress)

        paths, parts = zip(*paths_and_parts)
        assert len(paths) == len(parts)
        if len(paths) == 1:
            return paths[0], parts[0]
        else:
            return paths, parts

    def zipped(self):
        return [(pt, pr) for pt, pr in self]

    def __iter__(self):
        path = self.path
        parts = self.parts
        if isinstance(self.path, str):
            path = [self.path]
            parts = [self.parts]
        return zip(path, parts)
