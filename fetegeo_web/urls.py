from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse
from place.views import geo, ctry, get_location, index

urlpatterns = patterns('',
                       url(r'^api/geo/(?P<query>.+)$', geo, name='geo'),
                       url(r'^api/ctry/(?P<query>.+)$', ctry, name='ctry'),
                       url(r'^api/loc/(?P<t>.+)/(?P<query>.+)$', get_location, name='loc'),
                       )

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'xml'], suffix_required=True)

urlpatterns += patterns('place.views',
                        url(r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: ", mimetype="text/plain")),
                        url(r'$^', index, name='index'),
                        )

urlpatterns += staticfiles_urlpatterns()
