# -*- coding: utf-8 -*-
from django_tables2.data import TableData
from mex.rpc import get_client
from mcrpc.exceptions import RpcError


class LazyStream:
    """A 'paginatable' wrapper for MultiChain Streams"""

    def __init__(self, name, descending=True):
        self.name = name
        self.descending = descending
        self.api = get_client()

    def __len__(self):
        try:
            return int(self.api.liststreams(self.name)[0]["items"])
        except (RpcError, IndexError):
            return 0

    def __getitem__(self, item):
        if self.descending:
            return self._get_descending(item)
        else:
            return self._get_ascending(item)

    def _get_ascending(self, item):
        """From oldest to latest"""
        if isinstance(item, slice):
            count = item.stop - item.start
            try:
                result = self.api.liststreamitems(
                    self.name,
                    verbose=True,
                    count=count,
                    start=item.start,
                    local_ordering=False,
                )
                result = [dict(e, stream=self.name) for e in result]
            except RpcError:
                return []
            return result

        elif isinstance(item, int):
            try:
                result = self.api.liststreamitems(
                    self.name, verbose=True, count=1, start=item, local_ordering=False
                )[0]
                result["stream"] = self.name
            except (RpcError, IndexError):
                return {}
            return result

    def _get_descending(self, item):
        """From latest to oldest entry"""
        if isinstance(item, slice):
            count = item.stop - item.start
            try:
                result = self.api.liststreamitems(
                    self.name,
                    verbose=True,
                    count=count,
                    start=-(item.start + count),
                    local_ordering=False,
                )
                result = [dict(e, stream=self.name) for e in result]
            except RpcError:
                return []
            return list(reversed(result))

        elif isinstance(item, int):
            try:
                result = self.api.liststreamitems(
                    self.name,
                    verbose=True,
                    count=1,
                    start=-(item + 1),
                    local_ordering=False,
                )[0]
                result["stream"] = self.name
            except (RpcError, IndexError):
                return {}
            return result


class TableDataLen(TableData):
    def __len__(self):
        return len(self.data)

    def order_by(self, aliases):
        if aliases == "-time":
            self.data.descending = True
        elif aliases == "time":
            self.data.descending = False
