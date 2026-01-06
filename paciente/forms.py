


from django import forms

from paciente.models import Paciente




class PacienteForm(forms.ModelForm):
    
    class Meta:
        model =Paciente
        fields = '__all__'
       
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'edad': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control'}),
            'telefono': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control'}),
            'obrasocial': forms.Select(attrs={'class': 'form-control'})
        }
    


class BusquedaPacienteForm(forms.Form):
    dni = forms.IntegerField(label='Ingrese el DNI')