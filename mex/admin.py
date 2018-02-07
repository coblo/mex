# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db.models import Sum, Q
from mex.models import Block, Transaction, Output, Address, Input, Stream
from django.conf.locale.en import formats as en_formats


en_formats.DATETIME_FORMAT = "Y-m-d H:m:s"


class BaseModelAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False


class TransactionInline(admin.TabularInline):
    """TODO: tidy up with https://stackoverflow.com/a/5556813"""
    model = Transaction
    verbose_name = "Transaction"
    verbose_name_plural = "Transactions"
    fields = ['hash', 'idx']
    readonly_fields = ('hash', 'idx')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Block)
class BlockAdmin(BaseModelAdmin):
    list_display = (
        'id', 'height', 'hash', 'miner', 'time', 'txcount',
    )
    readonly_fields = list_display
    search_fields = ['miner', 'hash',]
    inlines = [TransactionInline]


class InputInline(admin.TabularInline):
    """TODO: tidy up with https://stackoverflow.com/a/5556813"""
    model = Input
    verbose_name = "Input"
    verbose_name_plural = "Inputs"
    fields = ['transaction', 'spends', 'value', 'coinbase']
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OutputInline(admin.TabularInline):
    """TODO: tidy up with https://stackoverflow.com/a/5556813"""
    model = Output
    verbose_name = "Output"
    verbose_name_plural = "Outputs"
    fields = ['transaction', 'out_idx', 'value', 'address', 'spent']
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(BaseModelAdmin):
    list_display = (
       'hash', 'block', 'idx',
    )
    readonly_fields = list_display
    search_fields = ['block__hash', 'hash']
    inlines = [InputInline, OutputInline]


@admin.register(Output)
class OutputAdmin(BaseModelAdmin):
    list_display = (
       'id', 'transaction', 'out_idx', 'address', 'value', 'spent'
    )
    readonly_fields = list_display

    list_filter = ('spent',)
    search_fields = ('address__address',)


@admin.register(Input)
class InputAdmin(BaseModelAdmin):
    list_display = (
       'id', 'transaction', 'spends', 'coinbase',
    )
    readonly_fields = list_display

    list_filter = ('coinbase',)


@admin.register(Address)
class AddressAdmin(BaseModelAdmin):
    list_display = (
      'address', 'balance'
    )
    readonly_fields = list_display

    search_fields = ('address', )

    def get_queryset(self, request):
        qs = super(AddressAdmin, self).get_queryset(request)
        return qs.annotate(
            balance=Sum(
                'outputs_for_addr__value',
                filter=Q(outputs_for_addr__spent=False)
            )
        )

    def balance(self, obj):
        return obj.balance
    balance.admin_order_field = 'balance'


@admin.register(Stream)
class StreamAdmin(BaseModelAdmin):

    list_display = [
        'name',
        'createtxid',
        'creators',
        'open',
        'items',
        'keys',
        'publishers'
    ]

    readonly_fields = list_display + [
        'confirmed',
        'details',
        'streamref',
        'subscribed',
        'synchronized'
    ]
