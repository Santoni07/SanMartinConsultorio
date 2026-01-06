

from django import forms

from .models import Servicios

class ServiciosForm(forms.ModelForm):
    class Meta:
        model = Servicios
        fields = ['nombre', 'descripcion',  'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'imagen':forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }


