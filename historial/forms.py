from django import forms
from .models import ConsultaMedica

class ConsultaMedicaForm(forms.ModelForm):
    class Meta:
        model = ConsultaMedica
        fields = [
            'fecha',
            'motivo',
            'examen_fisico',  # 👈 NUEVO CAMPO
            'diagnostico',
            'tratamiento',
            'observaciones'
        ]

        widgets = {
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Seleccionar fecha'
            }),

            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo de la consulta'
            }),

            'examen_fisico': forms.Textarea(attrs={   # 👈 NUEVO WIDGET
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detalle del examen físico (signos vitales, hallazgos, etc.)'
            }),

            'diagnostico': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalle del diagnóstico'
            }),

            'tratamiento': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tratamiento indicado'
            }),

            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones adicionales'
            }),
        }