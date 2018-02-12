# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from mcrpc import RpcClient

log = logging.getLogger(__name__)


def get_client():
    return RpcClient(
        settings.NODE_IP,
        settings.NODE_PORT,
        settings.NODE_USER,
        settings.NODE_PWD
    )

