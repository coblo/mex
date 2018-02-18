# -*- coding: utf-8 -*-
"""
Copy to config.py and adjust to your local environment.
You may overide any of the settings configured in settings/__init__.py
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mex',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


MEX_BRAND = 'MEX Explorer'
NODE_IP = '127.0.0.1'
NODE_PORT = '8374'
NODE_USER = 'testuser'
NODE_PWD = 'testpassword'
