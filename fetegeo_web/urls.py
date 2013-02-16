from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('place.views',
     url(r'^api/(?P<query>.+)$', 'api'),
)

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'xml'], suffix_required=True)

urlpatterns += patterns('place.views',
     (r'$^', 'index'),
)
