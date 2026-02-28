from django import forms
from .models import Medico
from especialidades.models import Especialidades  # Ajustá el import si es necesario


class MedicosForm(forms.ModelForm):

    especialidad = forms.ModelMultipleChoiceField(
        queryset=Especialidades.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Medico
        fields = [
            'nombre',
            'apellido',
            'matricula',
            'email',
            'telefono',
            'img',
            'especialidad'
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'matricula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Matrícula'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'img': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }