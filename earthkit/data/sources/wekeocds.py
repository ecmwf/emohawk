# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

from hda.api import DataOrderRequest

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.decorators import normalize
from earthkit.data.utils import tqdm

from .file import FileSource
from .wekeo import EXTENSIONS
from .wekeo import ApiClient as WekeoClient
from .wekeo import HDAAPIKeyPrompt


class ApiClient(WekeoClient):
    name = "wekeocds"

    def __int__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def retrieve(self, name, request, target=None):
        rq = {
            "datasetId": name,
            "multiStringSelectValues": [
                {
                    "name": _name,
                    "value": _value if isinstance(_value, list) else [_value],
                }
                for _name, _value in request.items()
            ],
        }
        if "area" in request:
            rq.update({"boundingBoxValues": {"name": "area", "bbox": request["area"]}})
        matches = self.search(rq)
        out = []
        for result in matches.results:
            query = {"jobId": matches.job_id, "uri": result["url"]}
            # matches.debug(result)
            url = DataOrderRequest(self).run(query)
            out.append(
                self.stream(result.get("filename"), result.get("size"), target, *url)
            )
        return [os.path.abspath(_) for _ in out]


class WekeoCdsRetriever(FileSource):
    sphinxdoc = """
    WekeoCdsRetriever
    """

    @staticmethod
    def client():
        prompt = HDAAPIKeyPrompt()
        prompt.check()
        try:
            return ApiClient()
        except Exception as e:
            if ".hdarc" in str(e):
                prompt.ask_user_and_save()
                return ApiClient()

            raise

    def __init__(self, dataset, *args, **kwargs):
        super().__init__()

        assert isinstance(dataset, str)
        if len(args):
            assert len(args) == 1
            assert isinstance(args[0], dict)
            assert not kwargs
            kwargs = args[0]

        requests = self.requests(**kwargs)

        self.client()  # Trigger password prompt before thraeding

        nthreads = min(self.settings("number-of-download-threads"), len(requests))

        if nthreads < 2:
            self.path = [self._retrieve(dataset, r) for r in requests]
        else:
            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [pool.submit(self._retrieve, dataset, r) for r in requests]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(requests)))

    def _retrieve(self, dataset, request):
        def retrieve(target, args):
            self.client().retrieve(args[0], args[1], target)

        return self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )

    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def requests(self, **kwargs):
        if "year" in kwargs:
            if "month" not in kwargs:
                kwargs["month"] = [f"{i+1:02}" for i in range(0, 12)]
            if "day" not in kwargs:
                kwargs["day"] = [f"{i+1:02}" for i in range(0, 31)]

        split_on = kwargs.pop("split_on", None)
        if split_on is None or not isinstance(kwargs.get(split_on), (list, tuple)):
            return [kwargs]

        result = []

        for v in kwargs[split_on]:
            r = dict(**kwargs)
            r[split_on] = v
            result.append(r)

        return result


source = WekeoCdsRetriever
