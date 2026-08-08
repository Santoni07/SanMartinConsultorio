from django import forms
from paciente.models import Paciente


class PacienteForm(forms.ModelForm):

    class Meta:
        model = Paciente

        fields = [
            'dni',
            'nombre',
            'apellido',
            'fecha_nacimiento',
            'telefono',
            'sexo',
            'email',
            'direccion',
            'observaciones',
            'obrasocial'
        ]

        widgets = {

            'dni': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'apellido': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'sexo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'telefono': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),

            'direccion': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            'obrasocial': forms.Select(attrs={
                'class': 'form-select'
            })

        }

    def clean_dni(self):

        dni = self.cleaned_data["dni"]

        if (
            Paciente.objects
            .filter(dni=dni)
            .exclude(pk=self.instance.pk)
            .exists()
        ):

            raise forms.ValidationError(
                "Ya existe un paciente registrado con ese DNI."
            )

        return dni


class BusquedaPacienteForm(forms.Form):

    dni = forms.IntegerField(
        label='Ingrese el DNI'
    )


class PacienteUpdateForm(forms.ModelForm):

    class Meta:
        model = Paciente

        fields = [
            'dni',
            'nombre',
            'apellido',
            'telefono',
            'sexo',
            'email',
            'direccion',
            'observaciones',
            'obrasocial'
        ]

        widgets = {

            'dni': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'apellido': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'sexo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'telefono': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),

            'direccion': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            'obrasocial': forms.Select(attrs={
                'class': 'form-select'
            })

        }

    def clean_dni(self):

        dni = self.cleaned_data["dni"]

        if (
            Paciente.objects
            .filter(dni=dni)
            .exclude(pk=self.instance.pk)
            .exists()
        ):

            raise forms.ValidationError(
                "Ya existe un paciente registrado con ese DNI."
            )

        return dni