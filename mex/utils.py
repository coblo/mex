# -*- coding: utf-8 -*-
import json
import textwrap
from _sha256 import sha256
from binascii import unhexlify
from hashlib import new
import base58
import bleach
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLdLexer

from mex.custom_sort import make_custom_sort


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


custom_sort = make_custom_sort(
    [
        ["title", "extra", "tophash", "meta"],
        ["schema", "mediatype", "data", "url"],
        ["@context", "@type", "@id", "name", "identifier"],
    ]
)


def render_json(data):
    data = custom_sort(data)
    if hasattr(data, "get"):
        data = data.get("json") or data.get("text")
    text = json.dumps(data, sort_keys=False, indent=2)
    formatter = HtmlFormatter(style="monokai", cssclass="metadata", wrapcode=False)
    text = highlight(text, JsonLdLexer(), formatter)
    style = "<style>" + formatter.get_style_defs() + "</style>"
    text = (style + bleach.linkify(text)).strip()
    return mark_safe(text)


def iscc_clean(i):
    """Remove leading scheme and dashes"""
    return i.split(":")[-1].strip().replace("-", "")


ISCC_SYMBOLS = "C23456789rB1ZEFGTtYiAaVvMmHUPWXKDNbcdefghLjkSnopRqsJuQwxyz"


def iscc_verify(i):
    i = iscc_clean(i)
    for c in i:
        if c not in ISCC_SYMBOLS:
            raise ValueError('Illegal character "{}" in ISCC Code'.format(c))
    for component_code in iscc_split(i):
        iscc_verify_component(component_code)


ISCC_COMPONENT_CODES = [
    "CC",
    "CT",
    "Ct",
    "CY",
    "Ci",
    "CA",
    "Ca",
    "CV",
    "Cv",
    "CM",
    "Cm",
    "CD",
    "CR",
]


def iscc_verify_component(component_code):

    if not len(component_code) == 13:
        raise ValueError(
            "Illegal component length {} for {}".format(
                len(component_code), component_code
            )
        )

    header_code = component_code[:2]
    if header_code not in ISCC_COMPONENT_CODES:
        raise ValueError("Illegal component header {}".format(header_code))


def iscc_split(i):
    return textwrap.wrap(iscc_clean(i), 13)


def is_iscc(value):
    try:
        iscc_verify(value)
        return True
    except Exception:
        return False
