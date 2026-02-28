from django import forms
from .models import Turnos
from especialidades.models import Especialidades
from medicos.models import Medico

class SeleccionMedicoForm(forms.Form):

    especialidad = forms.ModelChoiceField(
        queryset=Especialidades.objects.all(),
        required=False,
        empty_label="Todas las especialidades",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    medico = forms.ModelChoiceField(
        queryset=Medico.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si viene especialidad en el form enviado
        if 'especialidad' in self.data:
            try:
                especialidad_id = int(self.data.get('especialidad'))

                if especialidad_id:
                    self.fields['medico'].queryset = Medico.objects.filter(
                        especialidad__id=especialidad_id
                    ).distinct()
                else:
                    self.fields['medico'].queryset = Medico.objects.all()

            except (ValueError, TypeError):
                self.fields['medico'].queryset = Medico.objects.all()

        else:
            # Primera carga
            self.fields['medico'].queryset = Medico.objects.all()
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