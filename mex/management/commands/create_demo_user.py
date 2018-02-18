# -*- coding: utf-8 -*-
from django.core.management import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        username, email = settings.ADMINS[0]
        password = User.objects.make_random_password()
        if User.objects.count() == 0:
            print("  Creating demo account user: '%s', password '%s'" % (username, password))
            User.objects.create_superuser(username, email, password)
        else:
            print("  Admin demo account can only be initialized if no Accounts exist")
