from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse

urlpatterns = patterns('place.views',
     url(r'^api/geo/(?P<query>.+)$', 'geo'),
     url(r'^api/ctry/(?P<query>.+)$', 'ctry'),
     url(r'^api/loc/(?P<query>.+)$', 'get_location'),
)

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'xml'], suffix_required=True)

urlpatterns += patterns('place.views',
     (r'$^', 'index'),
     (r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: ", mimetype="text/plain")),
)

urlpatterns += staticfiles_urlpatterns()
