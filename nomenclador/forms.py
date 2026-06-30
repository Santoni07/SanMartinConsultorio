from django import forms
from .models import NomencladorGeneral


class NomencladorGeneralForm(forms.ModelForm):

    class Meta:
        model = NomencladorGeneral
        fields = [
            'codigo',
            'descripcion',
            'activo',
            'observaciones',
        ]

        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }