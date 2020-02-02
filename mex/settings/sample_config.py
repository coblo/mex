# -*- coding: utf-8 -*-
"""
Copy to config.py and adjust to your local environment.
You may overide any of the settings configured in settings/__init__.py
"""

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mex",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}


MEX_BRAND = "COBLO Explorer"
MEX_FEATURED_STREAM = "iscc"
MEX_ADMIN = "Guardian"
MEX_MINER = "Validator"
MEX_ASSET = "Token"
MEX_SYMBOL = "CBL"
MEX_CURRENCY = "CoBlo"
MEX_FOOTER = "Copyright 2017-2020 <a style='color:white;' href='https://content-blockchain.org'>The Content Blockchain Project</a>"
MEX_IGNORE_STREAMS = ["root"]
MEX_SYNC_HORIZON = 300

NODE_IP = "127.0.0.1"
NODE_PORT = "8374"
NODE_USER = "testuser"
NODE_PWD = "testpassword"
