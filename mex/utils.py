# -*- coding: utf-8 -*-
import json
from _sha256 import sha256
from binascii import unhexlify
from hashlib import new

import base58
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer


def public_key_to_address(public_key: str, pkhv, cv):
    """Create Address from a public key.

    Implementation of http://bit.ly/2hH1UUY

    :param str public_key: hex encoded ECDSA public key
    :param str pkhv: address-pubkeyhash-version of chain
    :param str cv: address-checksum-value of chain
    :return str: address
    """

    # Work with raw bytes
    pubkey_raw = unhexlify(public_key)
    pkhv_raw = unhexlify(pkhv)
    cv_raw = unhexlify(cv)

    # Hash public key
    ripemd160 = new("ripemd160")
    ripemd160.update(sha256(pubkey_raw).digest())
    pubkey_raw_hashed = ripemd160.digest()

    # Extend
    steps = 20 // len(pkhv_raw)
    idx = 0
    privkey_ba = bytearray(pubkey_raw_hashed)
    for pkhv_byte in pkhv_raw:
        privkey_ba.insert(idx, pkhv_byte)
        idx += steps + 1
    pubkey_raw_extended = bytes(privkey_ba)

    pubkey_raw_sha256d = sha256d(pubkey_raw_extended)

    # XOR first 4 bytes with address-checksum-value for postfix
    postfix = xor_bytes(pubkey_raw_sha256d[:4], cv_raw)

    # Compose final address
    address_bin = pubkey_raw_extended + postfix
    return base58.b58encode(address_bin)


def sha256d(data):
    return sha256(sha256(data).digest()).digest()


def xor_bytes(a, b):
    result = bytearray()
    for b1, b2 in zip(a, b):
        result.append(b1 ^ b2)
    return bytes(result)


def render_json(data):
    # Convert the data to sorted, indented JSON
    response = json.dumps(data, sort_keys=True, indent=2)

    # Truncate the data. Alter as needed
    response = response[:5000]

    # Get the Pygments formatter
    formatter = HtmlFormatter(style="colorful")

    # Highlight the data
    response = highlight(response, JsonLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)
