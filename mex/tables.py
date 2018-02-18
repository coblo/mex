# -*- coding: utf-8 -*-
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2 import tables, Column, DateTimeColumn, LinkColumn
from mex.models import Block, Transaction, Address


class BlockTable(tables.Table):

    height = LinkColumn(verbose_name='Height', orderable=True)
    time = DateTimeColumn(verbose_name='Time (UTC)', format="Y-m-d H:i", orderable=True)
    miner = LinkColumn(verbose_name='Miner')
    txcount = Column(verbose_name='TXs', orderable=True)
    size = Column(orderable=True)

    class Meta:
        model = Block
        fields = ('height', 'time', 'miner', 'txcount', 'size', )
        order_by = '-height',
        attrs = {'class': 'table table-sm table-striped table-hover'}
        orderable = False

    def render_height(self, record=None):
        link = reverse('block-detail', args=[str(record.hash)])
        return mark_safe(
            '<a href="{}" class="badge badge-info"><i class="fas fa-cube"></i>  {}</a>'
                .format(link, record.height))

    def render_miner(self, record=None):
        link = reverse('address-detail', args=[str(record.miner)])
        return mark_safe(
            '<a href="{}">{}</a>'
                .format(link, record.miner))


class TransactionTable(tables.Table):

    block = LinkColumn(verbose_name='Block')
    hash = LinkColumn(verbose_name='TX Hash')
    idx = Column(verbose_name='IDX')

    class Meta:
        model = Transaction
        fields = ('block', 'hash', 'idx',)
        attrs = {'class': 'table table-sm table-striped table-hover'}
        order_by = ('-block', 'idx')

    def render_block(self, record=None):
        link = reverse('block-detail', args=[str(record.block.hash)])
        return mark_safe(
            '<a href="{}" class="badge badge-info"><i class="fas fa-cube"></i>  {}</a>'
                .format(link, record.block.height))


class AddressTable(tables.Table):

    address = LinkColumn(verbose_name='Address')
    balance = Column(verbose_name='Balance', orderable=True)

    class Meta:
        model = Address
        fields = ('address', 'balance')
        attrs = {'class': 'table table-sm table-striped table-hover'}
        order_by = ('-balance',)
        orderable = False

