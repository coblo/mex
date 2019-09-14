# -*- coding: utf-8 -*-
from django.db import models
import binascii


class HashField(models.BinaryField):
    description = "Hex-Hashes saved as raw binary data."

    def __init__(self, *args, **kwargs):
        super(HashField, self).__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection, context):
        if value:
            return binascii.hexlify(value).decode("ascii")

    def get_prep_value(self, value):
        if value:
            return binascii.unhexlify(value)
