from django.shortcuts import render_to_response
from place.models import PlaceName
from django.template.loader import render_to_string


TITLE = 'Fetegeo Mapping'


def index(request):
    error = False
    if 'query' in request.GET:
        query = request.GET['query']
        
        if not query:
            error = True
        else:
            waypoints = PlaceName.objects.filter(name__iexact=query)
            return render_to_response('index.html', {'waypoints': waypoints, 'content': render_to_string('waypoints.html', {'waypoints': waypoints}), })
    return render_to_response('index.html', {'error': error})
