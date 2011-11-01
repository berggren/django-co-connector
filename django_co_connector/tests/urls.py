from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^example/', include('django_co_connector.urls')),
)
