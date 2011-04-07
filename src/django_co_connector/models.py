'''
Created on Apr 5, 2011

@author: leifj
'''

from django.db import models
from django.db.models.fields import CharField, URLField, DateTimeField, IntegerField
from django.contrib.auth.models import Group
from django.db.models.fields.related import OneToOneRel
from django.dispatch.dispatcher import Signal
from django_co_connector.settings import CO_ATTRIBUTES, CO_URI_ATTRIBUTE

class AccessControlEntry(models.Model):
    group = OneToOneRel(Group,related_name='acl',blank=True,null=True)
    permission = CharField(max_length=256)
    modify_time = DateTimeField(auto_now=True)
    create_time = DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s can %s" % (self.group.__unicode__(),self.permission)

    class Meta:
        unique_together = ('group','permission')

def allow(object,group,permission):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    
    if group == 'anyone':
        ace = object.acl.filter(group=None,permission=permission)
        if not ace:
            ace = AccessControlEntry.objects.create(group=None,permission=permission)
            object.acl.append(ace)
    else:
        ace = object.acl.filter(group=group,permission=permission)
        if not ace:
            ace = AccessControlEntry.objects.create(group=group,permission=permission)
            object.acl.append(ace)

def deny(object,group,permission):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    
    if group == 'anyone':
        ace = object.acl.filter(group=None,permission=permission)
        if ace:
            object.acl.remove(ace)
    else:
        ace = object.acl.filter(group=group,permission=permission)
        if ace:
            object.acl.remove(ace)

def can(object,user,permission):
    if not hasattr(object,'acl'):
        raise Exception,"no acl property"
    # XXX use more sql here
    for ace in object.acl.filter(permission=permission):
        if not ace.group or ace.group in user.groups:
            return True
            
    return False

class GroupConnector(models.Model):
    group = OneToOneRel(Group,related_name='connector')
    modify_time = DateTimeField(auto_now=True)
    create_time = DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True

class AttributeGroupConnector(GroupConnector):
    attribute = CharField(max_length=1024)
    value = CharField(max_length=1024)
    
    def __unicode__(self):
        return "%s=%s for %s" % (self.attribute,self.value,self.group.name)
    
    class Meta:
        unique_together = ('attribute','value')

class URIGroupConnector(GroupConnector):
    url = URLField(unique=True)
    activity_url = URLField(blank=True)
    membership_url = URLField(blank=True)
    ttl = IntegerField(blank=True)
    
    def __unicode__(self):
        return "%s for %s" % (self.uri,self.group.name)
    
    def fetch_updates(self):
        return ([],[])
    
    def fetch_all(self):
        return []
    
    def fetch_meta(self):
        return {}
    
    def update(self):
        # pull JSON to get display and ttl (?)
        (added,removed) = self.fetch_updates()
        for user in added:
            if not self.group in user.groups:
                add_member.send(sender=self.group,user=user)
                user.groups.append(self.group)
        for user in removed:
            if self.group in user.groups:     
                remove_member.send(sender=self.group,user=user)
                user.groups.remove(self.group)
    
add_member = Signal(providing_args=['user'])
remove_member = Signal(providing_args=['user'])

def co_import_from_request(request):
    epes = request.META.get(CO_URI_ATTRIBUTE)
    for uri in epes.split(';'):
        if uri.startswith("http"):
            co_import_uri(uri,members=[request.user])
        
    for attribute in request.META.get(CO_ATTRIBUTES):
        values = request.META.get(attribute)
        for value in values.split(';'):
            co_import_av(attribute,value,members=[request.user])

def co_import_av(attribute,value,members=None):
    aco = AttributeGroupConnector.objects.get(attribute=attribute,value=value)
    if not aco:
        group = Group.objects.create(name=value)
        aco = AttributeGroupConnector.objects.create(attribute=attribute,value=value,group=group)
    
    for user in members:
        if not aco.group in user.groups:
            add_member.send(sender=aco.group,user=user)
            user.groups.apppend(aco.group)
            user.save()
    
    return aco

def co_import_uri(uri,members=None):
    gco = URIGroupConnector.objects.get(uri=uri)
    if not gco:
        group = Group.objects.create(name=uri)
        gco = URIGroupConnector.objects.create(uri=uri,ttl=0,group=group)
    
    obj = gco.fetch_meta()
    changed = False
    if obj.has_key('name'):
        gco.group.name = obj['name']
        changed = True
    if obj.has_key('ttl'):
        gco.ttl = obj['ttl']
        changed = True
    if obj.has_key('member-feed'):
        gco.member_feed = obj['member-feed']
        changed = True
    
    if not members:
        members = gco.fetch_all()
    
    for user in members:
        if not gco.group in user.groups:
            add_member.send(sender=gco.group,user=user)
            user.groups.apppend(gco.group)
            user.save()
    
    if changed:
        gco.save()
        gco.group.save()
    
    return gco