# -*- coding: utf-8 -*-
import datetime
from functools import partial

import ubjson
from binascii import unhexlify
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from django_filters.views import FilterView
from django_tables2 import MultiTableMixin, SingleTableView, SingleTableMixin
from mex.filters import StreamItemFilter
from mex.paginator import StreamPaginator
from mex.rpc import get_client
from mex.tables import (
    BlockTable,
    TransactionTable,
    AddressTable,
    StreamTable,
    StreamItemTable,
)
from mex.models import Block, Transaction, Address, Output, Stream, StreamItem
from mex.utils import public_key_to_address


class StatusView(TemplateView):
    template_name = "mex/status.html"

    def get_context_data(self, **kwargs):
        api = get_client()
        ctx = super().get_context_data(**kwargs)
        ctx["info"] = api.getinfo()
        return ctx


class HomeView(MultiTableMixin, TemplateView):

    template_name = "mex/home.html"
    tables = [
        BlockTable(Block.objects.all()),
        TransactionTable(Transaction.objects.all()),
    ]
    table_pagination = {"per_page": 6}


class TableBlocks(SingleTableView):
    template_name = "mex/table_simple.html"
    model = Block
    table_class = BlockTable
    paginate_by = 6


class TableTransactions(SingleTableView):
    template_name = "mex/table_simple.html"
    model = Transaction
    table_class = TransactionTable
    paginate_by = 6


class BlockListView(SingleTableView):
    model = Block
    table_class = BlockTable
    paginate_by = 17


class TransactionListView(SingleTableView):
    model = Transaction
    table_class = TransactionTable
    paginate_by = 17


class AddressListView(SingleTableView):
    model = Address
    table_class = AddressTable
    paginate_by = 17

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.with_balance()


class StreamTableView(SingleTableView):
    model = Stream
    template_name = "mex/stream_list2.html"
    table_class = StreamTable
    queryset = Stream.objects.filter(show=True)
    paginate_by = 17


class StreamItemTableView(SingleTableMixin, FilterView):

    model = StreamItem
    template_name = "mex/stream_item_list.html"
    table_class = StreamItemTable
    paginate_by = 17
    filterset_class = StreamItemFilter

    @property
    def paginator_class(self):
        return partial(StreamPaginator, stream=self.kwargs["stream"])

    def get_queryset(self):
        stream = get_object_or_404(Stream, name=self.kwargs["stream"])
        return StreamItem.objects.filter(stream=stream).only("time", "keys")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_keys"] = self.request.GET.get("keys", None)
        return ctx


class TokenListView(TemplateView):
    template_name = "mex/token_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        ctx["tokens"] = api.listassets()
        return ctx


class BlockDetailView(DetailView):

    model = Block
    slug_field = "hash"
    slug_url_kwarg = "hash"

    def get_context_data(self, **kwargs):
        api = get_client()
        ctx = super().get_context_data(**kwargs)
        ctx["MEX_MINER"] = settings.MEX_MINER
        ctx["details"] = api.getblock(ctx["block"].hash, 1)
        ctx["formattedtime"] = datetime.datetime.fromtimestamp(ctx["details"]["time"])
        ctx["num_transactions"] = len(ctx["details"]["tx"])
        return ctx


class TransactionDetailView(TemplateView):
    template_name = "mex/transaction_detail.html"

    def get_context_data(self, **kwargs):
        api = get_client()
        ctx = super().get_context_data(**kwargs)
        tx_raw = api.getrawtransaction(ctx["hash"], 4)
        if tx_raw.get("confirmations"):
            try:
                tx_db = Transaction.objects.get(hash=tx_raw["txid"])
                outputs_db = tx_db.outputs_for_tx.order_by("out_idx")
            except Transaction.DoesNotExist:
                outputs_db = None
        else:
            outputs_db = None

        ctx["details"] = tx_raw
        ctx["raw"] = "raw" in self.request.GET
        blockchain_params = api.getblockchainparams()
        pubkeyhash_version = blockchain_params["address-pubkeyhash-version"]
        checksum_value = blockchain_params["address-checksum-value"]
        if "blocktime" in ctx["details"]:
            ctx["formattedBlocktime"] = datetime.datetime.fromtimestamp(
                ctx["details"]["blocktime"]
            )
        ctx["formattedVin"] = []
        ctx["formattedVout"] = []

        for index, vin in enumerate(ctx["details"]["vin"]):
            address = "N/A"
            if "scriptSig" in vin:
                public_key = vin["scriptSig"]["asm"].split(" ")[1]
                address = public_key_to_address(
                    public_key, pubkeyhash_version, checksum_value
                )
            ctx["formattedVin"].append(
                {
                    "index": index,
                    "address": address,
                    "transaction": vin["txid"] if "txid" in vin else "",
                    "vout": vin.get("vout", 0),
                }
            )

        for index, vout in enumerate(ctx["details"]["vout"]):
            address = "N/A"

            if "scriptPubKey" in vout and "addresses" in vout["scriptPubKey"]:
                address = ", ".join(vout["scriptPubKey"]["addresses"])

            if outputs_db and outputs_db[index].spent:
                redeemed_in = outputs_db[index].spent_by_txid()
            else:
                redeemed_in = ""

            ctx["formattedVout"].append(
                {
                    "index": index,
                    "address": address,
                    "transaction": redeemed_in,
                    "amount": vout["value"],
                }
            )
        return ctx


class AddressDetailView(DetailView):
    model = Address
    slug_field = "address"
    slug_url_kwarg = "address"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        address = ctx["address"].address
        ctx["amount_blocks"] = Block.objects.filter(miner=address).count()
        api = get_client()
        blocks = api.getinfo().blocks
        ctx["miner"] = False
        for perm in api.listpermissions("mine"):
            if (
                perm["address"] == address
                and perm["startblock"] < blocks < perm["endblock"]
            ):
                ctx["miner"] = True
        ctx["admin"] = False
        for perm in api.listpermissions("admin"):
            if (
                perm["address"] == address
                and perm["startblock"] < blocks < perm["endblock"]
            ):
                ctx["admin"] = True
        qs = super().get_queryset()
        ctx["balance"] = qs.with_balance().filter(address=address).first().balance
        last_out = Output.objects.filter(address=address).order_by(
            "-transaction__block__time"
        )[:10]
        ctx["last_tx"] = []
        for out in last_out:
            ctx["last_tx"].append(
                {
                    "tx": out.transaction.hash,
                    "time": out.transaction.block.time,
                    "hash": out.transaction.block.hash,
                    "height": out.transaction.block.height,
                }
            )
        return ctx


class StreamItemDetail(TemplateView):
    template_name = "mex/stream_item_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tx, out_idx = self.kwargs.get("output").split(":")
        output = Output.objects.get(transaction=tx, out_idx=out_idx)
        ctx["streamitem"] = output.streamitem
        if self.kwargs.get("stream") == "iscc":
            cid = output.streamitem.keys[1]
            smart_licenses = StreamItem.objects.filter(
                keys__1__contains=cid, stream="smart-license"
            )
            ctx["smartlicenses"] = smart_licenses
        return ctx


class StreamDetailView(TemplateView):
    template_name = "mex/stream_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        ctx["stream_details"] = api.liststreams(ctx["stream"])[0]
        ctx["stream_items"] = list(reversed(api.liststreamitems(ctx["stream"])))
        for key, item in enumerate(ctx["stream_items"]):
            if "blocktime" in item:
                ctx["stream_items"][key][
                    "formatted_time"
                ] = datetime.datetime.fromtimestamp(item["blocktime"])
            if item["data"]:
                try:
                    ctx["stream_items"][key]["formatted_data"] = ubjson.loadb(
                        unhexlify(item["data"])
                    )
                except Exception as e:
                    ctx["stream_items"][key]["formatted_data"] = item["data"]
        return ctx


class TokenDetailView(TemplateView):
    template_name = "mex/token_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        ctx["token_details"] = api.listassets(ctx["token"])[0]
        return ctx
