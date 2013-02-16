from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('place.views',
     url(r'^api/geo/(?P<query>.+)$', 'geo'),
     url(r'^api/ctry/(?P<query>.+)$', 'ctry'),
)

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'xml'], suffix_required=True)

urlpatterns += patterns('place.views',
     (r'$^', 'index'),
)
