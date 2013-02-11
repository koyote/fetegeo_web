from django.shortcuts import render_to_response
from Geo import Queryier

_DEFAULT_LANGS = ['EN']
q = Queryier.Queryier()

def index(request):
    error = False
      
    if 'query' in request.GET:
        query = request.GET['query'] 
        
        if not query:
            error = True
        else:
            q_res = q.search(_DEFAULT_LANGS, False, False, query, None)
            results = [ r.ri.place for r in q_res ]
            names = {r.ri.place.id: r.ri.pp for r in q_res}
            if not results:
                return render_to_response('index.html', {'no_result': True, 'q': query})
            else:
                return render_to_response('index.html', {'results': results, 'names': names})
    return render_to_response('index.html', {'error': error})
