'''
Created on Apr 5, 2011

@author: leifj
'''

from django.db import models
from django.db.models.fields import CharField, DateTimeField
from django.contrib.auth.models import Group, User
from django.db.models.fields.related import  ForeignKey

class AccessControlEntry(models.Model):
    group = ForeignKey(Group,related_name='+',blank=True,null=True)
    user = ForeignKey(User,related_name='+',blank=True,null=True)
    permission = CharField(max_length=256)
    modify_time = DateTimeField(auto_now=True)
    create_time = DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s can %s" % (self.group.__unicode__(),self.permission)

    class Meta:
        unique_together = (('group','permission'),('user','permission'))

def allow(object,ug,permission):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    
    if isinstance(ug, Group):
        return allow_group(object,ug,permission)
    elif isinstance(ug,User):
        return allow_user(object,ug,permission)
    elif isinstance(ug,str):
        if ug == 'anyone':
            ace = object.acl.filter(group=None,permission=permission)
            if not ace:
                ace = AccessControlEntry.objects.create(group=None,user=None,permission=permission)
                object.acl.append(ace)
    else:
        raise Exception,"Don't know how to allow %s to do stuff" % repr(ug)

def deny(object,ug,permission):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    
    if isinstance(ug, Group):
        return deny_group(object,ug,permission)
    elif isinstance(ug,User):
        return deny_user(object,ug,permission)
    elif isinstance(ug,str):
        if ug == 'anyone':
            ace = object.acl.filter(user=None,group=None,permission=permission)
            if ace:
                object.acl.remove(ace)
    else:
        raise Exception,"Don't know how to allow %s to do stuff" % repr(ug)

def acl(object):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    
    acl = object.acl
    if not acl:
        acl = []
    return acl

def allow_user(object,user,permission):
    ace = object.acl.filter(user=user,permission=permission)
    if not ace:
        ace = AccessControlEntry.objects.create(user=user,permission=permission)
        object.acl.append(ace)

def deny_user(object,user,permission):
    ace = object.acl.filter(user=user,permission=permission)
    if ace:
        object.acl.remove(ace)

def allow_group(object,group,permission):
    ace = object.acl.filter(group=group,permission=permission)
    if not ace:
        ace = AccessControlEntry.objects.create(group=group,permission=permission)
        object.acl.append(ace)

def deny_group(object,group,permission):
    ace = object.acl.filter(group=group,permission=permission)
    if ace:
        object.acl.remove(ace)

def is_allowed(object,user,permission):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    # XXX use more sql here
    for ace in object.acl.filter(permission=permission):
        if not ace.group or ace.group in user.groups or user == ace.user:
            return True
            
    return False