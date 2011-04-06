'''
Created on Apr 5, 2011

@author: leifj
'''

from django.db import models
from django.db.models.fields import CharField, URLField, DateTimeField, IntegerField
from django.contrib.auth.models import Group
from django.db.models.fields.related import OneToOneRel
from django.dispatch.dispatcher import Signal

class AccessControlEntry(models.Model):
    group = OneToOneRel(Group,related_name='acl')
    permission = CharField(max_length=256)
    modify_time = DateTimeField(auto_now=True)
    create_time = DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s can %s" % (self.group.__unicode__(),self.permission)

def has_permission(object,user,permission):
    if hasattr(object,'acl'):
        if hasattr(object.acl,'__call__'):
            acl = object.acl()
        else:
            acl = object.acl
            
        for ace in acl:
            if ace.permission == permission and ace.group in user.groups:
                return True
            
    return False

class GroupConnector(models.Model):
    ttl = IntegerField(blank=True)
    uri = URLField(unique=True)
    member_feed = URLField(blank=True)
    group = OneToOneRel(Group,related_name='connector')
    modify_time = DateTimeField(auto_now=True)
    create_time = DateTimeField(auto_now_add=True)
    
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
    
    def contains(self,user):
        return user in self.members
    
add_member = Signal(providing_args=['user'])
remove_member = Signal(providing_args=['user'])

def co_import_from_request(request):
    epes = request.META.get('HTTP_ENTITLEMENT')
    for uri in epes.split(';'):
        co_import(uri,members=[request.user])
    ## import urn:x-avp:attribute:value URIs aswell

def co_import(uri,members=None):
    gco = GroupConnector.objects.get(uri=uri)
    if not gco:
        group = Group.objects.create(name=uri)
        gco = GroupConnector.objects.create(uri=uri,ttl=0,group=group)
    
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
            add_member.send(sender=gco,user=user)
            user.groups.apppend(gco.group)
            user.save()
    
    if changed:
        gco.save()
        gco.group.save()
    
    return gco