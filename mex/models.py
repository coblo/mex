# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import SET_NULL, CASCADE
from django.urls import reverse
from django.contrib.postgres import fields as pg_models
from mex.fields import SHA256Field
from mex.querysets import AddressQuerySet


class Block(models.Model):

    height = models.PositiveIntegerField(primary_key=True)
    hash = SHA256Field(unique=True)
    merkleroot = SHA256Field()
    miner = models.ForeignKey("mex.Address", on_delete=SET_NULL, null=True)
    time = models.DateTimeField()
    txcount = models.PositiveSmallIntegerField()
    size = models.PositiveIntegerField()

    class Meta:
        get_latest_by = "height"

    def __str__(self):
        return "Block(%s)" % self.height

    def natural_key(self):
        return self.hash

    def get_absolute_url(self):
        return reverse("block-detail", args=[str(self.hash)])

    @classmethod
    def get_db_height(cls):
        try:
            return cls.objects.latest().height
        except Block.DoesNotExist:
            return -1


class Transaction(models.Model):

    hash = SHA256Field(primary_key=True)
    block = models.ForeignKey(
        Block, on_delete=CASCADE, null=True, related_name="transactions"
    )
    idx = models.PositiveSmallIntegerField(null=True)

    class Meta:
        ordering = ("-block", "idx")

    def __str__(self):
        return self.hash

    def natural_key(self):
        return self.hash

    def get_absolute_url(self):
        return reverse("transaction-detail", args=[str(self.hash)])


class Address(models.Model):

    address = models.CharField(max_length=52, primary_key=True)
    objects = AddressQuerySet.as_manager()

    def __str__(self):
        return self.address

    def natural_key(self):
        return self.address

    def get_absolute_url(self):
        return reverse("address-detail", args=[str(self.address)])


class Stream(models.Model):

    confirmed = models.IntegerField(editable=False)
    createtxid = models.ForeignKey("mex.Transaction", on_delete=CASCADE, null=True, editable=False)
    creators = models.ManyToManyField("mex.Address", editable=False)
    details = pg_models.JSONField(editable=False)
    indexes = pg_models.JSONField(editable=False)
    items = models.IntegerField(editable=False)
    keys = models.IntegerField(editable=False)
    name = models.CharField(max_length=52, primary_key=True, editable=False)
    publishers = models.IntegerField(editable=False)
    restrict = pg_models.JSONField(editable=False)
    retrieve = models.NullBooleanField(editable=False)
    salted = models.NullBooleanField(editable=False)
    streamref = models.CharField(max_length=255, editable=False)
    subscribed = models.BooleanField(editable=False)
    synchronized = models.BooleanField(editable=False)
    monitor = models.BooleanField(
        default=False,
        help_text='Import stream items to mex database.'
    )
    show = models.BooleanField(
        default=True,
        help_text='Show steam in frontend.'
    )
    custom_description = models.CharField(
        default='',
        max_length=256,
        blank=True,
        help_text='Custom stream description for frontend.'
    )

    class Meta:
        ordering = ('name', )

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name

    def get_absolute_url(self):
        return reverse("stream-detail", args=[str(self.name)])

    @property
    def description(self):
        return self.custom_description or self.details.get("info")


class StreamItem(models.Model):

    output = models.OneToOneField(
        "mex.Output",
        on_delete=CASCADE,
        help_text="The transaction output that created this stream item.",
        primary_key=True,
        editable=False,
    )
    stream = models.ForeignKey("mex.Stream", on_delete=CASCADE, editable=False)
    available = models.BooleanField(editable=False)
    data = pg_models.JSONField()
    keys = pg_models.ArrayField(models.CharField(max_length=256), editable=False)
    offchain = models.BooleanField(editable=False)
    publishers = models.ManyToManyField("mex.Address", editable=False)
    time = models.DateTimeField(editable=False)
    valid = models.BooleanField(editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['-time'])
        ]

    def __str__(self):
        return "/".join(self.keys)

    def natural_key(self):
        return self.output.natural_key()

    def get_absolute_url(self):
        return reverse("stream-item-detail", args=[self.natural_key()])


class Output(models.Model):

    transaction = models.ForeignKey(
        Transaction, on_delete=CASCADE, related_name="outputs_for_tx"
    )

    out_idx = models.PositiveSmallIntegerField()

    value = models.DecimalField(max_digits=28, decimal_places=8, null=True)

    address = models.ForeignKey(
        Address, on_delete=SET_NULL, related_name="outputs_for_addr", null=True
    )

    spent = models.BooleanField(default=False)

    def __str__(self):
        return "%s:%s" % (self.transaction, self.out_idx)

    def natural_key(self):
        return "%s:%s" % (self.transaction.hash, self.out_idx)

    def spent_by_txid(self):
        if self.spent:
            return self.inputs_for_output.first().transaction.hash


class Input(models.Model):

    transaction = models.ForeignKey(
        Transaction, on_delete=CASCADE, related_name="inputs_for_tx"
    )

    spends = models.ForeignKey(
        Output, on_delete=SET_NULL, related_name="inputs_for_output", null=True
    )

    coinbase = models.BooleanField()

    def __str__(self):
        return "%s" % self.spends

    def value(self):
        if self.coinbase:
            return 100
        elif self.spends:
            return self.spends.value
        else:
            return 0
