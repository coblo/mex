# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget
from mex.models import Block, Transaction, Output, Address, Input
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
