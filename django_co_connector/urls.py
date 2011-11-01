"""URLs for django_co_connector application."""

from django.conf.urls.defaults import *


urlpatterns = patterns('django_co_connector.views',
    url(r'^$', view='index', name='django_co_connector_index'),
)
