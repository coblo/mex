# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget
from mex.models import Block, Transaction, Output, Address, Input, Stream, StreamItem
from django.conf.locale.en import formats as en_formats

from mex.paginator import TimeLimitedPaginator
from mex.utils import render_json


en_formats.DATETIME_FORMAT = "Y-m-d H:i"


class BaseModelAdmin(admin.ModelAdmin):

    actions = None

    formfield_overrides = {
        JSONField: {"widget": PrettyJSONWidget(attrs={"initial": "parsed"})}
    }

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class TransactionInline(admin.TabularInline):
    """TODO: tidy up with https://stackoverflow.com/a/5556813"""

    model = Transaction
    verbose_name = "Transaction"
    verbose_name_plural = "Transactions"
    fields = ["hash", "idx"]
    readonly_fields = ("hash", "idx")
    show_change_link = True

    class Media:
        css = {"all": ("admin_tweaks.css",)}

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Block)
class BlockAdmin(BaseModelAdmin):
    list_display = "height", "hash", "miner", "time", "txcount", "size"
    fields = list_display + ("merkleroot",)
    readonly_fields = fields
    search_fields = "miner", "hash"
    inlines = [TransactionInline]


class InputInline(admin.TabularInline):
    """TODO: tidy up with https://stackoverflow.com/a/5556813"""

    model = Input
    verbose_name = "Input"
    verbose_name_plural = "Inputs"
    fieldsets = (
        ("Hello World", {"fields": ("transaction", "spends", "value", "coinbase")}),
    )
    readonly_fields = "transaction", "spends", "value", "coinbase"
    show_change_link = True

    class Media:
        css = {"all": ("admin_tweaks.css",)}

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OutputInline(admin.TabularInline):
    """TODO: tidy up with https://stackoverflow.com/a/5556813"""

    model = Output
    verbose_name = "Output"
    verbose_name_plural = "Outputs"
    fields = ["transaction", "out_idx", "value", "address", "spent"]
    readonly_fields = fields
    show_change_link = True

    class Media:
        css = {"all": ("admin_tweaks.css",)}

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(BaseModelAdmin):
    list_display = ("hash", "block", "idx")
    readonly_fields = list_display
    search_fields = ["block__hash", "hash"]
    inlines = [InputInline, OutputInline]


@admin.register(Output)
class OutputAdmin(BaseModelAdmin):
    list_display = ("id", "transaction", "out_idx", "address", "value", "spent")
    readonly_fields = list_display

    list_filter = ("spent",)
    search_fields = ("address__address",)


@admin.register(Input)
class InputAdmin(BaseModelAdmin):
    list_display = ("id", "transaction", "spends", "coinbase")
    readonly_fields = list_display

    list_filter = ("coinbase",)


@admin.register(Address)
class AddressAdmin(BaseModelAdmin):
    list_display = ("address", "balance")
    readonly_fields = list_display

    search_fields = ("address",)

    def get_queryset(self, request):
        qs = super(AddressAdmin, self).get_queryset(request)
        return qs.with_balance()

    def balance(self, obj):
        return obj.balance

    balance.admin_order_field = "balance"


@admin.register(Stream)
class StreamAdmin(BaseModelAdmin):
    list_display = (
        "name",
        "description",
        "restrict",
        "keys",
        "items",
        "confirmed",
        "publishers",
        "subscribed",
        "synchronized",
        "monitor",
        "show",
    )

    list_editable = ("monitor", "show")
    readonly_fields = (
        "confirmed",
        "createtxid",
        "creators",
        "details",
        "indexes",
        "items",
        "keys",
        "name",
        "publishers",
        "restrict",
        "retrieve",
        "salted",
        "streamref",
        "subscribed",
        "synchronized",
    )

    raw_id_fields = ("createtxid", "creators")
    fieldsets = (
        (None, {"fields": ("name", "custom_description", "monitor", "show")}),
        ("Meta", {"fields": (("streamref", "creators"), "createtxid", "details")}),
        (
            "Stats",
            {"fields": ("items", "confirmed", "publishers", "keys", "synchronized")},
        ),
        (
            "Configuration",
            {"fields": ("indexes", "restrict", "retrieve", "salted", "subscribed")},
        ),
    )


@admin.register(StreamItem)
class StreamItemAdmin(BaseModelAdmin):
    list_display = ("time", "stream", "keys", "offchain", "available", "valid")
    search_fields = ("keys",)
    list_filter = ("stream",)
    raw_id_fields = ("output", "publishers", "stream")
    exclude = ("data",)
    readonly_fields = (
        "output",
        "stream",
        "time",
        "keys",
        "data_prettified",
        "publishers",
        "available",
        "offchain",
        "valid",
    )
    show_full_result_count = False
    list_select_related = ("stream",)
    paginator = TimeLimitedPaginator

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
        qs = queryset.filter(keys__overlap=[search_term]).distinct()
        return qs, True

    def data_prettified(self, instance):
        """Function to display pretty version of our data"""
        return render_json(instance.data)

    data_prettified.short_description = "Data"
