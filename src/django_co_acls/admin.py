'''
Created on Mar 25, 2011

@author: leifj
'''
from django.contrib import admin
from django_co_acls.models import AccessControlEntry

admin.site.register(AccessControlEntry)
