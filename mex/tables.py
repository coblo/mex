# -*- coding: utf-8 -*-
from datetime import datetime
import pytz
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_tables2 import tables, Column, DateTimeColumn, LinkColumn
from mex.models import Block, Transaction, Address


class BlockTable(tables.Table):

    height = LinkColumn(verbose_name="Height", orderable=True)
    time = DateTimeColumn(
        verbose_name="Time (UTC)", format="Y-m-d H:i:s", orderable=True
    )
    miner = LinkColumn(verbose_name=settings.MEX_MINER)
    txcount = Column(verbose_name="TXs", orderable=True)
    size = Column(orderable=True)

    class Meta:
        model = Block
        fields = ("height", "time", "miner", "txcount", "size")
        order_by = ("-height",)
        attrs = {"class": "table table-sm table-striped table-hover"}
        orderable = False

    def render_height(self, record=None):
        link = reverse("block-detail", args=[str(record.hash)])
        return mark_safe(
            '<a href="{}" class="badge badge-info"><i class="fas fa-cube"></i>  {}</a>'.format(
                link, record.height
            )
        )

    def render_miner(self, record=None):
        link = reverse("address-detail", args=[str(record.miner)])
        return mark_safe('<a href="{}">{}</a>'.format(link, record.miner))


class TransactionTable(tables.Table):

    block = LinkColumn(verbose_name="Block")
    hash = LinkColumn(verbose_name="TX Hash")
    idx = Column(verbose_name="IDX")

    class Meta:
        model = Transaction
        fields = ("block", "hash", "idx")
        attrs = {"class": "table table-sm table-striped table-hover"}
        order_by = ("-block", "idx")

    def render_block(self, record=None):
        link = reverse("block-detail", args=[str(record.block.hash)])
        return mark_safe(
            '<a href="{}" class="badge badge-info"><i class="fas fa-cube"></i>  {}</a>'.format(
                link, record.block.height
            )
        )


class AddressTable(tables.Table):

    address = LinkColumn(verbose_name="Address")
    balance = Column(verbose_name="Balance", orderable=True)

    class Meta:
        model = Address
        fields = ("address", "balance")
        attrs = {"class": "table table-sm table-striped table-hover"}
        order_by = ("-balance",)
        orderable = False

    def render_balance(self, value):
        return "%s %s" % (value, settings.MEX_SYMBOL)


class ListStreamTable(tables.Table):

    name = Column(verbose_name="Stream")
    details = Column(verbose_name="Description")
    creators = Column(verbose_name="Creator", accessor="creators__0")
    items = Column()
    restrict = Column(verbose_name="Open")

    streams = {
        "alias": "Address alias registrations",
        "DOI": "Open Stream that maps DOI to ISCC",
        "ISBN": "Open Stream that maps ISBN to ISCC",
        "iscc": "Public ISCC Registry",
        "smart-license": "Public Smart License Registry",
        "test": "Stream for test data",
        "timestamp": "Open timestamping with SHA-256",
    }

    class Meta:
        attrs = {"class": "table table-sm table-striped table-hover"}

    def render_name(self, value):
        return format_html('<a href="/stream/{}">{}</a>', value, value)

    def render_details(self, value, record):
        value = value.get("info")
        if not value:
            value = self.streams.get(record["name"])
        return value

    def render_restrict(self, value):
        return not value["read"]


class StreamItemApiTable(tables.Table):

    txid = Column(verbose_name="TxID", orderable=False)
    time = Column(verbose_name="Time (UTC)", orderable=True)
    keys = Column(verbose_name="Key(s)", orderable=False)
    data = Column(verbose_name="Data", orderable=False)

    class Meta:
        attrs = {"class": "table table-sm table-striped table-hover"}
        order_by = ("-time",)

    def render_txid(self, value):
        lnk = '<a href="/tx/{}">{}</a>'.format(value, value[:7])
        return mark_safe(lnk)

    def render_time(self, value):
        value = datetime.fromtimestamp(value, tz=pytz.utc)
        value = value.strftime("%Y-%m-%d %H:%M:%S")
        return value

    def render_keys(self, value, record):
        if isinstance(value, list):
            value = "-".join(value)
        value = value[:55]
        key = "{}:{}".format(record["txid"], record["vout"])
        stream = record["stream"]
        lnk = '<a href="/stream/{}/{}">{}</a>'.format(stream, key, value)

        return mark_safe(lnk)

    def render_data(self, value):
        if isinstance(value, str):
            return value[:64]
        data = value.get("json")
        if data:
            title = (
                data.get("title")
                or data.get("ISCC")
                or data.get("ISBN")
                or data.get("comment")
            )
        else:
            title = value.get("text")
        if not title:
            title = str(value)
        return title[:64] if title else ""
