# -*- coding: utf-8 -*-
from django.conf import settings
from django.apps import AppConfig
from django.contrib.admin import AdminSite


class MexConfig(AppConfig):

    name = "mex"
    verbose_name = settings.MEX_BRAND

    def ready(self):
        AdminSite.site_title = settings.MEX_BRAND
        AdminSite.site_header = settings.MEX_BRAND
        AdminSite.index_title = ""
