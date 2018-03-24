# -*- coding: utf-8 -*-
import datetime

from django.views.generic import DetailView, TemplateView
from django_tables2 import MultiTableMixin, SingleTableView

from mex.rpc import get_client
from mex.tables import BlockTable, TransactionTable, AddressTable
from mex.models import Block, Transaction, Address
from mex.utils import public_key_to_address


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

    def get_context_data(self, **kwargs):
        api = get_client()
        ctx = super().get_context_data(**kwargs)
        ctx['details'] = api.getblock(ctx['block'].hash, 1)
        ctx['formattedtime'] = datetime.datetime.fromtimestamp(ctx['details']['time'])
        ctx['num_transactions'] = len(ctx['details']['tx'])
        return ctx


class TransactionDetailView(DetailView):
    model = Transaction
    slug_field = 'hash'
    slug_url_kwarg = 'hash'

    def get_context_data(self, **kwargs):
        api = get_client()
        ctx = super().get_context_data(**kwargs)
        ctx['details'] = api.getrawtransaction(ctx['transaction'].hash, 4)
        blockchain_params = api.getblockchainparams()
        pubkeyhash_version = blockchain_params['address-pubkeyhash-version']
        checksum_value = blockchain_params['address-checksum-value']
        ctx['formattedBlocktime'] = datetime.datetime.fromtimestamp(ctx['details']['blocktime'])
        ctx['formattedVin'] = []
        ctx['formattedVout'] = []
        for index, vin in enumerate(ctx['details']['vin']):
            address = 'N/A'
            if 'scriptSig' in vin:
                public_key = vin['scriptSig']['asm'].split(' ')[1]
                address = public_key_to_address(public_key, pubkeyhash_version, checksum_value)
            ctx['formattedVin'].append({
                'index': index,
                'address': address,
                'transaction': vin['txid'] if 'txid' in vin else ''
            })
        for index, vout in enumerate(ctx['details']['vout']):
            address = 'N/A'
            if 'scriptPubKey' in vout and 'addresses' in vout['scriptPubKey']:
                address = ', '.join(vout['scriptPubKey']['addresses'])
            ctx['formattedVout'].append({
                'index': index,
                'address': address,
                'transaction': vin['txid'] if 'txid' in vin else '',
                'amount': vout['value']
            })
        return ctx


class AddressDetailView(DetailView):
    model = Address
    slug_field = 'address'
    slug_url_kwarg = 'address'
