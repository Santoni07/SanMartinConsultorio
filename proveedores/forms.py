from django import forms


class PagoLiquidacionProveedorForm(forms.Form):

    importe = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control"
            }
        )
    )

    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
            }
        )
    )


