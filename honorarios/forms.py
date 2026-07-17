from django import forms
from caja.models import MedioPago
from medicos.models import Medico
from core.models import CentroMedico

class PagoLiquidacionForm(forms.Form):

    importe = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )

    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
    )
class FiltroHistorialLiquidacionesForm(forms.Form):

    desde = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        )
    )

    hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        )
    )

    medico = forms.ModelChoiceField(
        queryset=Medico.objects.order_by(
            "apellido",
            "nombre"
        ),
        required=False,
        empty_label="Todos los médicos",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        )
    )

    centro_medico = forms.ModelChoiceField(
        queryset=CentroMedico.objects.filter(
            activo=True
        ),
        required=False,
        empty_label="Todas las sedes",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        )
    )

    estado = forms.ChoiceField(

        required=False,

        choices=[

            ("", "Todos los estados"),

            ("PENDIENTE", "Pendiente"),

            ("PARCIAL", "Parcial"),

            ("PAGADA", "Pagada"),

        ],

        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        )

    )