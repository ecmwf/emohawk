# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

from . import Reader

LOG = logging.getLogger(__name__)


class UnknownReaderBase(Reader):
    def __init__(
        self,
        source,
        path="",
        magic=None,
        content_type=None,
        skip_warning=False,
        **kwargs,
    ):
        super().__init__(source, path)
        self.magic = magic
        self.content_type = content_type
        self.skip_warning = skip_warning

    def ignore(self):
        # Used by multi-source
        return True

    def __len__(self):
        return 0


class UnknownReader(UnknownReaderBase):
    def __init__(self, source, path, **kwargs):
        super().__init__(source, path=path, **kwargs)
        if not self.skip_warning:
            LOG.warning(
                (
                    f"Unknown file type, no reader available. "
                    f"path={path} magic={self.magic} content_type={self.content_type}"
                )
            )


class UnknownStreamReader(UnknownReaderBase):
    def __init__(self, source, data, **kwargs):
        super().__init__(source, **kwargs)
        if not self.skip_warning:
            LOG.warning(
                (
                    f"Unknown stream data type, no reader available. "
                    f"magic={self.magic} content_type={self.content_type}"
                )
            )


class UnknownMemoryReader(UnknownReaderBase):
    def __init__(self, source, data, **kwargs):
        super().__init__(source, **kwargs)
        if not self.skip_warning:
            LOG.warning(
                (
                    f"Unknown memory data type, no reader available. "
                    f"magic={self.magic} content_type={self.content_type}"
                )
            )
