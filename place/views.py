from geo import Queryier, Results
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import XMLRenderer, JSONRenderer
from place.forms import IndexForm
from place.models import Lang
from place.serialiser import ResultSerialiser

_DEFAULT_LANG = Lang.objects.get(iso639_1='EN').id
q = Queryier.Queryier()
    
def index(request):
    error = False
    
    if request.method == 'POST':
        form = IndexForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            lang = form.cleaned_data['langs']
            if not lang:
                lang = _DEFAULT_LANG
            if not query:
                error = True
            else:
                q_res = q.search([lang], False, False, query, None)
                names, places = _merge_results(q_res)
                if not names:
                    return _rtr(request, 'index.html', {'no_result': True, 'q': query, 'form': form})
                else:
                    return _rtr(request, 'index.html', {'places': places, 'names': names, 'form': form})
    else:
        form = IndexForm()
        
    return _rtr(request, 'index.html', {'error': error, 'form': form})

@api_view(['GET'])
@renderer_classes((JSONRenderer, XMLRenderer))
def api(request, query, format=None):
    if request.method == 'GET':
        q_res = q.search([_DEFAULT_LANG], False, False, query, None)
        if not q_res:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        names, places = _merge_results(q_res)
        res = [Results.RPlace(x, names[x.id]) for x in places]
        serialiser = ResultSerialiser(res, many=True)
        return Response(serialiser.data)

def _rtr(request, html, c):
    """
    Wrapper for render_to_response including the CSRF tag.
    """
    c.update(csrf(request))
    return render_to_response(html, c)

def _merge_results(q_res):
    """
    Method takes a list of results produced by the fetegeo search command.
    It will skip any results with exactly the same pretty-print name (as they are assumed to be identical)
    It will also try and merge LineStrings that are close enough to other LineStrings to be considered part of the same street.
    The method returns a list of places and a dict of place.id's to pretty print names.
    """
    names = dict()
    places = list()
    ls = dict()
    for r in q_res:
        place = r.ri.place
        if place.location is None:
            continue;
        if place.location.geom_type == 'LineString':
            for i, p in ls.items():
                if place.location.distance(p.location) < 0.01:  # TODO: is this number good?
                    ls[i].location = p.location.union(place.location).merged
                    break;
            else:
                ls[place.id] = place
                names[place.id] = r.ri.pp

        else:
            if r.ri.pp not in names.values():
                places.append(place)
                names[place.id] = r.ri.pp
    places.extend(place for place in ls.values())
            
    return names, places
