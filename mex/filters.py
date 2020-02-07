# -*- coding: utf-8 -*-
from itertools import chain
import django_filters
from mex.models import StreamItem
from mex.utils import iscc_verify, iscc_split


def is_iscc(value):
    try:
        iscc_verify(value)
        return True
    except Exception:
        return False


class CharArrayFilter(django_filters.BaseCSVFilter, django_filters.CharFilter):
    def filter(self, qs, value):
        try:
            new_value = list(
                chain.from_iterable([iscc_split(v) for v in value if is_iscc(v)])
            )
            if new_value:
                return super().filter(qs, new_value)
        except Exception:
            pass
        return super().filter(qs, value)


class StreamItemFilter(django_filters.FilterSet):

    keys = CharArrayFilter(
        label="Search stream keys ... ", distinct=True, lookup_expr="overlap"
    )

    class Meta:
        model = StreamItem
        fields = ["keys"]
