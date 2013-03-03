from django.core.cache import cache
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from geo import Queryier
from place.forms import IndexForm
from place.models import Lang, get_country_name_lang, Place, Country
from place.serialiser import ResultSerialiser, SerialisableResult
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import XMLRenderer, JSONRenderer
from rest_framework.response import Response
import ast
import os
import pygeoip

_DEFAULT_LANG = Lang.objects.get(iso639_1='EN').id
q = Queryier.Queryier()
geoip = pygeoip.GeoIP(os.path.join(os.path.dirname(__file__), 'geoip/GeoLiteCity.dat').replace('\\', '/'), pygeoip.MEMORY_CACHE)
    
def index(request):
    """
    Entry point for the default index.html. Handles all form options and validation.
    """
    error = False
    user_lat_lng, ctry = _get_coor_and_country(request)
    
    if request.method == 'POST':
        form = IndexForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            lang = form.cleaned_data['langs']
            dangling = form.cleaned_data['dangling']
            find_all = form.cleaned_data['find_all']
            
            if not lang:
                lang = _DEFAULT_LANG
                
            if not query:
                error = True
            else:
                q_res = q.search([lang], find_all, dangling, query, ctry)
                place_names, postcode_names, places = _merge_results(q_res)
                if (not place_names and not postcode_names) or not places:
                    return _rtr(request, 'index.html', {'no_result': True, 'q': query, 'form': form, 'user_lat_lng': user_lat_lng})
                else:
                    return _rtr(request, 'index.html', {'place_names': place_names, 'postcode_names': postcode_names, 'form': form, 'user_lat_lng': user_lat_lng})
    else:
        form = IndexForm()
        
    return _rtr(request, 'index.html', {'error': error, 'form': form, 'user_lat_lng': user_lat_lng})


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
    _, ctry = _get_coor_and_country(request)
    
    if not langs:
        langs = [_DEFAULT_LANG]

    q_res = q.search(langs, find_all, dangling, query, ctry)
        
    if not q_res:
        return Response(dict(error="True", query=query))
        
    place_names, postcode_names, places = _merge_results(q_res)
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
    location = cache.get(query + t)
       
    if not location:
        return Response(dict(error="True", query=query))
    
    try:
        lat = location.x
        lng = location.y
    except AttributeError:
        lat = []
        lng = []
        for polys in location.coords:
                for x, y in polys:
                    lat.append(x)
                    lng.append(y)
                    
    return Response(dict(type=location.geom_type, x=lat, y=lng, centroidX=location.centroid.x, centroidY=location.centroid.y))
        


def _find_langs(lang_str):
    """
    Return Lang objects from a list of langs.
    """
    langs = []
    for iso in ast.literal_eval(lang_str):
        try:
            langs.append(Lang.objects.filter(iso639_1__iexact=iso)[0].id)
        except:
            continue
    return langs


def _rtr(request, html, c):
    """
    Wrapper for render_to_response including the CSRF tag.
    """
    c.update(csrf(request))
    return render_to_response(html, c)


def _merge_results(q_res, admin_levels=[]):
    """
    Method takes a list of results produced by the fetegeo search command.
    It will skip any results with exactly the same pretty-print name (as they are assumed to be identical)
    It will also try and merge LineStrings that are close enough to other LineStrings to be considered part of the same street.
    The method returns a list of places and a dict of place.id's to pretty print place_names.
    """
    place_names = dict()
    postcode_names = dict()
    places = list()
    ls = dict()
    for r in q_res:
        place = r.ri.place
        pp = r.print_pp(admin_levels)
        if place.location is None:
            continue;
        if place.location.geom_type in ('LineString', 'MultiLineString'):
            for i, p in ls.items():
                if place.location.distance(p.location) < 0.01:  # TODO: is this number good?
                    ls[i].location = p.location.union(place.location).merged
                    break;
            else:
                ls[place.id] = place
                if isinstance(place, Place):
                    place_names[place.id] = pp
                else:
                    postcode_names[place.id] = pp

        else:
            if pp not in place_names.values():
                places.append(place)
                if isinstance(place, Place):
                    place_names[place.id] = pp
                else:
                    postcode_names[place.id] = pp

    places.extend(place for place in ls.values())
    
    # Cache locations in order to retrieve them easily onclick.
    for p in places:
        key = str(p.id) + p.__class__.__name__
        cache.set(key, p.location, 9999)    
            
    return place_names, postcode_names, places


def _get_client_ip(request):
    """
    Return the client's ip address.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _get_coor_and_country(request):
    """
    Return a client's coordinates and country.
    """
    ip = _get_client_ip(request)
    geodata = geoip.record_by_addr(ip)
    if geodata:
        user_lat_lng = [geodata['latitude'], geodata['longitude']]
        try:
            country = Country.objects.get(iso3166_2=geodata['country_code'])
        except:
            country = None
    else:
        user_lat_lng = [49.5981299, 6.1308834]  # lets default to luxembourg because we can!
        country = None
    return user_lat_lng, country
