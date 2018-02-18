# -*- coding: utf-8 -*-
import os
import shutil
import sys
from fabric.api import task, local
sys.path.append(os.path.dirname(__file__))
from mex.settings import BASE_DIR


DIR_MIGRATIONS = os.path.join(BASE_DIR, 'migrations')


@task
def reset():
    """Reset local development development environment"""

    if os.path.exists(DIR_MIGRATIONS):
        print('Delete existing migrations at: %s' % DIR_MIGRATIONS)
        shutil.rmtree(DIR_MIGRATIONS)

    print('Reset database')
    local('python manage.py reset_db --noinput')
    local('python manage.py makemigrations mex')
    local('python manage.py migrate --noinput --run-syncdb')
    local('python manage.py create_demo_user')
