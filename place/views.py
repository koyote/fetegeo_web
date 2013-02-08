from django.shortcuts import render_to_response
from place.models import PlaceName

def index(request):
    error = False
    if 'query' in request.GET:
        query = request.GET['query']
        
        if not query:
            error = True
        else:
            results = PlaceName.objects.filter(name__iexact=query)
            if results.count() == 0 or all(r.place.location is None for r in results):
                return render_to_response('index.html', {'no_result': True, 'q': query})
            else:
                return render_to_response('index.html', {'results': results})
    return render_to_response('index.html', {'error': error})
