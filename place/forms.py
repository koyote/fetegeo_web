from django import forms
from place.models import Lang

class IndexForm(forms.Form):
    query = forms.CharField()
    langs = forms.ChoiceField(choices=[('', "Choose Language")] + [(x.id, x.name) for x in Lang.objects.all().order_by('name')], required=False, label='Language')
    dangling = forms.BooleanField(required=False, label='Allow Dangling')
    find_all = forms.BooleanField(required=False, label='Search outside of home country', initial=True)