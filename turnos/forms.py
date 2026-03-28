from django import forms
from .models import Turnos
from especialidades.models import Especialidades
from medicos.models import Medico
from .models import DisponibilidadMedico,ExcepcionAgenda

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
                
                
                

class AgendaMedicoForm(forms.Form):

    medico = forms.ModelChoiceField(
        queryset=Medico.objects.all(),
        label="Médico"
    )

    dias = forms.MultipleChoiceField(
        choices=DisponibilidadMedico.DIAS,
        widget=forms.CheckboxSelectMultiple,
        label="Días de atención"
    )

    hora_inicio = forms.TimeField(label="Hora inicio")
    hora_fin = forms.TimeField(label="Hora fin")

    duracion_turno = forms.IntegerField(
        label="Duración (minutos)",
        initial=20
    )


# 🔥 Generador de horarios
def generar_horas():
    horas = []
    for h in range(7, 21):  # 07:00 a 20:40
        for m in [0, 20, 40]:
            hora = f"{h:02d}:{m:02d}"
            horas.append((hora, hora))
    return horas


HORAS = generar_horas()


class ConfiguracionAgendaForm(forms.Form):

    medico = forms.ModelChoiceField(queryset=Medico.objects.all())

    fecha_desde = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_hasta = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    # DÍAS
    lunes = forms.BooleanField(required=False)
    martes = forms.BooleanField(required=False)
    miercoles = forms.BooleanField(required=False)
    jueves = forms.BooleanField(required=False)
    viernes = forms.BooleanField(required=False)

    # HORARIOS (AHORA DROPDOWN 🔥)
    lunes_inicio = forms.ChoiceField(choices=HORAS, required=False)
    lunes_fin = forms.ChoiceField(choices=HORAS, required=False)

    martes_inicio = forms.ChoiceField(choices=HORAS, required=False)
    martes_fin = forms.ChoiceField(choices=HORAS, required=False)

    miercoles_inicio = forms.ChoiceField(choices=HORAS, required=False)
    miercoles_fin = forms.ChoiceField(choices=HORAS, required=False)

    jueves_inicio = forms.ChoiceField(choices=HORAS, required=False)
    jueves_fin = forms.ChoiceField(choices=HORAS, required=False)

    viernes_inicio = forms.ChoiceField(choices=HORAS, required=False)
    viernes_fin = forms.ChoiceField(choices=HORAS, required=False)
    

class ExcepcionAgendaForm(forms.ModelForm):
    class Meta:
        model = ExcepcionAgenda
        fields = ['fecha', 'tipo', 'hora_inicio', 'hora_fin', 'nueva_fecha', 'motivo']

        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control', 'id': 'tipo'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'hora_inicio'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'hora_fin'}),
            'nueva_fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'nueva_fecha'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'id': 'motivo'}),
        }
class SeleccionMedicoConsultaForm(forms.Form):

    especialidad = forms.ModelChoiceField(
        queryset=Especialidades.objects.all(),
        required=False,
        empty_label="Todas las especialidades",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'id_especialidad'
        })
    )

    medico = forms.ModelChoiceField(
        queryset=Medico.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'id_medico'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'especialidad' in self.data:
            try:
                especialidad_id = int(self.data.get('especialidad'))

                if especialidad_id:
                    self.fields['medico'].queryset = Medico.objects.filter(
                        especialidad__id=especialidad_id  # 🔥 CORRECTO
                    ).distinct()
                else:
                    self.fields['medico'].queryset = Medico.objects.all()

            except (ValueError, TypeError):
                self.fields['medico'].queryset = Medico.objects.all()

        else:
            self.fields['medico'].queryset = Medico.objects.all()