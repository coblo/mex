# -*- coding: utf-8 -*-
import datetime
import ubjson
from binascii import unhexlify

from django.views.generic import DetailView, TemplateView
from django_tables2 import MultiTableMixin, SingleTableView

from mex.rpc import get_client
from mex.tables import BlockTable, TransactionTable, AddressTable
from mex.models import Block, Transaction, Address, Output
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


class StreamListView(TemplateView):
    template_name = 'mex/stream_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        streams = api.liststreams()
        ctx['streams'] = sorted(streams, key=lambda k: -k['items'])
        return ctx


class TokenListView(TemplateView):
    template_name = 'mex/token_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        ctx['tokens'] =  api.listassets()
        return ctx


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        address = ctx['address'].address
        ctx['amount_blocks'] = Block.objects.filter(miner=address).count()
        api = get_client()
        blocks = api.getinfo().blocks
        ctx['miner'] = False
        for perm in api.listpermissions("mine"):
            if perm['address'] == address and perm['startblock'] < blocks and perm['endblock'] > blocks:
                ctx['miner'] = True
        ctx['admin'] = False
        for perm in api.listpermissions("admin"):
            if perm['address'] == address and perm['startblock'] < blocks and perm['endblock'] > blocks:
                ctx['admin'] = True
        qs = super().get_queryset()
        ctx['balance'] = qs.with_balance().filter(address=address).first().balance
        last_out = Output.objects.filter(address=address).order_by('-transaction__block__time')[:10]
        ctx['last_tx'] = []
        for out in last_out:
            ctx['last_tx'].append({
                'tx': out.transaction.hash,
                'time': out.transaction.block.time,
                'hash': out.transaction.block.hash,
                'height': out.transaction.block.height
            })
        return ctx

class StreamDetailView(TemplateView):
    template_name = 'mex/stream_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        ctx['stream_details'] = api.liststreams(ctx['stream'])[0]
        ctx['stream_items'] = api.liststreamitems(ctx['stream'])
        for key, item in enumerate(ctx['stream_items']):
            ctx['stream_items'][key]['formatted_time'] = datetime.datetime.fromtimestamp(item['blocktime'])
            if item['data']:
                try:
                    ctx['stream_items'][key]['formatted_data'] = ubjson.loadb(unhexlify(item['data']))
                except Exception as e:
                    ctx['stream_items'][key]['formatted_data'] = item['data']
        return ctx


class TokenDetailView(TemplateView):
    template_name = 'mex/token_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        api = get_client()
        ctx['token_details'] = api.listassets(ctx['token'])[0]
        # for key, item in enumerate(ctx['stream_items']):
        #     ctx['stream_items'][key]['formatted_time'] = datetime.datetime.fromtimestamp(item['blocktime'])
        #     if item['data']:
        #         try:
        #             ctx['stream_items'][key]['formatted_data'] = ubjson.loadb(unhexlify(item['data']))
        #         except Exception as e:
        #             ctx['stream_items'][key]['formatted_data'] = item['data']
        return ctx