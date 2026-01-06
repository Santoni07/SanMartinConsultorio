       
from django import forms

from especialidades.models import Especialidades

from .models import Medico



class MedicosForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['nombre', 'apellido', 'matricula', 'email', 'telefono', 'img', 'especialidad']
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matricula'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefono'}),
            'img': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'especialidad': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['img'].widget = forms.ClearableFileInput(attrs={'class': 'form-control'})