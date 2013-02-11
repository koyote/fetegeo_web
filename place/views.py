from django.shortcuts import render_to_response
from Geo import Queryier, Free_Text
from place.models import PlaceName

_DEFAULT_LANGS = ['EN']

def index(request):
    error = False
      
    if 'query' in request.GET:
        query = request.GET['query']
        
        q = Queryier.Queryier()
        ft = Free_Text.Free_Text()
        
        if not query:
            error = True
        else:
            ft_res = ft.name_to_lat_long(q, _DEFAULT_LANGS, False, False, query, None)
            results = [ r.ri.place for r in ft_res ]
            names = {r.ri.place.id: r.ri.pp for r in ft_res}
            if not results:
                return render_to_response('index.html', {'no_result': True, 'q': query})
            else:
                return render_to_response('index.html', {'results': results, 'names': names})
    return render_to_response('index.html', {'error': error})
