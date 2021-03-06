"""
 Copyright (C) 2013 Pit Apps

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to
 deal in the Software without restriction, including without limitation the
 rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 sell copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 IN THE SOFTWARE.
"""

import ast
import os

from django.core.cache import cache
from django.core.context_processors import csrf
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import XMLRenderer, JSONRenderer
from rest_framework.response import Response
import pygeoip

from geo import Queryier
from place.forms import IndexForm
from place.models import Lang, get_country_name_lang, Country
from place.serialiser import ResultSerialiser, SerialisableResult


_DEFAULT_LANG = Lang.objects.get(iso639_1='EN').id
q = Queryier.Queryier()
geoip = pygeoip.GeoIP(os.path.join(os.path.dirname(__file__), 'geoip/GeoLiteCity.dat').replace('\\', '/'), pygeoip.MEMORY_CACHE)


def index(request):
    """
    Entry point for the default index.html. Handles all form options and validation.
    """
    error = False
    user_lon_lat, ctry = _get_coor_and_country(request)
    renderHtmls = {'default': 'index.html', 'ajax': 'results.html'}

    if request.method == 'POST':
        form = IndexForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            lang = form.cleaned_data['langs']
            dangling = form.cleaned_data['dangling']
            find_all = form.cleaned_data['find_all']
            start = form.cleaned_data['start']
            limit = ast.literal_eval(form.cleaned_data['limit'])

            if not lang:
                lang = _DEFAULT_LANG

            if not query:
                error = True
            else:
                result = q.search([lang], find_all, dangling, query, ctry, start=start, limit=limit)
                if not result:
                    return _rtr(request, renderHtmls, {'no_result': True, 'q': query, 'user_lon_lat': user_lon_lat})
                else:
                    place_names, postcode_names, places, total_results = result
                    return _rtr(request, renderHtmls,
                                {'form': form, 'place_names': place_names, 'postcode_names': postcode_names, 'places': places, 'total': total_results,
                                 'limit': limit, 'user_lon_lat': user_lon_lat})
    else:
        form = IndexForm()

    return _rtr(request, renderHtmls, {'error': error, 'form': form, 'user_lon_lat': user_lon_lat})


@api_view(['POST'])
@renderer_classes((JSONRenderer, XMLRenderer))
def geo(request, query, format=None):
    """
    Method dealing with the API requests to geo. Uses the same method for fetching results as index.
    """
    dangling = ast.literal_eval(request.DATA['dangling'])  # Convert String to Boolean
    find_all = ast.literal_eval(request.DATA['find_all'])
    show_all = ast.literal_eval(request.DATA['show_all'])
    lang_str = request.DATA['langs']
    langs = _find_langs(lang_str)

    try:
        ctry = Country.objects.get(iso3166_2=request.DATA['country'])
    except ObjectDoesNotExist:
        _, ctry = _get_coor_and_country(request)

    if not langs:
        langs = [_DEFAULT_LANG]

    result = q.search(langs, find_all, dangling, query, ctry)
    if not result or not result[0]:
        return Response(dict(error="True", query=query))

    place_names, postcode_names, places, _ = result
    place_names.update(postcode_names)
    res = [SerialisableResult(x, place_names[x.id]) for x in places]
    serialiser = ResultSerialiser(res, many=True, context={'show_all': show_all})
    return Response(serialiser.data)


@api_view(['POST'])
@renderer_classes((JSONRenderer, XMLRenderer))
def ctry(request, query, format=None):
    """
    Method dealing with the API requests to country.
    """

    lang_str = request.DATA['langs']
    langs = _find_langs(lang_str)

    if not langs:
        langs = [_DEFAULT_LANG]

    country, lang = get_country_name_lang(query, langs)
    if lang:
        lang = lang.name

    if not country:
        return Response(dict(error="True", query=query))

    return Response(dict(result=country, query=query, lang=lang))


@api_view(['GET'])
@renderer_classes((JSONRenderer, XMLRenderer))
def get_location(request, t, query, format=None):
    """
    Method dealing with the API requests asking for the location of a place's id.
    This only retrieves locations that are stored in the cache.
    """
    loc_geojson = cache.get(query + t)

    if not loc_geojson:
        return Response(dict(error="True", query=query))

    return Response(dict(geometry=loc_geojson))


def _find_langs(lang_str):
    """
    Return Lang objects from a list of langs.
    """
    langs = []
    for iso in ast.literal_eval(lang_str):
        try:
            langs.append(Lang.objects.filter(iso639_1__iexact=iso)[0].id)
        except ObjectDoesNotExist:
            continue
    return langs


def _rtr(request, html, c):
    """
    Wrapper for render_to_response including the CSRF tag.
    Also renders a different page if the request was send through ajax.
    """
    c.update(csrf(request))
    if request.is_ajax():
        return render(request, html['ajax'], c)
    return render(request, html['default'], c)


def _get_client_ip(request):
    """
    Return the client's ip address.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def _get_coor_and_country(request):
    """
    Return a client's coordinates and country.
    """
    ip = _get_client_ip(request)
    geodata = geoip.record_by_addr(ip)
    if geodata:
        user_lon_lat = [geodata['longitude'], geodata['latitude']]
        try:
            country = Country.objects.get(iso3166_2=geodata['country_code'])
        except ObjectDoesNotExist:
            country = None
    else:
        user_lon_lat = [6.1308834, 49.5981299]  # lets default to Luxembourg because we can!
        country = None
    return user_lon_lat, country
