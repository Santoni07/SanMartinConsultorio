
from django import forms
from .models import Especialidades
from django.forms.widgets import ClearableFileInput

class EspecialidadesForm(forms.ModelForm):
    
    class Meta:
        model = Especialidades
        fields = ['nombre', 'descripcion', 'img']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'img': ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
 
        
    def __init__(self, *args, **kwargs):
        super(EspecialidadesForm, self).__init__(*args, **kwargs)
        # Establecer el campo 'img' como opcional
        self.fields['img'].required = False
 