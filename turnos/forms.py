from django import forms
from .models import Turnos
from especialidades.models import Especialidades
from medicos.models import Medico

class SeleccionMedicoForm(forms.Form):
    especialidad = forms.ModelChoiceField(
        queryset=Especialidades.objects.all(),
        label="Especialidad",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )
    medico = forms.ModelChoiceField(
        queryset=Medico.objects.all(),
        label="Médico",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turnos
        fields = ['especialidad', 'medico', 'fecha', 'hora', 'paciente', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'especialidad': 'Especialidad',
            'medico': 'Médico',
            'fecha': 'Fecha del turno',
            'hora': 'Hora del turno',
            'paciente': 'Paciente',
            'observaciones': 'Observaciones (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases Bootstrap u otras configuraciones globales
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.DateInput, forms.TimeInput, forms.Textarea)):
                field.widget.attrs.update({'class': 'form-control'})