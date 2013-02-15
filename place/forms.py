from django import forms
from place.models import Lang

class IndexForm(forms.Form):
    langs = forms.ChoiceField(choices=[('', "Choose Language")] + [(x.id, x.name) for x in Lang.objects.all().order_by('name')], required=False)
    query = forms.CharField()