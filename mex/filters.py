# -*- coding: utf-8 -*-
import django_filters
from mex.models import StreamItem


class CharArrayFilter(django_filters.BaseCSVFilter, django_filters.CharFilter):
    pass


class StreamItemFilter(django_filters.FilterSet):

    keys = CharArrayFilter(
        label="Search stream keys ... ", distinct=True, lookup_expr="overlap"
    )

    class Meta:
        model = StreamItem
        fields = ["keys"]
