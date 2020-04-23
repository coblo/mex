"""
Dictionary custom sorting. Source: https://github.com/laowantong/customsort
"""
import unicodedata
from collections import OrderedDict


def to_ascii(s):
    return unicodedata.normalize("NFD", s.lower()).encode("ASCII", "ignore")


def make_custom_sort(orders):

    orders = [{k: -i for (i, k) in enumerate(reversed(order), 1)} for order in orders]

    def process(stuff):
        if isinstance(stuff, dict):
            l = [(k, process(v)) for (k, v) in stuff.items()]
            keys = set(stuff)
            order = max(orders, key=lambda order: len(keys.intersection(order)))
            order.update(
                {
                    key: i
                    for (i, key) in enumerate(
                        sorted(keys.difference(order), key=to_ascii), 1
                    )
                }
            )
            return OrderedDict(sorted(l, key=lambda x: order[x[0]]))
        if isinstance(stuff, list):
            return [process(x) for x in stuff]
        return stuff

    return process
