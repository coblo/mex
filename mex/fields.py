# -*- coding: utf-8 -*-
"""Custom Django Model Fields

Credits for BinaryHashField to:
https://github.com/Racum/django-binhash (3-Clause BSD License)
"""
import re
import binascii
from django.core import validators
from django.db.models.fields import Field
from django.core.exceptions import ValidationError


HEXADECIMAL_VALUES = re.compile(r"^[0-9a-fA-F]+\Z")


class BinaryHashField(Field):
    description = "Hex-Hashes saved as raw binary data."
    empty_values = (None, "")

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = self.hex_length
        super(BinaryHashField, self).__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length))

    def get_internal_type(self):
        return "BinaryField"

    def hex_to_bytes(self, value):
        if value is None:
            return value
        elif (
            isinstance(value, str)
            and len(value) == self.hex_length
            and HEXADECIMAL_VALUES.search(str(value))
        ):
            return binascii.unhexlify(value)
        else:
            message_tpl = "Enter a valid {alg} (hexadecimal string with {size} bytes)."
            message = message_tpl.format(alg=self.algorithm, size=self.hex_length)
            raise ValidationError(message)

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super(BinaryHashField, self).get_db_prep_value(
            value, connection, prepared
        )
        if value not in self.empty_values:
            return connection.Database.Binary(self.hex_to_bytes(value))

    def from_db_value(self, value, expression, connection, context):
        if value not in self.empty_values:
            return binascii.hexlify(value).decode("ascii")

    def to_python(self, value):
        self.hex_to_bytes(value)
        return value

    def get_default(self):
        if self.has_default() and not callable(self.default):
            self.hex_to_bytes(self.default)
            return self.default
        default = super(BinaryHashField, self).get_default()
        return default

    def formfield(self, **kwargs):
        return super(BinaryHashField, self).formfield(max_length=self.max_length)


class SHA256Field(BinaryHashField):
    description = "SHA-256 hash data saved as binary"
    algorithm = "SHA-256"
    hex_length = 64
