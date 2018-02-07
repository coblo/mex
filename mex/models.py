# -*- coding: utf-8 -*-
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import SET_NULL, CASCADE
from mex import fields


class Block(models.Model):

    hash = fields.HashField(max_length=32, unique=True)
    miner = models.CharField(max_length=42)
    height = models.PositiveIntegerField()
    time = models.DateTimeField()
    txcount = models.PositiveIntegerField()

    class Meta:
        get_latest_by = 'height'

    def __str__(self):
        return f'Block({self.height})'

    def natural_key(self):
        return self.hash

    @classmethod
    def get_height(cls):
        try:
            return cls.objects.latest().height
        except Block.DoesNotExist:
            return -1


class Transaction(models.Model):

    hash = fields.HashField(max_length=32, unique=True)
    block = models.ForeignKey(
        Block, on_delete=CASCADE, null=True, related_name='transactions')
    idx = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('-block', 'idx')

    def __str__(self):
        return self.hash

    def natural_key(self):
        return self.hash


class Address(models.Model):

    address = models.CharField(max_length=52, primary_key=True)

    def __str__(self):
        return self.address

    def natural_key(self):
        return self.address


class Output(models.Model):

    transaction = models.ForeignKey(
        Transaction, on_delete=CASCADE, related_name='outputs_for_tx'
    )

    out_idx = models.PositiveSmallIntegerField()

    value = models.DecimalField(max_digits=28, decimal_places=8, null=True)

    address = models.ForeignKey(
        Address, on_delete=SET_NULL, related_name='outputs_for_addr', null=True
    )

    spent = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.transaction}:{self.out_idx}'

    def natural_key(self):
        return f'{self.transaction.hash}:{self.out_idx}'


class Input(models.Model):

    transaction = models.ForeignKey(
        Transaction, on_delete=CASCADE, related_name='inputs_for_tx'
    )

    spends = models.ForeignKey(
        Output, on_delete=SET_NULL, related_name='inputs_for_output',
        null=True
    )

    coinbase = models.BooleanField()

    def __str__(self):
        return f'{self.spends}'

    def value(self):
        if self.coinbase:
            return 100
        elif self.spends:
            return self.spends.value
        else:
            return 0


class Stream(models.Model):

    name = models.CharField(max_length=32)
    createtxid = fields.HashField(max_length=32, unique=True)
    streamref = models.CharField(max_length=64)
    open = models.BooleanField()
    details = JSONField(encoder=DjangoJSONEncoder)
    creators = ArrayField(models.CharField(max_length=52, blank=True), size=8)
    subscribed = models.BooleanField()
    synchronized = models.BooleanField()
    items = models.IntegerField()
    confirmed = models.IntegerField()
    keys = models.IntegerField()
    publishers = models.IntegerField()

    def __str__(self):
        return f'{self.name}'
