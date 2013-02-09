from django.conf.urls import patterns
from django.contrib import admin
from place.views import index
admin.autodiscover()

urlpatterns = patterns('',
     (r'$^', index),
)
