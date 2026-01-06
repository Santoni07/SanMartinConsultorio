from django import forms
from .models import Estudio
from datetime import date

class EstudioForm(forms.ModelForm):
    class Meta:
        model = Estudio
        fields = ['tipo', 'fecha', 'descripcion', 'archivo']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select form-select-lg mb-3',
            }),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-lg mb-3',
                'placeholder': 'Seleccioná la fecha del estudio'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control form-control-lg mb-3',
                'placeholder': 'Descripción breve del estudio...',
                'rows': 3,
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-lg mb-3',
                'accept': '.pdf,.jpg,.png,.jpeg',
            }),
        }
        labels = {
            'tipo': 'Tipo de Estudio',
            'fecha': 'Fecha del Estudio',
            'descripcion': 'Descripción',
            'archivo': 'Archivo Adjunto',
        }
def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('fecha'):
            self.initial['fecha'] = date.today()
