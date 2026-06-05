from django import forms
from .models import CajaDiaria, MovimientoCaja, MedioPago
from django.utils import timezone
from turnos.models import Turnos

class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = [
            'turno',
            'saldo_inicial',
            'observacion_apertura',
        ]

        widgets = {
            'turno': forms.Select(attrs={
                'class': 'form-select'
            }),
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ingrese saldo inicial'
            }),
            'observacion_apertura': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones de apertura'
            }),
        }

class MovimientoCajaForm(forms.ModelForm):
    class Meta:
        model = MovimientoCaja
        fields = [
            'tipo',
            'medio_pago',
            'importe',
            'concepto',
            'observacion',
        ]

        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'medio_pago': forms.Select(attrs={
                'class': 'form-select'
            }),
            'importe': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ingrese importe'
            }),
            'concepto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Consulta médica'
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observación opcional'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['medio_pago'].queryset = MedioPago.objects.filter(
            activo=True
        ).order_by('nombre')



class CobroConsultaForm(forms.ModelForm):
    turno = forms.ModelChoiceField(
        queryset=Turnos.objects.none(),
        required=True,
        label='Turno a cobrar',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    class Meta:
        model = MovimientoCaja
        fields = [
            'turno',
            'medio_pago',
            'importe',
            'concepto',
            'observacion',
        ]

        widgets = {
            'medio_pago': forms.Select(attrs={
                'class': 'form-select'
            }),
            'importe': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Importe de la consulta'
            }),
            'concepto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Consulta médica'
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observación opcional'
            }),
        }

    def __init__(self, *args, **kwargs):
        centro_medico = kwargs.pop('centro_medico', None)
        super().__init__(*args, **kwargs)

        self.fields['medio_pago'].queryset = MedioPago.objects.filter(
            activo=True
        ).order_by('nombre')

        if centro_medico:
            self.fields['turno'].queryset = Turnos.objects.filter(
                centro_medico=centro_medico,
                fecha=timezone.localdate(),
                estado__in=['PENDIENTE', 'ATENDIDO']
            ).select_related(
                'paciente',
                'medico',
                'especialidad'
            ).order_by('hora')

        self.fields['concepto'].initial = 'Consulta médica'
class AnularMovimientoCajaForm(forms.Form):
    motivo_anulacion = forms.CharField(
        label='Motivo de anulación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique el motivo de la anulación'
        }),
        required=True
    )


class CerrarCajaForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = [
            'observacion_cierre',
        ]

        widgets = {
            'observacion_cierre': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones del cierre de caja'
            }),
        }