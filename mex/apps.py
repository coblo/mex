# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.contrib.admin import AdminSite


# class AccessUser(object):
#     has_module_perms = has_perm = __getattr__ = lambda s, *a, **kw: True


class MexConfig(AppConfig):

    name = 'mex'
    verbose_name = "Mex Explorer"

    def ready(self):
        """
        Monkeypatch default admin with our own admin site
        see: https://stackoverflow.com/a/30056258
        """
        from django.contrib import admin
        from django.contrib.auth.models import User, Group
        AdminSite.site_title = 'Content Blockchain Explorer'
        AdminSite.site_header = 'Content Blockchain Explorer'
        AdminSite.index_title = ''

        # admin.site.has_permission = lambda r: setattr(r, 'user', AccessUser()) or True
        # admin.site.unregister(User)
        # admin.site.unregister(Group)
        # admin.site.disable_action('delete_selected')
