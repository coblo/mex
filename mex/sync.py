# -*- coding: utf-8 -*-
from datetime import datetime
import pytz
from django.conf import settings
from django.db import InterfaceError, OperationalError
from django.db import connection

from mex.exceptions import SyncError
from mex.rpc import get_client
from mex.models import Block, Transaction, Output, Address, Input, Stream, StreamItem
import logging

from mex.tools import batchwise

log = logging.getLogger("mex.sync")


def clean_reorgs(horizon=settings.MEX_SYNC_HORIZON):
    """
    Clean chain reorganizations up to `horizon` number of blocks in the past.

    First we compare the latest `horizon` block hashes from the database with
    those form the authoritative node. If we find a difference we will delete
    all the blocks starting at the oldest differing block. Deleteing those
    blocks will automatically cascade throuth the datamodel and delete all
    dependant transactions, inputs and outputs.
    """
    log.info("clean reorgs with horizon {}".format(horizon))
    api = get_client()

    node_height = api.getblockcount()
    db_height = Block.get_db_height()
    if db_height > node_height:
        log.warning("database is ahead of node")
        return

    db_blocks = list(
        Block.objects.order_by("-height").values_list("height", "hash")[:horizon]
    )
    if not db_blocks:
        log.info("database has no block data")
        return

    db_height = db_blocks[0][0]
    db_horizon = db_blocks[-1][0]

    horizon_range = "%s-%s" % (db_horizon, db_height)
    node_data = api.listblocks(horizon_range, False)
    node_blocks = [(b["height"], b["hash"]) for b in reversed(node_data)]
    difference = set(db_blocks).difference(set(node_blocks))

    if not difference:
        log.info("no reorgs found")
        return

    fork_height = min(difference)[0]
    log.info("database reorg from height %s" % fork_height)
    Block.objects.filter(height__gte=fork_height).delete()


def sync_blocks(batch_size=1000):

    api = get_client()
    db_height = Block.get_db_height()
    node_height = api.getblockcount()

    if db_height == node_height:
        log.info("no new blocks to sync")
        return

    if db_height > node_height:
        raise SyncError("database is ahead of node")

    log.info("sync blocks %s-%s" % (db_height + 1, node_height))

    block_counter = 0

    existing_addrs = set(Address.objects.values_list("address", flat=True))

    from_to = range(db_height + 1, node_height)
    for batch in batchwise(from_to, batch_size=batch_size):
        log.info("sync blocks batch %s" % batch)
        block_objs = []
        for block_data in api.listblocks(batch, True):

            miner_addr = block_data["miner"]
            if miner_addr not in existing_addrs:
                Address.objects.create(address=miner_addr)
                existing_addrs.add(miner_addr)

            blocktime = datetime.fromtimestamp(block_data["time"], tz=pytz.utc)

            block_objs.append(
                Block(
                    height=block_data["height"],
                    hash=block_data["hash"],
                    merkleroot=block_data["merkleroot"],
                    miner_id=miner_addr,
                    time=blocktime,
                    txcount=block_data["txcount"],
                    size=block_data["size"],
                )
            )
            block_counter += 1

        Block.objects.bulk_create(block_objs, batch_size=batch_size)

    log.info("imported %s blocks" % block_counter)


def sync_transactions():
    api = get_client()
    queryset = (
        Block.objects.filter(transactions__isnull=True).only("hash").order_by("height")
    )
    if not queryset.exists():
        return
    addrs_existing = set(Address.objects.values_list("address", flat=True))
    log.info("sync transactions from %s blocks" % queryset.count())
    tx_counter = 0
    out_counter = 0
    in_counter = 0
    addr_counter = 0

    for block_obj in queryset:

        block_data = api.getblock(block_obj.hash, 4)
        tx_hashes = [item["txid"] for item in block_data["tx"]]
        tx_objs = []

        for tx_idx, tx_hash in enumerate(tx_hashes):
            tx_obj = Transaction(hash=tx_hash, block=block_obj, idx=tx_idx)
            tx_objs.append(tx_obj)
            tx_counter += 1

        # only postgres sets primary ids for tx_objs here.
        Transaction.objects.bulk_create(tx_objs)

        tx_objs_by_hash = {txo.hash: txo for txo in tx_objs}

        # create outputs for all transactions in block
        out_objs = []
        for tx_data in block_data["tx"]:
            if tx_data is None:
                continue

            tx_obj = tx_objs_by_hash[tx_data["txid"]]

            # Create new outputs
            for out_entry in tx_data["vout"]:
                value = out_entry.get("value")

                try:
                    address = out_entry["scriptPubKey"]["addresses"][0]
                except KeyError:
                    address = None
                out_idx = out_entry["n"]

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
        for tx_data in block_data["tx"]:
            if tx_data is None:
                continue

            tx_obj = tx_objs_by_hash[tx_data["txid"]]
            # Create input and mark spent outputs
            for vin_entry in tx_data["vin"]:
                txid = vin_entry.get("txid")
                coinbase = vin_entry.get("coinbase")
                vout = vin_entry.get("vout")
                if txid:
                    out = Output.objects.get(transaction__hash=txid, out_idx=vout)

                    in_objs.append(
                        Input(transaction=tx_obj, spends=out, coinbase=False)
                    )
                    in_counter += 1
                    out.spent = True
                    out.save()
                if coinbase:
                    in_objs.append(Input(transaction=tx_obj, coinbase=True))
                    in_counter += 1
        Input.objects.bulk_create(in_objs)
        log.info(
            "imported %s transactions from block %s" % (len(tx_objs), block_obj.height)
        )

    log.info("imported %s transactions" % tx_counter)
    log.info("imported %s outputs" % out_counter)
    log.info("imported %s inputs" % in_counter)
    log.info("imported %s addresses" % addr_counter)


def sync_streams():
    api = get_client()
    streams = api.liststreams("*", verbose=True)
    for stream in streams:

        # Key for update
        name = stream.pop("name")

        # Set fk by id
        stream["createtxid_id"] = stream.pop("createtxid")
        creators = stream.pop("creators")
        stream_obj, created = Stream.objects.update_or_create(
            name=name, defaults=stream
        )

        creator_objs = Address.objects.filter(address__in=creators)
        if creator_objs.exists():
            stream_obj.creators.add(*creator_objs)
    log.info("imported %s streams" % len(streams))


def sync_stream_items():
    """Synchronize stream data for all monitored streams."""

    api = get_client()
    streams = Stream.objects.filter(monitor=True)
    for stream_obj in streams:
        log.info("import items for stream %s" % stream_obj.name)
        height = StreamItem.objects.filter(stream=stream_obj).count()
        total_new_items = 0
        while True:
            raw_items = api.liststreamitems(
                stream_obj.name, verbose=True, count=100, start=height
            )

            if not raw_items:
                break
            new_stream_items = {}

            # collect referenced outputs
            txids_raw = [r['txid'] for r in raw_items]
            outputs = Output.objects.filter(transaction_id__in=txids_raw).only(
                'id', 'transaction_id', 'out_idx'
            )
            # Map txid/out_idx composite to primary key of Output
            outputs = {f'{o.transaction_id}{o.out_idx}': o.pk for o in outputs}
            for raw_item in raw_items:
                if raw_item["confirmations"] == 0:
                    continue

                # Transform raw data
                txid = raw_item.pop("txid")
                vout = raw_item.pop("vout")

                raw_item["output_id"] = outputs[f'{txid}{vout}']
                raw_item["stream_id"] = stream_obj.pk
                raw_item["time"] = datetime.fromtimestamp(raw_item["time"], tz=pytz.utc)
                del raw_item["blockhash"]
                del raw_item["blockindex"]
                del raw_item["blocktime"]
                del raw_item["confirmations"]
                del raw_item["timereceived"]

                publishers = raw_item.pop("publishers")

                s_item_obj = StreamItem(**raw_item)
                new_stream_items[s_item_obj] = publishers

            StreamItem.objects.bulk_create(new_stream_items.keys())
            for item_obj, publishers in new_stream_items.items():
                item_obj.publishers.add(*publishers)
            total_new_items += len(new_stream_items.keys())
            height += 100
        if total_new_items:
            log.info(
                "imported %s items from stream %s"
                % (total_new_items, stream_obj.name)
            )


if __name__ == "__main__":
    import time
    import timeit
    from mex.tools import init_logging

    init_logging()

    while True:
        log.info("starting sync round")
        start = timeit.default_timer()
        try:
            clean_reorgs()
            sync_blocks()
            sync_transactions()
            sync_streams()
            sync_stream_items()
            stop = timeit.default_timer()
            runtime = stop - start
            log.info("finished sync round in %s seconds" % runtime)
        except (InterfaceError, OperationalError) as e:
            log.info(repr(e))
            log.info("try to gracefully reconnect to db")
            try:
                connection.connect()
                log.info("reconnect to db success")
            except Exception as e:
                log.warning("reconnect to db failed")
        except Exception as e:
            log.error(repr(e))
        time.sleep(10)
