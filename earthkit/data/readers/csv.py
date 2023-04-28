# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import csv
import io
import logging
import mimetypes
import os
import zipfile

from . import Reader

LOG = logging.getLogger(__name__)


class ZipProbe:
    def __init__(self, path, newline=None, encoding=None):
        zip = zipfile.ZipFile(path)
        members = zip.infolist()
        self.f = zip.open(members[0].filename)
        self.encoding = encoding

    def read(self, size):
        bytes = self.f.read(size)
        return bytes.decode(self.encoding)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        pass


def probe_csv(
    path,
    probe_size=4096,
    compression=None,
    for_is_csv=False,
    minimum_columns=2,
    minimum_rows=2,
):
    OPENS = {
        None: open,
        "zip": ZipProbe,
    }

    try:
        import gzip

        OPENS["gzip"] = gzip.open
    except ImportError:
        pass

    try:
        import bz2

        OPENS["bz2"] = bz2.open
    except ImportError:
        pass

    try:
        import lzma

        OPENS["lzma"] = lzma.open
    except ImportError:
        pass

    _open = OPENS[compression]

    try:
        with _open(path, newline="", encoding="utf-8") as f:
            sample = f.read(probe_size)
            sniffer = csv.Sniffer()
            dialect, has_header = sniffer.sniff(sample), sniffer.has_header(sample)

            LOG.debug("dialect = %s", dialect)
            LOG.debug("has_header = %s", has_header)
            if hasattr(dialect, "delimiter"):
                LOG.debug("delimiter = '%s'", dialect.delimiter)

            if for_is_csv:
                # Check that it is not a trivial text file.
                reader = csv.reader(io.StringIO(sample), dialect)
                if has_header:
                    header = next(reader)
                    LOG.debug("for_is_csv header %s", header)
                    if len(header) < minimum_columns:
                        return None, False
                cnt = 0
                length = None
                for row in reader:
                    cnt += 1
                    LOG.debug("for_is_csv row %s %s", cnt, row)
                    if length is None:
                        length = len(row)
                    if length != len(row):
                        return None, False
                    if cnt >= minimum_rows:
                        break

                if cnt < minimum_rows:
                    return None, False

            return dialect, has_header

    except UnicodeDecodeError:
        return None, False

    except csv.Error:
        return None, False


def is_csv(path, probe_size=4096, compression=None):
    _, extension = os.path.splitext(path)

    if extension in (".xml",):
        return False

    dialect, _ = probe_csv(path, probe_size, compression, for_is_csv=True)
    return dialect is not None


class CSVReader(Reader):
    def __init__(self, source, path, compression=None):
        super().__init__(source, path)
        self.compression = compression
        self.dialect, self.has_header = probe_csv(path, compression=compression)

    def to_pandas(self, **kwargs):
        import pandas

        pandas_read_csv_kwargs = kwargs.get("pandas_read_csv_kwargs", {})
        if self.compression is not None:
            pandas_read_csv_kwargs = dict(**pandas_read_csv_kwargs)
            pandas_read_csv_kwargs["compression"] = self.compression

        LOG.debug("pandas.read_csv(%s,%s)", self.path, pandas_read_csv_kwargs)
        return pandas.read_csv(self.path, **pandas_read_csv_kwargs)


def reader(source, path, magic, deeper_check, fwf=False):
    kind, compression = mimetypes.guess_type(path)

    if kind == "text/csv":
        return CSVReader(source, path, compression=compression)

    if deeper_check and False:
        if is_csv(path):
            return CSVReader(source, path)
