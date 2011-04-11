'''
Created on Apr 7, 2011

@author: leifj
'''

from django.conf import settings

CO_ATTRIBUTES = getattr(settings,'CO_ATTRIBUTES',('HTTP_AFFILIATION','HTTP_ENTITLEMENT'))