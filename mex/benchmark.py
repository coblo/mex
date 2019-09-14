# -*- coding: utf-8 -*-
"""
Benchmarks to get a feeling for the bootlenecks.

Testnet rpc scan results at node height 59354:

RPC listblocks: 7.382926345811435
RPC listblocks verbose: 27.969617406454475
RPC full getblock scan verbose=1: 135.90371246640606
RPC full getblock scan verbose=4: 180.16512355423876
RPC full getrawtransaction scan verbose=4: 369.658727571638

Insight:

`getblock` with verbose=4 includes transaction details. We can avoid api
call overhead by not calling `getrawtransaction` for each individual tx.
"""
import logging
import timeit
from mex.rpc import get_client


log = logging.getLogger("mex.benchmark")


def benchmark_rpc():
    api = get_client()
    node_height = api.getblockcount()["result"]
    log.info(f"Node height: {node_height}")

    log.info("Starting benchmark. Please be patient!")
    start = timeit.default_timer()
    blocks = api.listblocks("-" + str(node_height), verbose=False)["result"]
    stop = timeit.default_timer()
    runtime = stop - start
    log.info(f"RPC listblocks: {runtime}")

    start = timeit.default_timer()
    blocks = api.listblocks("-" + str(node_height), verbose=True)["result"]
    stop = timeit.default_timer()
    runtime = stop - start
    log.info(f"RPC listblocks verbose: {runtime}")

    block_hashes = [item["hash"] for item in blocks]
    tx_hashes = []

    start = timeit.default_timer()
    for block_hash in block_hashes:
        data = api.getblock(block_hash, verbose=1)["result"]["tx"]
        tx_hashes.extend(data)  # pre-collect for getrawtransactions
    stop = timeit.default_timer()
    runtime = stop - start
    log.info(f"RPC full getblock scan verbose=1: {runtime}")

    start = timeit.default_timer()
    for block_hash in block_hashes:
        data = api.getblock(block_hash, verbose=4)
    stop = timeit.default_timer()
    runtime = stop - start
    log.info(f"RPC full getblock scan verbose=4: {runtime}")

    start = timeit.default_timer()
    for tx_hash in tx_hashes:
        data = api.getrawtransaction(tx_hash, verbose=1)["result"]
    stop = timeit.default_timer()
    runtime = stop - start
    log.info(f"RPC full getrawtransaction scan verbose=4: {runtime}")


if __name__ == "__main__":
    from mex.tools import init_logging, batchwise

    init_logging()
    benchmark_rpc()
