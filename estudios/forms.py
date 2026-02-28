from django import forms
from datetime import date
from .models import Estudio
from historial.models import ConsultaMedica


class EstudioForm(forms.ModelForm):
    consulta = forms.ModelChoiceField(
        queryset=ConsultaMedica.objects.none(),
        required=False,
        label="Asociar a Consulta",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg mb-3',
        })
    )

    class Meta:
        model = Estudio
        fields = ['tipo', 'fecha', 'consulta', 'descripcion', 'archivo']

        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select form-select-lg mb-3',
            }),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-lg mb-3',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control form-control-lg mb-3',
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
            'consulta': 'Consulta Asociada',
            'descripcion': 'Descripción',
            'archivo': 'Archivo Adjunto',
        }

    def __init__(self, *args, **kwargs):
        paciente = kwargs.pop('paciente', None)
        super().__init__(*args, **kwargs)

        if not self.initial.get('fecha'):
            self.initial['fecha'] = date.today()

        # 🔥 FILTRAR CONSULTAS DEL PACIENTE
        if paciente:
            self.fields['consulta'].queryset = ConsultaMedica.objects.filter(
                historia_clinica__paciente=paciente
            ).order_by('-fecha')