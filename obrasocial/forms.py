

from django import forms

from obrasocial.models import ObraSocial
class ObraSocialForm(forms.Form):
    nombre = forms.CharField(max_length=50)
    
    class Meta:
        model = ObraSocial
        fields = ['nombre']
   