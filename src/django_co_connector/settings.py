'''
Created on Apr 7, 2011

@author: leifj
'''

from django.conf import settings

CO_ATTRIBUTES = getattr(settings,'CO_ATTRIBUTES',('HTTP_AFFILIATION'))
CO_URI_ATTRIBUTE = getattr(settings,'CO_URI_ATTRIBUTES','HTTP_ENTITLEMENT')