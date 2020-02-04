# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Sum, Q


class AddressQuerySet(models.QuerySet):
    def with_balance(self):
        return self.annotate(
            balance=Sum(
                "outputs_for_addr__value", filter=Q(outputs_for_addr__spent=False)
            )
        )
