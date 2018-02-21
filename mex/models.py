# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import SET_NULL, CASCADE
from django.urls import reverse

from mex import fields
from mex.querysets import AddressQuerySet


class Block(models.Model):

    height = models.PositiveIntegerField(primary_key=True)
    hash = fields.HashField(max_length=32, unique=True)
    merkleroot = fields.HashField(max_length=32)
    miner = models.ForeignKey('mex.Address', on_delete=SET_NULL, null=True)
    time = models.DateTimeField()
    txcount = models.PositiveSmallIntegerField()
    size = models.PositiveIntegerField()

    class Meta:
        get_latest_by = 'height'

    def __str__(self):
        return 'Block(%s)' % self.height

    def natural_key(self):
        return self.hash

    def get_absolute_url(self):
        return reverse('block-detail', args=[str(self.hash)])

    @classmethod
    def get_db_height(cls):
        try:
            return cls.objects.latest().height
        except Block.DoesNotExist:
            return -1


class Transaction(models.Model):

    hash = fields.HashField(max_length=32, unique=True)
    block = models.ForeignKey(
        Block, on_delete=CASCADE, null=True, related_name='transactions')
    idx = models.PositiveSmallIntegerField(null=True)

    class Meta:
        ordering = ('-block', 'idx')

    def __str__(self):
        return self.hash

    def natural_key(self):
        return self.hash

    def get_absolute_url(self):
        return reverse('transaction-detail', args=[str(self.hash)])


class Address(models.Model):

    address = models.CharField(max_length=52, primary_key=True)
    objects = AddressQuerySet.as_manager()

    def __str__(self):
        return self.address

    def natural_key(self):
        return self.address

    def get_absolute_url(self):
        return reverse('address-detail', args=[str(self.address)])


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
        return '%s:%s' % (self.transaction, self.out_idx)

    def natural_key(self):
        return '%s:%s' % (self.transaction.hash, self.out_idx)


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
        return '%s' % self.spends

    def value(self):
        if self.coinbase:
            return 100
        elif self.spends:
            return self.spends.value
        else:
            return 0
