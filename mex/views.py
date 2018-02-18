# -*- coding: utf-8 -*-
from django.views.generic import DetailView, TemplateView
from django_tables2 import MultiTableMixin, SingleTableView

from mex.rpc import get_client
from mex.tables import BlockTable, TransactionTable, AddressTable
from mex.models import Block, Transaction, Address


class StatusView(TemplateView):
    template_name = 'mex/status.html'

    def get_context_data(self, **kwargs):
        api = get_client()
        ctx = super().get_context_data(**kwargs)
        ctx['info'] = api.getinfo()
        return ctx


class HomeView(MultiTableMixin, TemplateView):

    template_name = 'mex/home.html'
    tables = [
        BlockTable(Block.objects.all()),
        TransactionTable(Transaction.objects.all())
    ]
    table_pagination = {
        'per_page': 6,
    }


class TableBlocks(SingleTableView):
    template_name = 'mex/table_simple.html'
    model = Block
    table_class = BlockTable
    paginate_by = 6


class TableTransactions(SingleTableView):
    template_name = 'mex/table_simple.html'
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


class BlockDetailView(DetailView):

    model = Block
    slug_field = 'hash'
    slug_url_kwarg = 'hash'


class TransactionDetailView(DetailView):
    model = Transaction
    slug_field = 'hash'
    slug_url_kwarg = 'hash'


class AddressDetailView(DetailView):
    model = Address
    slug_field = 'address'
    slug_url_kwarg = 'address'
