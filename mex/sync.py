# -*- coding: utf-8 -*-
from datetime import datetime
import pytz
from mex.rpc import get_client
from mex.models import Block, Transaction, Output, Address, Input, Stream
import logging

from mex.tools import batchwise

log = logging.getLogger('mex.sync')


HORIZON = 100


def clean_reorgs(horizon=HORIZON):
    """
    Clean chain reorganizations up to `horizon` number of blocks in the past.

    First we compare the latest `horizon` block hashes from the database with
    those form the authoritative node. If we find a difference we will delete
    all the blocks starting at the oldest differing block. Deleteing those
    blocks will automatically cascade throuth the datamodel and delete all
    dependant transactions, inputs and outputs.
    """
    log.info('clean reorgs')
    db_blocks = list(
        Block.objects
            .order_by('-height')
            .values_list('height', 'hash')[:horizon]
    )
    if not db_blocks:
        return

    db_height = db_blocks[0][0]
    db_horizon = db_blocks[-1][0]

    api = get_client()
    node_data = api.listblocks(f"{db_horizon}-{db_height}", False)['result']
    node_blocks = [(b['height'], b['hash']) for b in reversed(node_data)]
    difference = set(db_blocks).difference(set(node_blocks))

    if not difference:
        return

    fork_height = min(difference)[0]
    log.info(f'db reorg from height {fork_height} - deleting stale blocks!')
    Block.objects.filter(height__gte=fork_height).delete()


def sync_blocks(batch_size=1000):
    api = get_client()

    db_height = Block.get_height()
    node_height = api.getblockcount()['result']
    if db_height == node_height:
        log.info('no new blocks to sync')
        return

    log.info(f'sync blocks {db_height+1}-{node_height}')

    block_counter = 0

    for batch in batchwise(range(db_height + 1, node_height), batch_size=batch_size):
        block_objs = []
        for block_data in api.listblocks(batch, verbose=False)['result']:
            del block_data['confirmations']
            block_data['time'] = datetime.utcfromtimestamp(
                block_data['time']).replace(tzinfo=pytz.utc)
            block_objs.append(Block(**block_data))
            block_counter += 1

        Block.objects.bulk_create(block_objs, batch_size=batch_size)

    log.info(f'imported {block_counter} blocks')


def sync_transactions():
    api = get_client()
    queryset = Block.objects\
        .filter(transactions__isnull=True)\
        .only('hash')\
        .order_by('height')\

    if not queryset.exists():
        return
    addrs_existing = set(Address.objects.values_list('address', flat=True))
    log.info(f'sync transactions from {queryset.count()} blocks')
    tx_counter = 0
    out_counter = 0
    in_counter = 0
    addr_counter = 0

    for block_obj in queryset:

        block_data = api.getblock(block_obj.hash, 4)['result']
        tx_hashes = [item['txid'] for item in block_data['tx']]
        tx_objs = []

        for tx_idx, tx_hash in enumerate(tx_hashes):
            tx_obj = Transaction(
                hash=tx_hash,
                block=block_obj,
                idx=tx_idx
            )
            tx_objs.append(tx_obj)
            tx_counter += 1

        # only postgres sets primary ids for tx_objs here.
        Transaction.objects.bulk_create(tx_objs)

        tx_objs_by_hash = {txo.hash: txo for txo in tx_objs}

        # create outputs for all transactions in block
        out_objs = []
        for tx_data in block_data['tx']:
            if tx_data is None:
                continue

            tx_obj = tx_objs_by_hash[tx_data['txid']]

            # Create new outputs
            for out_entry in tx_data['vout']:
                value = out_entry.get('value')

                try:
                    address = out_entry['scriptPubKey']['addresses'][0]
                except KeyError:
                    address = None
                out_idx = out_entry['n']

                if address and address not in addrs_existing:
                    Address.objects.create(address=address)
                    addrs_existing.add(address)
                    addr_counter += 1

                out_objs.append(
                    Output(
                        transaction=tx_obj,
                        out_idx=out_idx,
                        value=value,
                        address_id=address,
                    )
                )
                out_counter += 1

        # postgres needed to set object ids
        Output.objects.bulk_create(out_objs)

        # create inputs for all transactions in block
        in_objs = []
        for tx_data in block_data['tx']:
            if tx_data is None:
                continue

            tx_obj = tx_objs_by_hash[tx_data['txid']]
            # Create input and mark spent outputs
            for vin_entry in tx_data['vin']:
                txid = vin_entry.get('txid')
                coinbase = vin_entry.get('coinbase')
                vout = vin_entry.get('vout')
                if txid:
                    out = Output.objects.get(transaction__hash=txid, out_idx=vout)

                    in_objs.append(
                        Input(
                            transaction=tx_obj,
                            spends=out,
                            coinbase=False
                        )
                    )
                    in_counter += 1
                    out.spent = True
                    out.save()
                if coinbase:
                    in_objs.append(Input(transaction=tx_obj, coinbase=True))
                    in_counter += 1
        Input.objects.bulk_create(in_objs)

    # Output.objects\
    #     .filter(inputs_for_output__isnull=False)\
    #     .update(spent=True)

    log.info(f'imported {tx_counter} transactions')
    log.info(f'imported {out_counter} outputs')
    log.info(f'imported {in_counter} inputs')
    log.info(f'imported {addr_counter} addresses')


def sync_streams():
    log.info('sync streams')
    api = get_client()
    data = api.liststreams()
    for entry in data['result']:
        name = entry.pop('name')
        Stream.objects.update_or_create(name=name, defaults=entry)
    log.info(f"imported/updated {len(data['result'])} streams")


if __name__ == '__main__':
    import time
    import timeit
    from mex.tools import init_logging

    init_logging()

    while True:
        log.info(f'starting sync round')
        start = timeit.default_timer()
        clean_reorgs()
        sync_blocks()
        sync_transactions()
        sync_streams()
        stop = timeit.default_timer()
        runtime = stop - start
        log.info(f'finished sync round in {runtime} seconds')
        time.sleep(10)
