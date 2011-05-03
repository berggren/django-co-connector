'''
Created on Apr 5, 2011

@author: leifj
'''

from django.db import models
from django.db.models.fields import CharField, DateTimeField
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class AccessControlEntry(models.Model):
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    permission = CharField(max_length=256)
    modify_time = DateTimeField(auto_now=True)
    create_time = DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s can %s on %s" % (self.group.__unicode__(),self.permission,self.content_object.__unicode__())

    class Meta:
        unique_together = (('group','permission'),('user','permission'))

def allow(object,ug,permission):
    if isinstance(ug, Group):
        return allow_group(object,ug,permission)
    elif isinstance(ug,User):
        return allow_user(object,ug,permission)
    elif isinstance(ug,str):
        if ug == 'anyone':
            ace,created = AccessControlEntry.objects.get_or_create(content_object=object,user=None,group=None)
            return ace
    else:
        raise Exception,"Don't know how to allow %s to do stuff" % repr(ug)

def deny(object,ug,permission):
    if isinstance(ug, Group):
        return deny_group(object,ug,permission)
    elif isinstance(ug,User):
        return deny_user(object,ug,permission)
    elif isinstance(ug,str):
        if ug == 'anyone':
            acl = AccessControlEntry.objects.filter(content_object=object,user=None,group=None,permission=permission)
            for ace in acl: # just in case we grew duplicates
                ace.delete()
            return None
    else:
        raise Exception,"Don't know how to allow %s to do stuff" % repr(ug)

def acl(object):
    return AccessControlEntry.objects.filter(content_object=object)

def allow_user(object,user,permission):
    ace,created = AccessControlEntry.objects.get_or_create(content_object=object,user=user,permission=permission)
    return ace

def deny_user(object,user,permission):
    acl = AccessControlEntry.objects.filter(content_object=object,user=user,permission=permission)
    for ace in acl:
        ace.delete()
    return None

def allow_group(object,group,permission):
    ace,created = AccessControlEntry.objects.get_or_create(content_object=object,group=group,permission=permission)
    return ace

def deny_group(object,group,permission):
    acl = AccessControlEntry.objects.filter(content_object=object,group=group,permission=permission)
    for ace in acl:
        ace.delete()
    return None

def is_allowed(object,user,permission):
    for ace in AccessControlEntry.objects.filter(content_object=object,permission=permission):
        if (not ace.group and not ace.user) or (ace.group in user.groups) or (user == ace.user):
            return True
            
    return False