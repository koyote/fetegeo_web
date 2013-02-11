from Geo import Queryier
from django import forms
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from place.models import Lang

_DEFAULT_LANG = Lang.objects.get(iso639_1='EN').id
q = Queryier.Queryier()


class IndexForm(forms.Form):
    langs = forms.ChoiceField(choices=[('', "Choose Language")] + [(x.id, x.name) for x in Lang.objects.all()], required=False)
    query = forms.CharField()
    
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
                results = [r.ri.place for r in q_res]
                names = {r.ri.place.id: r.ri.pp for r in q_res}
                if not results:
                    return rtr(request, 'index.html', {'no_result': True, 'q': query, 'form': form})
                else:
                    return rtr(request, 'index.html', {'results': results, 'names': names, 'form': form})
    else:
        form = IndexForm()
        
    return rtr(request, 'index.html', {'error': error, 'form': form})

def rtr(request, html, c):
    c.update(csrf(request))
    return render_to_response(html, c)
