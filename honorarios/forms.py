from django import forms
from caja.models import MedioPago


class PagoLiquidacionForm(forms.Form):

    medio_pago = forms.ModelChoiceField(
        queryset=MedioPago.objects.filter(
            activo=True
        ),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

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